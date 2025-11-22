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
    APPLICATION_MANAGER = "APPLICATION_MANAGER"
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


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(Enum(UserRole), unique=True, nullable=False)
    display_name = Column(String, nullable=False)

    users = relationship("User", back_populates="role")


class Affiliation(Base):
    __tablename__ = "affiliations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    users = relationship("User", back_populates="affiliation")


class User(Base):
    __tablename__ = "users"

    access_metadata = {
        "id": {"read_level": 3, "write_level": 3},
        "account_name": {"read_level": 3, "write_level": 3},
        "first_name": {"read_level": 3, "write_level": 3},
        "middle_name": {"read_level": 3, "write_level": 3},
        "last_name": {"read_level": 3, "write_level": 3},
        "name": {"read_level": 3, "write_level": 3},
        "email": {"read_level": 3, "write_level": 3},
        "affiliation_id": {"read_level": 3, "write_level": 3},
        "role_id": {"read_level": 3, "write_level": 3},
        "password_hash": {"read_level": 1, "write_level": 1},
    }

    id = Column(Integer, primary_key=True, index=True)
    account_name = Column(String, unique=True, nullable=False, index=True)
    first_name = Column(String, nullable=False)
    middle_name = Column(String, nullable=True)
    last_name = Column(String, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    affiliation_id = Column(Integer, ForeignKey("affiliations.id"), nullable=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    password_hash = Column(String, nullable=False)

    affiliation = relationship("Affiliation", back_populates="users")
    role = relationship("Role", back_populates="users")
    projects = relationship("ResearchProject", back_populates="pi", foreign_keys="ResearchProject.pi_id")
    managed_projects = relationship(
        "ResearchProject", back_populates="manager", foreign_keys="ResearchProject.manager_id"
    )
    approvals = relationship("Approval", back_populates="approver")


class ResearchProject(Base):
    __tablename__ = "research_projects"

    access_metadata = {
        "id": {"read_level": 2, "write_level": 3},
        "title": {"read_level": 2, "write_level": 3},
        "description": {"read_level": 2, "write_level": 3},
        "pi_id": {"read_level": 2, "write_level": 3},
        "manager_id": {"read_level": 2, "write_level": 3},
    }

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

    access_metadata = {
        "id": {"read_level": 2, "write_level": 3},
        "project_id": {"read_level": 2, "write_level": 3},
        "requested_date": {"read_level": 2, "write_level": 3},
        "duration_hours": {"read_level": 2, "write_level": 3},
        "justification": {"read_level": 2, "write_level": 3},
        "status": {"read_level": 2, "write_level": 3},
        "created_at": {"read_level": 2, "write_level": 3},
    }

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

    access_metadata = {
        "id": {"read_level": 3, "write_level": 4},
        "request_id": {"read_level": 3, "write_level": 4},
        "beamline": {"read_level": 3, "write_level": 4},
        "slot_date": {"read_level": 3, "write_level": 4},
        "slot_time": {"read_level": 3, "write_level": 4},
        "duration_hours": {"read_level": 3, "write_level": 4},
        "status": {"read_level": 3, "write_level": 4},
        "created_at": {"read_level": 3, "write_level": 4},
    }

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

    access_metadata = {
        "id": {"read_level": 4, "write_level": 5},
        "allocation_id": {"read_level": 4, "write_level": 5},
        "approver_id": {"read_level": 4, "write_level": 5},
        "approved": {"read_level": 4, "write_level": 5},
        "notes": {"read_level": 4, "write_level": 5},
        "created_at": {"read_level": 4, "write_level": 5},
    }

    id = Column(Integer, primary_key=True, index=True)
    allocation_id = Column(Integer, ForeignKey("allocations.id"), nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    allocation = relationship("Allocation", back_populates="approvals")
    approver = relationship("User", back_populates="approvals")
