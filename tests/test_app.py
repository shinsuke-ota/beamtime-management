from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def create_user(payload):
    response = client.post("/users/", json=payload)
    assert response.status_code == 200
    return response.json()["id"]


def test_full_workflow():
    pi_id = create_user({
        "name": "Dr. PI",
        "email": "pi@example.com",
        "affiliation": "Lab",
        "role": "PI",
    })
    manager_id = create_user({
        "name": "Manager",
        "email": "manager@example.com",
        "affiliation": "Lab",
        "role": "PROJECT_MANAGER",
    })
    allocator_id = create_user({
        "name": "Allocator",
        "email": "allocator@example.com",
        "affiliation": "Lab",
        "role": "ALLOCATOR",
    })
    approver_id = create_user({
        "name": "Approver",
        "email": "approver@example.com",
        "affiliation": "Lab",
        "role": "APPROVER",
    })

    project_payload = {
        "title": "Project A",
        "description": "Study",
        "pi_id": pi_id,
        "manager_id": manager_id,
    }
    project_resp = client.post("/projects/", json=project_payload)
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
    )
    assert request_resp.status_code == 200
    request_id = request_resp.json()["id"]

    status_resp = client.patch(
        f"/requests/{request_id}/status",
        params={"manager_id": manager_id},
        json={"status": "APPROVED"},
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
    )
    assert allocation_resp.status_code == 200
    allocation_id = allocation_resp.json()["id"]

    approval_resp = client.post(
        f"/allocations/{allocation_id}/approve",
        json={"approver_id": approver_id, "approved": True},
    )
    assert approval_resp.status_code == 200
    assert approval_resp.json()["approved"] is True

    projects_resp = client.get(f"/users/{pi_id}/projects")
    assert projects_resp.status_code == 200
    assert len(projects_resp.json()) == 1

    monthly_resp = client.get("/reports/monthly", params={"year": date.today().year})
    assert monthly_resp.status_code == 200
    assert len(monthly_resp.json()) >= 1

    table_resp = client.get("/allocations/table")
    assert table_resp.status_code == 200
    assert table_resp.json()[0]["project_title"] == "Project A"
