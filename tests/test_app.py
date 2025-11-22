from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database import Base
from app.dependencies import get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

Base.metadata.drop_all(bind=test_engine)
Base.metadata.create_all(bind=test_engine)


def reset_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def register_initial_application_manager():
    response = client.post(
        "/auth/application-manager-setup",
        json={
            "name": "Initial Application Manager",
            "email": "manager@beamtime.org",
            "affiliation": "Lab",
            "password": "initpass",
        },
    )
    assert response.status_code == 201
    data = response.json()
    return data["user"]["id"], data["token"]["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def create_department(token: str) -> int:
    institution_resp = client.post(
        "/institutions/", json={"name": "Test Institution"}, headers=auth_headers(token)
    )
    assert institution_resp.status_code == 201
    institution_id = institution_resp.json()["id"]

    department_resp = client.post(
        "/departments/",
        json={"name": "Test Department", "institution_id": institution_id},
        headers=auth_headers(token),
    )
    assert department_resp.status_code == 201
    return department_resp.json()["id"]


def create_user(payload, token, department_id):
    full_payload = payload | {
        "password": payload.get("password", "testpass"),
        "department_id": department_id,
    }
    response = client.post("/users/", json=full_payload, headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()["id"]


def test_full_workflow():
    reset_database()
    approver_id, approver_token = register_initial_approver()
    department_id = create_department(approver_token)
    pi_id = create_user({
        "name": "Dr. PI",
        "email": "pi@example.com",
        "affiliation": "Lab",
        "role": "PI",
    }, approver_token, department_id)
    manager_id = create_user({
        "name": "Manager",
        "email": "manager@example.com",
        "affiliation": "Lab",
        "role": "PROJECT_MANAGER",
    }, approver_token, department_id)
    allocator_id = create_user({
        "name": "Allocator",
        "email": "allocator@example.com",
        "affiliation": "Lab",
        "role": "ALLOCATOR",
    }, approver_token, department_id)

    project_payload = {
        "title": "Project A",
        "description": "Study",
        "pi_id": pi_id,
        "manager_id": manager_id,
    }
    project_resp = client.post("/projects/", json=project_payload, headers=auth_headers(approver_token))
    assert project_resp.status_code == 200
    project_id = project_resp.json()["id"]

    request_payload = {
        "requested_date": date.today().isoformat(),
        "duration_hours": 8,
        "justification": "Need beamtime",
    }
    request_resp = client.post(
        f"/projects/{project_id}/requests",
        params={"pi_id": pi_id},
        json=request_payload,
        headers=auth_headers(approver_token),
    )
    assert request_resp.status_code == 200
    request_id = request_resp.json()["id"]

    status_resp = client.patch(
        f"/requests/{request_id}/status",
        params={"manager_id": manager_id},
        json={"status": "APPROVED"},
        headers=auth_headers(approver_token),
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "APPROVED"

    allocation_payload = {
        "beamline": "BL1",
        "slot_date": date.today().isoformat(),
        "slot_time": "08:00",
        "duration_hours": 8,
    }
    allocation_resp = client.post(
        f"/requests/{request_id}/allocations",
        params={"allocator_id": allocator_id},
        json=allocation_payload,
        headers=auth_headers(approver_token),
    )
    assert allocation_resp.status_code == 200
    allocation_id = allocation_resp.json()["id"]

    approval_resp = client.post(
        f"/allocations/{allocation_id}/approve",
        json={"approver_id": approver_id, "approved": True},
        headers=auth_headers(approver_token),
    )
    assert approval_resp.status_code == 200
    assert approval_resp.json()["approved"] is True

    projects_resp = client.get(f"/users/{pi_id}/projects", headers=auth_headers(approver_token))
    assert projects_resp.status_code == 200
    assert len(projects_resp.json()) == 1

    monthly_resp = client.get(
        "/reports/monthly", params={"year": date.today().year}, headers=auth_headers(approver_token)
    )
    assert monthly_resp.status_code == 200
    assert len(monthly_resp.json()) >= 1

    table_resp = client.get("/allocations/table", headers=auth_headers(approver_token))
    assert table_resp.status_code == 200
    assert table_resp.json()[0]["project_title"] == "Project A"


def test_list_users_returns_ordered_users():
    reset_database()
    initial_id, approver_token = register_initial_approver()
    department_id = create_department(approver_token)
    users = [
        {
            "name": "Charlie",
            "email": "charlie@example.com",
            "affiliation": "Lab",
            "role": "PI",
            "password": "testpass",
        },
        {
            "name": "Alice",
            "email": "alice@example.com",
            "affiliation": "Lab",
            "role": "APPROVER",
            "password": "testpass",
        },
        {
            "name": "Bob",
            "email": "bob@example.com",
            "affiliation": "Lab",
            "role": "ALLOCATOR",
            "password": "testpass",
        },
    ]
    created_ids = [create_user(payload, approver_token, department_id) for payload in users]

    response = client.get("/users/", headers=auth_headers(approver_token))
    assert response.status_code == 200
    result = response.json()
    assert [user["name"] for user in result] == [
        "Alice",
        "Bob",
        "Charlie",
        "Initial Application Manager",
    ]
    assert sorted(created_ids + [initial_id]) == sorted([user["id"] for user in result])


def test_get_user_by_id():
    reset_database()
    _, approver_token = register_initial_approver()
    department_id = create_department(approver_token)
    user_id = create_user(
        {
            "name": "Eve",
            "email": "eve@example.com",
            "affiliation": "Lab",
            "role": "PROJECT_MANAGER",
            "password": "testpass",
        },
        approver_token,
        department_id,
    )

    response = client.get(f"/users/{user_id}", headers=auth_headers(approver_token))
    assert response.status_code == 200
    assert response.json() == {
        "id": user_id,
        "name": "Eve",
        "email": "eve@example.com",
        "affiliation": "Lab",
        "department_id": department_id,
        "role": "PROJECT_MANAGER",
    }
