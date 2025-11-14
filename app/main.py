from collections import defaultdict
from datetime import datetime
from typing import List

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine
from .dependencies import ensure_role, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Beamtime Management API")


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.put("/users/{user_id}", response_model=schemas.User)
def update_user(user_id: int, payload: schemas.UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(db_user, field, value)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/users/{user_id}/projects", response_model=List[schemas.Project])
def list_projects_for_pi(user_id: int, db: Session = Depends(get_db)):
    ensure_role(db, user_id, models.UserRole.PI)
    return db.query(models.ResearchProject).filter(models.ResearchProject.pi_id == user_id).all()


@app.post("/projects/", response_model=schemas.Project)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    ensure_role(db, project.manager_id, models.UserRole.PROJECT_MANAGER)
    ensure_role(db, project.pi_id, models.UserRole.PI)
    db_project = models.ResearchProject(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@app.put("/projects/{project_id}", response_model=schemas.Project)
def update_project(project_id: int, payload: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    db_project = db.query(models.ResearchProject).filter(models.ResearchProject.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    update_data = payload.dict(exclude_unset=True)
    if "manager_id" in update_data:
        ensure_role(db, update_data["manager_id"], models.UserRole.PROJECT_MANAGER)
    if "pi_id" in update_data:
        ensure_role(db, update_data["pi_id"], models.UserRole.PI)
    for field, value in update_data.items():
        setattr(db_project, field, value)
    db.commit()
    db.refresh(db_project)
    return db_project


@app.delete("/projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    db_project = db.query(models.ResearchProject).filter(models.ResearchProject.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    db.delete(db_project)
    db.commit()
    return {"detail": "Project deleted"}


@app.post("/projects/{project_id}/requests", response_model=schemas.BeamtimeRequest)
def create_request(project_id: int, payload: schemas.BeamtimeRequestCreate, pi_id: int, db: Session = Depends(get_db)):
    project = db.query(models.ResearchProject).filter(models.ResearchProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    ensure_role(db, pi_id, models.UserRole.PI)
    if project.pi_id != pi_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="PI does not own project")
    db_request = models.BeamtimeRequest(project_id=project_id, **payload.dict())
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request


@app.get("/projects/{project_id}/requests", response_model=List[schemas.BeamtimeRequest])
def list_requests(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.ResearchProject).filter(models.ResearchProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return db.query(models.BeamtimeRequest).filter(models.BeamtimeRequest.project_id == project_id).all()


@app.get("/managers/{manager_id}/requests", response_model=List[schemas.BeamtimeRequest])
def manager_requests(manager_id: int, db: Session = Depends(get_db)):
    ensure_role(db, manager_id, models.UserRole.PROJECT_MANAGER)
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
):
    ensure_role(db, manager_id, models.UserRole.PROJECT_MANAGER)
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
):
    ensure_role(db, allocator_id, models.UserRole.ALLOCATOR)
    request = db.query(models.BeamtimeRequest).filter(models.BeamtimeRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    db_allocation = models.Allocation(request_id=request_id, **payload.dict())
    db.add(db_allocation)
    db.commit()
    db.refresh(db_allocation)
    return db_allocation


@app.get("/allocations/", response_model=List[schemas.Allocation])
def list_allocations(db: Session = Depends(get_db)):
    return db.query(models.Allocation).all()


@app.get("/allocations/table", response_model=List[schemas.AllocationTableRow])
def allocation_table(db: Session = Depends(get_db)):
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
):
    ensure_role(db, payload.approver_id, models.UserRole.APPROVER)
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
def monthly_report(year: int, db: Session = Depends(get_db)):
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
