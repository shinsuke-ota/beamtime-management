# Beamtime Management

## Project purpose
Beamtime Management streamlines how research facilities schedule and approve
beamline access. It centralizes project intake, principal investigator (PI)
requests, allocator scheduling, and final approvals so laboratory staff and
external collaborators can see the exact state of every beamtime slot.

The platform is split into a FastAPI backend that exposes secure REST
endpoints and a Vue/Vuetify frontend that visualizes calendars, request lists,
and status dashboards.

## Architecture overview
- **Backend** – FastAPI application (`app/`) with SQLAlchemy models,
  Pydantic schemas, and Alembic migrations. It currently ships with an SQLite
  database (`app/database.py`) but can be pointed at PostgreSQL/MySQL by
  updating `SQLALCHEMY_DATABASE_URL`.
- **Frontend** – Vite-powered Vue 3 SPA (`frontend/`) styled with Vuetify and
  communicating with the API through `frontend/src/services/api.js`. The
  base URL is configured via `VITE_API_URL`.
- **Data & migrations** – SQLAlchemy ORM models live in `app/models.py` and
  are versioned through Alembic (see `alembic/`).

## Role-based feature summary
| Role | Key features |
| --- | --- |
| Principal Investigator (PI) | Create/update projects, submit beamtime requests, view allocation outcomes. |
| Project Manager | Own a portfolio of projects, review PI requests, approve/decline or request changes, track status dashboards. |
| Allocator | Schedule approved requests onto beamlines, manage calendar slots, prepare tables for reporting. |
| Approver | Perform final compliance/operations approval on allocations, lock schedules when confirmed. |

## Prerequisites
- Python 3.11+
- Node.js 20+ and npm 10+
- SQLite (bundled) or another SQL database reachable from the backend
- Recommended: `pipx`, `pyenv`, and `direnv` to manage tools/env vars

## Backend environment setup (FastAPI)
```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Create a `.env` (optional) for secrets such as alternative database URLs. The
default `sqlite:///./beamtime.db` works locally with no extra setup.

## Frontend environment setup (Node + Vite)
```bash
cd frontend
npm install
```

Create `frontend/.env` to point the SPA at your API if it differs from
`http://localhost:8000`:

```
VITE_API_URL=http://localhost:8000
```

## Database migrations
Alembic manages schema changes.

```bash
# Create a migration after editing SQLAlchemy models
alembic revision --autogenerate -m "Describe change"

# Apply migrations to the current environment
db_url="sqlite:///./beamtime.db"  # or export DATABASE_URL
alembic upgrade head
```

During CI/CD or deployment, always run `alembic upgrade head` before starting
application processes.

## Development workflow
1. **Start the backend**
   ```bash
   source .venv/bin/activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
2. **Start the frontend**
   ```bash
   cd frontend
   npm run dev -- --host
   ```
3. Visit `http://localhost:5173` (default Vite port). The SPA proxies API
   calls to `VITE_API_URL`.
4. Use the FastAPI docs at `http://localhost:8000/docs` for quick API
   exploration.

## Testing
| Layer | Command |
| --- | --- |
| Backend unit/API tests | `pytest` |
| Frontend type/build check | `cd frontend && npm run build` |

Add future frontend unit tests under `frontend/src` and wire them through
`npm test` when available.

## Deployment
1. Build backend image or install dependencies on your server/container.
2. Configure environment variables:
   - `SQLALCHEMY_DATABASE_URL` (e.g. PostgreSQL)
   - `VITE_API_URL` (for the frontend build, usually `/api` behind the same domain)
3. Run Alembic migrations: `alembic upgrade head`.
4. Start FastAPI behind an ASGI server such as Uvicorn/Gunicorn:
   `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
5. Build the frontend: `cd frontend && npm run build`. Serve the generated
   `dist/` directory with a CDN, static file host, or mount it behind the
   backend (configure Nginx/Traefik to proxy API traffic to FastAPI).
6. Monitor logs and configure HTTPS + authentication before exposing to users.

## Screenshots
Add calendar/list UI screenshots once the components are implemented. Save
images under `docs/screenshots/` (e.g. `docs/screenshots/calendar.png`) and
reference them here:

```markdown
![Calendar view](docs/screenshots/calendar.png)
![Request list](docs/screenshots/request-list.png)
```

## Additional tips
- Keep backend/ frontend branches in sync; schema changes usually require
  updated UI flows.
- Use role-based seed data during development to exercise PI/manager workflows.
- Run `npm run build` and `pytest` before committing to ensure both stacks stay
  healthy.
