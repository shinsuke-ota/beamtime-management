from dataclasses import dataclass
from enum import IntEnum
from typing import Iterable

from fastapi import HTTPException, status

from .models import Role, User, UserRole


class AccessLevel(IntEnum):
    SELF = 1
    APPLICATION_MANAGER = 6
    PI = 2
    PROJECT_MANAGER = 3
    ALLOCATOR = 4
    APPROVER = 5


ROLE_ACCESS_LEVELS: dict[UserRole, AccessLevel] = {
    UserRole.APPLICATION_MANAGER: AccessLevel.APPLICATION_MANAGER,
    UserRole.PI: AccessLevel.PI,
    UserRole.PROJECT_MANAGER: AccessLevel.PROJECT_MANAGER,
    UserRole.ALLOCATOR: AccessLevel.ALLOCATOR,
    UserRole.APPROVER: AccessLevel.APPROVER,
}


@dataclass(frozen=True)
class FieldAccess:
    read: AccessLevel
    write: AccessLevel


# User fields default to level 3 (Project Manager) for read/write except password.
USER_FIELD_ACCESS: dict[str, FieldAccess] = {
    "id": FieldAccess(read=AccessLevel.PROJECT_MANAGER, write=AccessLevel.PROJECT_MANAGER),
    "account_name": FieldAccess(read=AccessLevel.PROJECT_MANAGER, write=AccessLevel.PROJECT_MANAGER),
    "first_name": FieldAccess(read=AccessLevel.PROJECT_MANAGER, write=AccessLevel.PROJECT_MANAGER),
    "middle_name": FieldAccess(read=AccessLevel.PROJECT_MANAGER, write=AccessLevel.PROJECT_MANAGER),
    "last_name": FieldAccess(read=AccessLevel.PROJECT_MANAGER, write=AccessLevel.PROJECT_MANAGER),
    "name": FieldAccess(read=AccessLevel.PROJECT_MANAGER, write=AccessLevel.PROJECT_MANAGER),
    "email": FieldAccess(read=AccessLevel.PROJECT_MANAGER, write=AccessLevel.PROJECT_MANAGER),
    "affiliation_id": FieldAccess(read=AccessLevel.PROJECT_MANAGER, write=AccessLevel.PROJECT_MANAGER),
    "role_id": FieldAccess(read=AccessLevel.PROJECT_MANAGER, write=AccessLevel.PROJECT_MANAGER),
    "password_hash": FieldAccess(read=AccessLevel.SELF, write=AccessLevel.SELF),
}

REDACTED_VALUE = "REDACTED"


def get_role_level(role: Role | None) -> AccessLevel:
    if not role:
        return AccessLevel.SELF
    return ROLE_ACCESS_LEVELS.get(role.slug, AccessLevel.SELF)


def get_user_level(actor: User, target: User | None = None) -> AccessLevel:
    level = get_role_level(actor.role)
    if target and actor.id == target.id:
        return max(level, AccessLevel.SELF)
    return level


def ensure_level(
    actor: User,
    required_level: AccessLevel,
    detail: str = "Insufficient privileges for this action",
):
    if get_role_level(actor.role) < required_level:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def ensure_user_field_access(
    actor: User, target: User, operation: str, fields: Iterable[str]
):
    level = get_user_level(actor, target)
    for field in fields:
        requirement = USER_FIELD_ACCESS.get(field)
        if not requirement:
            continue
        needed = requirement.read if operation == "read" else requirement.write
        if level < needed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient privileges to {operation} field '{field}'",
            )


def ensure_subject_meets_level(db_user: User, required_level: AccessLevel) -> None:
    if get_role_level(db_user.role) < required_level:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User must meet access level {required_level}",
        )


def redact_user_payload(target: User, actor: User) -> dict:
    level = get_user_level(actor, target)
    payload = {
        "id": target.id,
        "account_name": target.account_name,
        "first_name": target.first_name,
        "middle_name": target.middle_name,
        "last_name": target.last_name,
        "name": target.name,
        "email": target.email,
        "affiliation_id": target.affiliation_id,
        "role_id": target.role_id,
    }
    for field, requirement in USER_FIELD_ACCESS.items():
        if field not in payload:
            continue
        if level < requirement.read:
            payload[field] = REDACTED_VALUE if field not in {"role_id", "affiliation_id"} else None
    return payload
