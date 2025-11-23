import os
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from email_validator import EmailNotValidError, validate_email

from . import models, schemas
from .authorization import (
    AccessLevel,
    ensure_level,
    ensure_user_field_access,
    redact_user_payload,
)
from .database import Base, engine
from .dependencies import (
    create_access_token,
    ensure_access_level,
    get_current_user,
    get_db,
    get_password_hash,
    verify_password,
)

Base.metadata.create_all(bind=engine)


def get_role_by_id(db: Session, role_id: int) -> models.Role:
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role id")
    return role


def get_or_create_role(db: Session, slug: models.UserRole) -> models.Role:
    role = db.query(models.Role).filter(models.Role.slug == slug).first()
    if role:
        return role
    # Determine access level based on role
    from .authorization import ROLE_ACCESS_LEVELS
    access_level = ROLE_ACCESS_LEVELS.get(slug, 1)
    role = models.Role(
        slug=slug,
        display_name=slug.replace("_", " ").title(),
        access_level=access_level
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def build_full_name(first_name: str, last_name: str, middle_name: str | None = None) -> str:
    parts = [first_name]
    if middle_name:
        parts.append(middle_name)
    parts.append(last_name)
    return " ".join(parts)


def application_manager_exists(db: Session) -> bool:
    role = db.query(models.Role).filter(
        models.Role.slug == models.UserRole.APPLICATION_MANAGER
    ).first()
    if not role:
        return False
    return db.query(models.User).filter(
        models.User.role_id == role.id
    ).first() is not None

app = FastAPI(title="Beamtime Management API")

app.state.session_cookie = os.environ.get("SESSION_COOKIE_NAME", "session")
app.state.session_ttl_minutes = int(os.environ.get("SESSION_TTL_MINUTES", "60"))

# Allow overriding CORS origins via environment variable; default to common local Vite ports.
_default_origins = {
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
}
allowed_origins = os.environ.get("ALLOWED_ORIGINS")
if allowed_origins:
    origins = [origin.strip() for origin in allowed_origins.split(",") if origin.strip()]
else:
    origins = sorted(_default_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_institution_or_404(db: Session, institution_id: int) -> models.Institution:
    institution = db.query(models.Institution).filter(models.Institution.id == institution_id).first()
    if not institution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")
    return institution


def get_department_or_404(db: Session, department_id: int) -> models.Department:
    department = db.query(models.Department).filter(models.Department.id == department_id).first()
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return department


@app.post(
    "/institutions/",
    response_model=schemas.Institution,
    status_code=status.HTTP_201_CREATED,
)
def create_institution(
    payload: schemas.InstitutionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ensure_level(
        current_user, AccessLevel.ALLOCATOR, "Only allocators or higher can create institutions"
    )
    institution = models.Institution(name=payload.name)
    try:
        db.add(institution)
        db.commit()
        db.refresh(institution)
        return institution
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An institution with that name already exists",
        )


@app.get("/institutions/", response_model=List[schemas.Institution])
def list_institutions(db: Session = Depends(get_db)):
    return db.query(models.Institution).order_by(models.Institution.name.asc()).all()


@app.get("/institutions/{institution_id}", response_model=schemas.Institution)
def get_institution(institution_id: int, db: Session = Depends(get_db)):
    return get_institution_or_404(db, institution_id)


@app.put("/institutions/{institution_id}", response_model=schemas.Institution)
def update_institution(
    institution_id: int,
    payload: schemas.InstitutionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ensure_level(
        current_user, AccessLevel.ALLOCATOR, "Only allocators or higher can update institutions"
    )
    institution = get_institution_or_404(db, institution_id)
    institution.name = payload.name
    try:
        db.commit()
        db.refresh(institution)
        return institution
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An institution with that name already exists",
        )


@app.delete("/institutions/{institution_id}")
def delete_institution(
    institution_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ensure_level(
        current_user, AccessLevel.ALLOCATOR, "Only allocators or higher can delete institutions"
    )
    institution = get_institution_or_404(db, institution_id)
    db.delete(institution)
    db.commit()
    return {"detail": "Institution deleted"}


@app.post(
    "/departments/",
    response_model=schemas.Department,
    status_code=status.HTTP_201_CREATED,
)
def create_department(
    payload: schemas.DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ensure_level(current_user, AccessLevel.ALLOCATOR, "Only allocators or higher can create departments")
    get_institution_or_404(db, payload.institution_id)
    department = models.Department(**payload.dict())
    try:
        db.add(department)
        db.commit()
        db.refresh(department)
        return department
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A department with that name already exists for this institution",
        )


@app.get("/departments/", response_model=List[schemas.Department])
def list_departments(
    institution_id: Optional[int] = None, db: Session = Depends(get_db)
):
    query = db.query(models.Department)
    if institution_id is not None:
        query = query.filter(models.Department.institution_id == institution_id)
    return query.order_by(models.Department.name.asc()).all()


@app.get("/departments/{department_id}", response_model=schemas.Department)
def get_department(department_id: int, db: Session = Depends(get_db)):
    return get_department_or_404(db, department_id)


@app.get("/roles/", response_model=List[schemas.Role])
def list_roles(db: Session = Depends(get_db)):
    return db.query(models.Role).order_by(models.Role.access_level.asc()).all()


@app.put("/departments/{department_id}", response_model=schemas.Department)
def update_department(
    department_id: int,
    payload: schemas.DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ensure_level(current_user, AccessLevel.ALLOCATOR, "Only allocators or higher can update departments")
    department = get_department_or_404(db, department_id)
    update_data = payload.dict(exclude_unset=True)
    if "institution_id" in update_data:
        get_institution_or_404(db, update_data["institution_id"])
    for field, value in update_data.items():
        setattr(department, field, value)
    try:
        db.commit()
        db.refresh(department)
        return department
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A department with that name already exists for this institution",
        )


@app.delete("/departments/{department_id}")
def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ensure_level(current_user, AccessLevel.ALLOCATOR, "Only allocators or higher can delete departments")
    department = get_department_or_404(db, department_id)
    db.delete(department)
    db.commit()
    return {"detail": "Department deleted"}


@app.get(
    "/auth/setup-status",
    response_model=schemas.SetupStatusResponse,
)
def get_setup_status(db: Session = Depends(get_db)):
    requires_setup = not application_manager_exists(db)
    return schemas.SetupStatusResponse(
        requires_setup=requires_setup,
        message="Application Manager setup required"
        if requires_setup
        else "System is configured",
    )


@app.post(
    "/auth/application-manager-setup",
    response_model=schemas.ApplicationManagerSetupResponse,
    status_code=status.HTTP_201_CREATED,
)
def application_manager_setup(
    payload: schemas.ApplicationManagerSetupRequest, db: Session = Depends(get_db)
):
    if application_manager_exists(db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An Application Manager is already registered",
        )
    try:
        validate_email(payload.email)
    except EmailNotValidError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    try:
        app_manager_role = get_or_create_role(
            db, models.UserRole.APPLICATION_MANAGER
        )
        db_user = models.User(
            account_name=payload.account_name,
            first_name=payload.first_name,
            middle_name=payload.middle_name,
            last_name=payload.last_name,
            name=payload.name
            or build_full_name(payload.first_name, payload.last_name, payload.middle_name),
            email=payload.email,
            affiliation=payload.affiliation,
            role_id=app_manager_role.id,
            password_hash=get_password_hash(payload.password),
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except IntegrityError as e:
        db.rollback()
        print(f"IntegrityError: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with that email or account name already exists",
        )
    except Exception as e:
        db.rollback()
        print(f"Unexpected error during user creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}",
        )

    access_token = create_access_token(
        data={"sub": str(db_user.id), "role": db_user.role.value},
        expires_delta=timedelta(minutes=60),
    )
    return schemas.ApplicationManagerSetupResponse(
        user=redact_user_payload(db_user, db_user),
        token=schemas.Token(access_token=access_token),
    )


@app.post("/auth/signup", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if not application_manager_exists(db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Register an Application Manager before self-service signup",
        )
    role = get_role_by_id(db, user.role_id)
    user_count = db.query(models.User).count()
    if user_count > 0 and role.slug != models.UserRole.PI:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Self-service signup is allowed only for PIs",
        )
    try:
        validate_email(user.email)
    except EmailNotValidError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    get_department_or_404(db, user.department_id)
    try:
        db_user = models.User(
            account_name=user.account_name,
            first_name=user.first_name,
            middle_name=user.middle_name,
            last_name=user.last_name,
            name=user.name or build_full_name(user.first_name, user.last_name, user.middle_name),
            email=user.email,
            affiliation=user.affiliation,
            department_id=user.department_id,
            role_id=user.role_id,
            password_hash=get_password_hash(user.password),
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return redact_user_payload(db_user, db_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with that email already exists",
        )


@app.post("/auth/login", response_model=schemas.Token)
def login(payload: schemas.LoginRequest, response: Response, db: Session = Depends(get_db)):
    print(f"Login attempt: email={payload.email}, account_name={payload.account_name}")
    filters = []
    if payload.email:
        filters.append(models.User.email == payload.email)
    if payload.account_name:
        filters.append(models.User.name == payload.account_name)
    db_user = db.query(models.User).filter(or_(*filters)).first() if filters else None
    print(f"User found: {db_user is not None}")
    if db_user:
        print(f"User: id={db_user.id}, email={db_user.email}, has_role={db_user.role is not None}")
    if not db_user or not verify_password(payload.password, db_user.password_hash):
        print("Authentication failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect account name/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": str(db_user.id), "role": db_user.role.slug},
        expires_delta=timedelta(minutes=60),
    )
    session_ttl = timedelta(minutes=app.state.session_ttl_minutes)
    session_token = create_access_token(
        data={
            "sub": str(db_user.id),
            "user": {
                "id": db_user.id,
                "name": db_user.name,
                "email": db_user.email,
                "role": db_user.role.slug,
            }
        },
        expires_delta=session_ttl,
    )
    response.set_cookie(
        key=app.state.session_cookie,
        value=session_token,
        httponly=True,
        samesite="lax",
        max_age=int(session_ttl.total_seconds()),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/auth/me", response_model=schemas.PublicUser)
def get_current_user_info(
    current_user: models.User = Depends(get_current_user),
):
    return redact_user_payload(current_user, current_user)


@app.post("/users/", response_model=schemas.PublicUser)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ensure_level(
        current_user,
        AccessLevel.APPLICATION_MANAGER,
        "Only Application Managers can create new users",
    )
    try:
        validate_email(user.email)
    except EmailNotValidError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    get_department_or_404(db, user.department_id)
    # Validate role_id exists
    get_role_by_id(db, user.role_id)
    db_user = models.User(
        account_name=user.account_name,
        first_name=user.first_name,
        middle_name=user.middle_name,
        last_name=user.last_name,
        name=user.name or build_full_name(user.first_name, user.last_name, user.middle_name),
        email=user.email,
        affiliation=user.affiliation,
        department_id=user.department_id,
        role_id=user.role_id,
        password_hash=get_password_hash(user.password),
    )
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return redact_user_payload(db_user, current_user)
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        print(f"IntegrityError occurred: {error_msg}")
        print(f"Full exception: {e}")
        if 'email' in error_msg.lower():
            detail = "A user with that email already exists"
        elif 'account_name' in error_msg.lower():
            detail = "A user with that account name already exists"
        else:
            detail = "A user with that information already exists"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )
    except Exception as e:
        db.rollback()
        print(f"Unexpected error during user creation: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create user: {str(e)}",
        )


@app.get("/users/", response_model=List[schemas.PublicUser])
def list_users(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    users = db.query(models.User).order_by(models.User.name.asc()).all()
    return [redact_user_payload(user, current_user) for user in users]


@app.get("/users/{user_id}", response_model=schemas.PublicUser)
def get_user(
    user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return redact_user_payload(db_user, current_user)


@app.put("/users/{user_id}", response_model=schemas.PublicUser)
def update_user(
    user_id: int,
    payload: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    update_data = payload.dict(exclude_unset=True)
    if "email" in update_data:
        try:
            validate_email(update_data["email"])
        except EmailNotValidError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if "department_id" in update_data and update_data["department_id"] is not None:
        get_department_or_404(db, update_data["department_id"])
    password = update_data.pop("password", None)
    if password:
        update_data["password_hash"] = get_password_hash(password)
    if any(field in update_data for field in ["first_name", "last_name", "middle_name"]):
        update_data.setdefault("name", build_full_name(
            update_data.get("first_name", db_user.first_name),
            update_data.get("last_name", db_user.last_name),
            update_data.get("middle_name", db_user.middle_name),
        ))
    # Validate role_id if provided
    if "role_id" in update_data and update_data["role_id"] is not None:
        get_role_by_id(db, update_data["role_id"])
    ensure_user_field_access(current_user, db_user, "write", update_data.keys())
    try:
        for field, value in update_data.items():
            setattr(db_user, field, value)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address already exists",
        )
    db.refresh(db_user)
    return redact_user_payload(db_user, current_user)


@app.get("/users/{user_id}/projects", response_model=List[schemas.Project])
def list_projects_for_pi(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ensure_access_level(db, user_id, AccessLevel.PI)
    return db.query(models.ResearchProject).filter(models.ResearchProject.pi_id == user_id).all()


@app.post("/projects/", response_model=schemas.Project)
def create_project(
    project: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ensure_level(current_user, AccessLevel.PROJECT_MANAGER, "Only managers or higher can create projects")
    ensure_access_level(db, project.manager_id, AccessLevel.PROJECT_MANAGER)
    ensure_access_level(db, project.pi_id, AccessLevel.PI)
    db_project = models.ResearchProject(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@app.put("/projects/{project_id}", response_model=schemas.Project)
def update_project(
    project_id: int,
    payload: schemas.ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ensure_level(current_user, AccessLevel.PROJECT_MANAGER, "Only managers or higher can update projects")
    db_project = db.query(models.ResearchProject).filter(models.ResearchProject.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    update_data = payload.dict(exclude_unset=True)
    if "manager_id" in update_data:
        ensure_access_level(db, update_data["manager_id"], AccessLevel.PROJECT_MANAGER)
    if "pi_id" in update_data:
        ensure_access_level(db, update_data["pi_id"], AccessLevel.PI)
    for field, value in update_data.items():
        setattr(db_project, field, value)
    db.commit()
    db.refresh(db_project)
    return db_project


@app.delete("/projects/{project_id}")
def delete_project(
    project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    ensure_level(current_user, AccessLevel.PROJECT_MANAGER, "Only managers or higher can delete projects")
    db_project = db.query(models.ResearchProject).filter(models.ResearchProject.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    db.delete(db_project)
    db.commit()
    return {"detail": "Project deleted"}


@app.post("/projects/{project_id}/requests", response_model=schemas.BeamtimeRequest)
def create_request(
    project_id: int,
    payload: schemas.BeamtimeRequestCreate,
    pi_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ensure_level(current_user, AccessLevel.PI, "Only PIs or higher can create requests")
    project = db.query(models.ResearchProject).filter(models.ResearchProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    ensure_access_level(db, pi_id, AccessLevel.PI)
    if project.pi_id != pi_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="PI does not own project")
    db_request = models.BeamtimeRequest(project_id=project_id, **payload.dict())
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request


@app.get("/projects/{project_id}/requests", response_model=List[schemas.BeamtimeRequest])
def list_requests(
    project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    ensure_level(current_user, AccessLevel.PI, "Only PIs or higher can list requests")
    project = db.query(models.ResearchProject).filter(models.ResearchProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return db.query(models.BeamtimeRequest).filter(models.BeamtimeRequest.project_id == project_id).all()


@app.get("/managers/{manager_id}/requests", response_model=List[schemas.BeamtimeRequest])
def manager_requests(
    manager_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    ensure_access_level(db, manager_id, AccessLevel.PROJECT_MANAGER)
    project_ids = [p.id for p in db.query(models.ResearchProject).filter(models.ResearchProject.manager_id == manager_id)]
    if not project_ids:
        return []
    return db.query(models.BeamtimeRequest).filter(models.BeamtimeRequest.project_id.in_(project_ids)).all()


@app.patch("/requests/{request_id}/status", response_model=schemas.BeamtimeRequest)
def update_request_status(
    request_id: int,
    payload: schemas.BeamtimeRequestUpdate,
    manager_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ensure_level(current_user, AccessLevel.PROJECT_MANAGER, "Only managers or higher can update requests")
    ensure_access_level(db, manager_id, AccessLevel.PROJECT_MANAGER)
    db_request = db.query(models.BeamtimeRequest).filter(models.BeamtimeRequest.id == request_id).first()
    if not db_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    project = db_request.project
    if project.manager_id != manager_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager not assigned to project")
    db_request.status = payload.status
    db.commit()
    db.refresh(db_request)
    return db_request


@app.post("/requests/{request_id}/allocations", response_model=schemas.Allocation)
def create_allocation(
    request_id: int,
    payload: schemas.AllocationCreate,
    allocator_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ensure_level(current_user, AccessLevel.ALLOCATOR, "Only allocators or higher can create allocations")
    ensure_access_level(db, allocator_id, AccessLevel.ALLOCATOR)
    request = db.query(models.BeamtimeRequest).filter(models.BeamtimeRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    db_allocation = models.Allocation(request_id=request_id, **payload.dict())
    db.add(db_allocation)
    db.commit()
    db.refresh(db_allocation)
    return db_allocation


@app.get("/allocations/", response_model=List[schemas.Allocation])
def list_allocations(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    ensure_level(current_user, AccessLevel.PI, "Only PIs or higher can list allocations")
    return db.query(models.Allocation).all()


@app.get("/allocations/table", response_model=List[schemas.AllocationTableRow])
def allocation_table(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    ensure_level(current_user, AccessLevel.PI, "Only PIs or higher can list allocations")
    allocations = (
        db.query(models.Allocation, models.ResearchProject)
        .join(models.BeamtimeRequest, models.BeamtimeRequest.id == models.Allocation.request_id)
        .join(models.ResearchProject, models.ResearchProject.id == models.BeamtimeRequest.project_id)
        .all()
    )
    table = [
        schemas.AllocationTableRow(
            project_title=project.title,
            beamline=allocation.beamline,
            slot_date=allocation.slot_date,
            slot_time=allocation.slot_time,
            duration_hours=allocation.duration_hours,
            status=allocation.status,
        )
        for allocation, project in allocations
    ]
    return table


@app.post("/allocations/{allocation_id}/approve", response_model=schemas.Approval)
def approve_allocation(
    allocation_id: int,
    payload: schemas.ApprovalCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ensure_level(current_user, AccessLevel.APPROVER, "Only approvers can approve allocations")
    ensure_access_level(db, payload.approver_id, AccessLevel.APPROVER)
    allocation = db.query(models.Allocation).filter(models.Allocation.id == allocation_id).first()
    if not allocation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allocation not found")
    approval = models.Approval(allocation_id=allocation_id, **payload.dict())
    db.add(approval)
    if payload.approved:
        allocation.status = models.AllocationStatus.CONFIRMED
    db.commit()
    db.refresh(approval)
    return approval


@app.get("/reports/monthly", response_model=List[schemas.MonthlyReportItem])
def monthly_report(
    year: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    ensure_level(current_user, AccessLevel.PROJECT_MANAGER, "Only managers or higher can view reports")
    report = defaultdict(lambda: {"requests": 0, "allocations": 0})
    start = datetime(year, 1, 1)
    end = datetime(year, 12, 31, 23, 59, 59)

    requests = (
        db.query(models.BeamtimeRequest)
        .filter(models.BeamtimeRequest.created_at.between(start, end))
        .all()
    )
    for req in requests:
        month = req.created_at.strftime("%Y-%m")
        report[month]["requests"] += 1

    allocations = (
        db.query(models.Allocation)
        .filter(models.Allocation.created_at.between(start, end))
        .all()
    )
    for allocation in allocations:
        month = allocation.created_at.strftime("%Y-%m")
        report[month]["allocations"] += 1

    return [
        schemas.MonthlyReportItem(
            month=month,
            request_count=data["requests"],
            allocation_count=data["allocations"],
        )
        for month, data in sorted(report.items())
    ]


# Experimental Courses endpoints
@app.get("/experimental-courses/", response_model=List[schemas.ExperimentalCourse])
def list_experimental_courses(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all experimental courses"""
    courses = db.query(models.ExperimentalCourse).all()
    return courses


# Approved Projects endpoints
@app.post("/approved-projects/", response_model=schemas.ApprovedProject, status_code=status.HTTP_201_CREATED)
def create_approved_project(
    payload: schemas.ApprovedProjectCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new approved project (ALLOCATOR+ only)"""
    ensure_level(current_user, AccessLevel.ALLOCATOR, "Only allocators or higher can create approved projects")
    
    # Check if project_number already exists
    existing = db.query(models.ApprovedProject).filter(
        models.ApprovedProject.project_number == payload.project_number
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project number {payload.project_number} already exists"
        )
    
    # Verify all PI users exist
    for user_id in payload.principal_investigator_ids:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with id {user_id} not found"
            )
    
    # Create the project
    project = models.ApprovedProject(
        project_number=payload.project_number,
        title=payload.title,
        summary=payload.summary
    )
    db.add(project)
    db.flush()
    
    # Add principal investigators
    for idx, user_id in enumerate(payload.principal_investigator_ids):
        pi = models.ProjectPI(
            project_id=project.id,
            user_id=user_id,
            is_primary=(idx == 0)  # First PI is primary
        )
        db.add(pi)
    
    # Add beam requests
    for beam_req in payload.beam_requests:
        beam = models.BeamRequest(
            project_id=project.id,
            **beam_req.dict()
        )
        db.add(beam)
    
    db.commit()
    db.refresh(project)
    return project


@app.get("/approved-projects/", response_model=List[schemas.ApprovedProject])
def list_approved_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all approved projects (PI+ can view)"""
    ensure_level(current_user, AccessLevel.PI, "Only PIs or higher can view approved projects")
    projects = db.query(models.ApprovedProject).offset(skip).limit(limit).all()
    return projects


@app.get("/approved-projects/{project_id}", response_model=schemas.ApprovedProject)
def get_approved_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get a specific approved project"""
    ensure_level(current_user, AccessLevel.PI, "Only PIs or higher can view approved projects")
    project = db.query(models.ApprovedProject).filter(models.ApprovedProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@app.put("/approved-projects/{project_id}", response_model=schemas.ApprovedProject)
def update_approved_project(
    project_id: int,
    payload: schemas.ApprovedProjectUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update an approved project (ALLOCATOR+ only)"""
    ensure_level(current_user, AccessLevel.ALLOCATOR, "Only allocators or higher can update approved projects")
    
    project = db.query(models.ApprovedProject).filter(models.ApprovedProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    # Update basic fields
    if payload.project_number is not None:
        # Check if new project_number already exists
        existing = db.query(models.ApprovedProject).filter(
            models.ApprovedProject.project_number == payload.project_number,
            models.ApprovedProject.id != project_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project number {payload.project_number} already exists"
            )
        project.project_number = payload.project_number
    
    if payload.title is not None:
        project.title = payload.title
    
    if payload.summary is not None:
        project.summary = payload.summary
    
    # Update principal investigators if provided
    if payload.principal_investigator_ids is not None:
        # Verify all PI users exist
        for user_id in payload.principal_investigator_ids:
            user = db.query(models.User).filter(models.User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User with id {user_id} not found"
                )
        
        # Remove existing PIs
        db.query(models.ProjectPI).filter(models.ProjectPI.project_id == project_id).delete()
        
        # Add new PIs
        for idx, user_id in enumerate(payload.principal_investigator_ids):
            pi = models.ProjectPI(
                project_id=project.id,
                user_id=user_id,
                is_primary=(idx == 0)
            )
            db.add(pi)
    
    # Update beam requests if provided
    if payload.beam_requests is not None:
        # Remove existing beam requests
        db.query(models.BeamRequest).filter(models.BeamRequest.project_id == project_id).delete()
        
        # Add new beam requests
        for beam_req in payload.beam_requests:
            beam = models.BeamRequest(
                project_id=project.id,
                **beam_req.dict()
            )
            db.add(beam)
    
    db.commit()
    db.refresh(project)
    return project


@app.delete("/approved-projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_approved_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete an approved project (ALLOCATOR+ only)"""
    ensure_level(current_user, AccessLevel.ALLOCATOR, "Only allocators or higher can delete approved projects")
    
    project = db.query(models.ApprovedProject).filter(models.ApprovedProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    db.delete(project)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
