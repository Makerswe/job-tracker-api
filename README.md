# Job Application Tracker API

![CI](https://github.com/Makerswe/job-tracker-api/actions/workflows/ci.yml/badge.svg)

A REST API for tracking job applications. Save the jobs you apply for, move them through each stage (applied → interviewing → offer), search and filter them, and see your response rate.

Built with **FastAPI**, **SQLAlchemy 2.0** and **JWT authentication**. It has 17 automated tests, Docker support and a GitHub Actions CI pipeline.

## Features

- **User accounts:** register and log in. Passwords are hashed with bcrypt, and requests are authenticated with JWT bearer tokens.
- **Full CRUD** for job applications: create, read, partial update (PATCH) and delete.
- **Filtering, search, sorting and pagination**, for example `GET /applications?status=interviewing&q=python&sort=company&limit=10`.
- **Stats endpoint:** counts per status, plus the share of submitted applications that got a reply.
- **Data isolation:** users only ever see their own applications. Other users' records return `404`, so the API doesn't reveal which ids exist.
- **Input validation** with Pydantic: emails, URLs, field lengths and allowed statuses.
- **Interactive docs** generated automatically at `/docs` (Swagger UI) and `/redoc`.

## Tech stack

| Area | Tools |
|---|---|
| Framework | FastAPI, Uvicorn |
| Database | SQLAlchemy 2.0, with SQLite for development and PostgreSQL for Docker |
| Auth | PyJWT, bcrypt, OAuth2 password flow |
| Testing | pytest, FastAPI TestClient, in-memory SQLite |
| Quality | Ruff (linting and formatting) |
| DevOps | Docker, Docker Compose, GitHub Actions |

## Getting started

### Option 1: run locally

```bash
git clone https://github.com/Makerswe/job-tracker-api.git
cd job-tracker-api
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env             # then set SECRET_KEY
uvicorn app.main:app --reload
```

Open **http://localhost:8000/docs**.

### Option 2: Docker (API + PostgreSQL)

```bash
docker compose up --build
```

Open **http://localhost:8000/docs**.

### Run the tests

```bash
pytest -v
ruff check .
```

## Using the API

1. `POST /auth/register` with your email, name and password.
2. In Swagger, click **Authorize** and log in with your email and password. Outside Swagger, call `POST /auth/login` to get a token.
3. Call any `/applications` endpoint.

Example with curl:

```bash
# Log in
TOKEN=$(curl -s -X POST localhost:8000/auth/login \
  -d "username=you@example.com&password=secret123" | jq -r .access_token)

# Add an application
curl -X POST localhost:8000/applications \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"company":"Capitec","position":"Junior Backend Developer","status":"applied","applied_on":"2026-10-01"}'

# See your stats
curl localhost:8000/applications/stats -H "Authorization: Bearer $TOKEN"
```

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/auth/register` | Create an account |
| `POST` | `/auth/login` | Get a JWT access token |
| `GET` | `/auth/me` | Current user |
| `POST` | `/applications` | Add an application |
| `GET` | `/applications` | List, with `status`, `q`, `sort`, `order`, `limit` and `offset` |
| `GET` | `/applications/stats` | Counts per status and response rate |
| `GET` | `/applications/{id}` | Get one application |
| `PATCH` | `/applications/{id}` | Update some fields |
| `DELETE` | `/applications/{id}` | Delete |

Statuses: `wishlist`, `applied`, `interviewing`, `offer`, `rejected` and `withdrawn`.

## Project structure

```
app/
  main.py            # App setup and router registration
  config.py          # Settings from environment variables
  database.py        # Engine, session, per-request DB dependency
  models.py          # SQLAlchemy tables (User, Application)
  schemas.py         # Pydantic request/response models
  security.py        # Password hashing and JWT helpers
  deps.py            # Shared dependencies (DB session, current user)
  routers/
    auth.py          # Register, login, me
    applications.py  # CRUD, filtering, stats
tests/               # pytest suite, using a fresh in-memory DB per test
```

## Design decisions

- **PATCH instead of PUT** for updates, so clients send only the fields that changed (`exclude_unset=True`).
- **404 instead of 403** for other users' records, so the API doesn't leak which ids exist.
- **Dependency injection** for the database session and current user. That keeps routes small and lets tests swap in a test database.
- **Response rate leaves out the wishlist**, because those jobs were never submitted.

## Possible next steps

- Alembic database migrations
- Refresh tokens
- Reminders for follow-ups and interview dates
- A React frontend

## Author

**Loyiso Arnold**, BSc Computer Science (UWC), Cape Town
