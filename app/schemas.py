from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr

from .models import AllocationStatus, RequestStatus, UserRole


class UserBase(BaseModel):
    name: str
    email: EmailStr
    affiliation: Optional[str] = None
    role: UserRole


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    affiliation: Optional[str] = None


class User(UserBase):
    id: int

    class Config:
        orm_mode = True


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
