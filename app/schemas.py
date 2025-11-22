from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from .authorization import AccessLevel
from .models import AllocationStatus, RequestStatus


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
    affiliation_id: Optional[int] = Field(
        None,
        json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER},
    )
    role_id: int = Field(
        ..., json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER}
    )


class UserCreate(UserBase):
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
    affiliation_id: Optional[int] = Field(
        None, json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER}
    )
    role_id: Optional[int] = Field(
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
    affiliation_id: Optional[int] = Field(
        None, json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER}
    )
    role_id: Optional[int] = Field(
        None, json_schema_extra={"read_level": AccessLevel.PROJECT_MANAGER, "write_level": AccessLevel.PROJECT_MANAGER}
    )

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
    affiliation_id: Optional[int] = None


class ApplicationManagerSetupResponse(BaseModel):
    user: User
    token: Token


class SetupStatusResponse(BaseModel):
    requires_setup: bool
    message: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


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
