import enum
from datetime import datetime, date

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


class UserRole(str, enum.Enum):
    PI = "PI"
    PROJECT_MANAGER = "PROJECT_MANAGER"
    ALLOCATOR = "ALLOCATOR"
    APPROVER = "APPROVER"


class RequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    REVIEWED = "REVIEWED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class AllocationStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    affiliation = Column(String, nullable=True)
    role = Column(Enum(UserRole), nullable=False)

    projects = relationship("ResearchProject", back_populates="pi", foreign_keys="ResearchProject.pi_id")
    managed_projects = relationship(
        "ResearchProject", back_populates="manager", foreign_keys="ResearchProject.manager_id"
    )
    approvals = relationship("Approval", back_populates="approver")


class ResearchProject(Base):
    __tablename__ = "research_projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    pi_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    pi = relationship("User", foreign_keys=[pi_id], back_populates="projects")
    manager = relationship("User", foreign_keys=[manager_id], back_populates="managed_projects")
    requests = relationship("BeamtimeRequest", back_populates="project")


class BeamtimeRequest(Base):
    __tablename__ = "beamtime_requests"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("research_projects.id"), nullable=False)
    requested_date = Column(Date, nullable=False)
    duration_hours = Column(Integer, nullable=False)
    justification = Column(Text, nullable=True)
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    project = relationship("ResearchProject", back_populates="requests")
    allocations = relationship("Allocation", back_populates="request")


class Allocation(Base):
    __tablename__ = "allocations"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("beamtime_requests.id"), nullable=False)
    beamline = Column(String, nullable=False)
    slot_date = Column(Date, nullable=False)
    slot_time = Column(String, nullable=False)
    duration_hours = Column(Integer, nullable=False)
    status = Column(Enum(AllocationStatus), default=AllocationStatus.SCHEDULED, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    request = relationship("BeamtimeRequest", back_populates="allocations")
    approvals = relationship("Approval", back_populates="allocation")


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    allocation_id = Column(Integer, ForeignKey("allocations.id"), nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    allocation = relationship("Allocation", back_populates="approvals")
    approver = relationship("User", back_populates="approvals")
