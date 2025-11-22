from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, root_validator

from .authorization import AccessLevel
from .models import AllocationStatus, RequestStatus, UserRole


class InstitutionBase(BaseModel):
    name: str


class InstitutionCreate(InstitutionBase):
    pass


class Institution(InstitutionBase):
    id: int

    class Config:
        orm_mode = True


class DepartmentBase(BaseModel):
    name: str
    institution_id: int


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    institution_id: Optional[int] = None


class Department(DepartmentBase):
    id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    account_name: str = Field(
        ...,
        pattern=r"^[a-z][a-z0-9_-]{2,31}$",
        json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER},
    )
    first_name: str = Field(
        ..., json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER}
    )
    middle_name: Optional[str] = Field(
        None,
        json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER},
    )
    last_name: str = Field(
        ..., json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER}
    )
    name: Optional[str] = Field(
        None,
        json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER},
    )
    email: EmailStr = Field(
        ..., json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER}
    )
    affiliation: Optional[str] = Field(
        None,
        json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER},
    )
    department_id: Optional[int] = Field(
        None,
        json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER},
    )
    role: UserRole = Field(
        ..., json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER}
    )


class UserCreate(UserBase):
    department_id: int
    password: str


class UserUpdate(BaseModel):
    account_name: Optional[str] = Field(
        None,
        pattern=r"^[a-z][a-z0-9_-]{2,31}$",
        json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER},
    )
    first_name: Optional[str] = Field(
        None, json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER}
    )
    middle_name: Optional[str] = Field(
        None, json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER}
    )
    last_name: Optional[str] = Field(
        None, json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER}
    )
    name: Optional[str] = Field(
        None, json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER}
    )
    email: Optional[EmailStr] = Field(
        None, json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER}
    )
    affiliation: Optional[str] = Field(
        None, json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER}
    )
    department_id: Optional[int] = Field(
        None,
        json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER},
    )
    role: Optional[UserRole] = Field(
        None, json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER}
    )
    password: Optional[str] = Field(
        None, json_schema_extra={"read_level": AccessLevel.SELF, "write_level": AccessLevel.SELF}
    )


class User(BaseModel):
    id: int = Field(
        ..., json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER}
    )
    account_name: str = Field(
        ..., json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER}
    )
    first_name: str = Field(
        ..., json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER}
    )
    middle_name: Optional[str] = Field(
        None, json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER}
    )
    last_name: str = Field(
        ..., json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER}
    )
    name: Optional[str] = Field(
        None, json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER}
    )
    email: Optional[EmailStr] = Field(
        None, json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER}
    )
    affiliation: Optional[str] = Field(
        None, json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER}
    )
    department_id: Optional[int] = Field(
        None,
        json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER},
    )
    role: Optional[UserRole] = Field(
        None, json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER}
    )

    class Config:
        orm_mode = True


class PublicUser(BaseModel):
    id: int
    name: str
    email: Optional[EmailStr] = None
    affiliation: Optional[str] = None
    department_id: Optional[int] = None
    role: Optional[UserRole] = None

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ApproverSetupRequest(BaseModel):
    account_name: str = Field(..., pattern=r"^[a-z][a-z0-9_-]{2,31}$")
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    name: Optional[str] = None
    email: EmailStr
    affiliation: Optional[str] = None


class ApplicationManagerSetupRequest(BaseModel):
    account_name: str = Field(..., pattern=r"^[a-z][a-z0-9_-]{2,31}$")
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    name: Optional[str] = None
    email: EmailStr
    affiliation: Optional[str] = None
    password: str


class ApplicationManagerSetupResponse(BaseModel):
    user: PublicUser
    token: Token


class SetupStatusResponse(BaseModel):
    requires_setup: bool
    message: str


class LoginRequest(BaseModel):
    account_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str

    @root_validator
    def ensure_identifier(cls, values):
        if not values.get("account_name") and not values.get("email"):
            raise ValueError("Either account name or email must be provided")
        return values


class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None
    pi_id: int
    manager_id: int


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    pi_id: Optional[int] = None
    manager_id: Optional[int] = None


class Project(ProjectBase):
    id: int

    class Config:
        orm_mode = True


class BeamtimeRequestBase(BaseModel):
    requested_date: date
    duration_hours: int
    justification: Optional[str] = None


class BeamtimeRequestCreate(BeamtimeRequestBase):
    pass


class BeamtimeRequestUpdate(BaseModel):
    status: RequestStatus


class BeamtimeRequest(BeamtimeRequestBase):
    id: int
    project_id: int
    status: RequestStatus
    created_at: datetime

    class Config:
        orm_mode = True


class AllocationBase(BaseModel):
    beamline: str
    slot_date: date
    slot_time: str
    duration_hours: int


class AllocationCreate(AllocationBase):
    pass


class Allocation(AllocationBase):
    id: int
    request_id: int
    status: AllocationStatus
    created_at: datetime

    class Config:
        orm_mode = True


class ApprovalBase(BaseModel):
    approver_id: int
    notes: Optional[str] = None


class ApprovalCreate(ApprovalBase):
    approved: bool = True


class Approval(ApprovalBase):
    id: int
    allocation_id: int
    approved: bool
    created_at: datetime

    class Config:
        orm_mode = True


class MonthlyReportItem(BaseModel):
    month: str
    request_count: int
    allocation_count: int


class AllocationTableRow(BaseModel):
    project_title: str
    beamline: str
    slot_date: date
    slot_time: str
    duration_hours: int
    status: AllocationStatus
