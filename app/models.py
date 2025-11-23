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
    UniqueConstraint,
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
    access_level = Column(Integer, nullable=False)

    users = relationship("User", back_populates="role")


class Affiliation(Base):
    __tablename__ = "affiliations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)


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
        "department_id": {"read_level": 3, "write_level": 3},
        "role": {"read_level": 3, "write_level": 3},
        "password_hash": {"read_level": 1, "write_level": 1},
    }

    id = Column(Integer, primary_key=True, index=True)
    account_name = Column(String, unique=True, nullable=False, index=True)
    first_name = Column(String, nullable=False)
    middle_name = Column(String, nullable=True)
    last_name = Column(String, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    password_hash = Column(String, nullable=False)

    department = relationship("Department", back_populates="users")
    role = relationship("Role", back_populates="users")
    projects = relationship("ResearchProject", back_populates="pi", foreign_keys="ResearchProject.pi_id")
    managed_projects = relationship(
        "ResearchProject", back_populates="manager", foreign_keys="ResearchProject.manager_id"
    )
    approvals = relationship("Approval", back_populates="approver")


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    departments = relationship("Department", back_populates="institution", cascade="all, delete")


class Department(Base):
    __tablename__ = "departments"
    __table_args__ = (
        UniqueConstraint("institution_id", "name", name="uq_department_institution_name"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False)

    institution = relationship("Institution", back_populates="departments")
    users = relationship("User", back_populates="department")


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


class ExperimentalCourse(Base):
    __tablename__ = "experimental_courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    beam_requests = relationship("BeamRequest", back_populates="course")


class ApprovedProject(Base):
    __tablename__ = "approved_projects"

    access_metadata = {
        "id": {"read_level": 2, "write_level": 4},
        "project_number": {"read_level": 2, "write_level": 4},
        "title": {"read_level": 2, "write_level": 4},
        "summary": {"read_level": 2, "write_level": 4},
        "created_at": {"read_level": 2, "write_level": 4},
        "updated_at": {"read_level": 2, "write_level": 4},
    }

    id = Column(Integer, primary_key=True, index=True)
    project_number = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    principal_investigators = relationship("ProjectPI", back_populates="project", cascade="all, delete-orphan")
    beam_requests = relationship("BeamRequest", back_populates="project", cascade="all, delete-orphan")


class ProjectPI(Base):
    __tablename__ = "project_pis"
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_pi"),
    )

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("approved_projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)

    project = relationship("ApprovedProject", back_populates="principal_investigators")
    user = relationship("User")


class BeamRequest(Base):
    __tablename__ = "beam_requests"

    access_metadata = {
        "id": {"read_level": 2, "write_level": 4},
        "project_id": {"read_level": 2, "write_level": 4},
        "beam_species": {"read_level": 2, "write_level": 4},
        "max_intensity": {"read_level": 2, "write_level": 4},
        "required_resolution": {"read_level": 2, "write_level": 4},
        "course_id": {"read_level": 2, "write_level": 4},
        "planned_irradiation_hours": {"read_level": 2, "write_level": 4},
        "completed_irradiation_hours": {"read_level": 2, "write_level": 4},
    }

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("approved_projects.id"), nullable=False)
    beam_species = Column(String, nullable=False)
    max_intensity = Column(String, nullable=True)
    required_resolution = Column(String, nullable=True)
    course_id = Column(Integer, ForeignKey("experimental_courses.id"), nullable=False)
    planned_irradiation_hours = Column(Integer, nullable=False, default=0)
    completed_irradiation_hours = Column(Integer, nullable=False, default=0)

    project = relationship("ApprovedProject", back_populates="beam_requests")
    course = relationship("ExperimentalCourse", back_populates="beam_requests")
