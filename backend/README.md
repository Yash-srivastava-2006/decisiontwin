# DecisionTwin AI Backend

Backend foundation for DecisionTwin AI built with FastAPI, SQLAlchemy 2.0, PostgreSQL, Alembic, and Pydantic Settings.

## Setup

1. Create a PostgreSQL database named `decisiontwin`.
2. Copy `.env.example` to `.env` and fill in your PostgreSQL password.
3. Install dependencies.
4. Run the API server.

## Installation

```bash
cd backend
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file with at least:

```env
DATABASE_URL=postgresql://postgres:<password>@localhost:5432/decisiontwin
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
APP_NAME=DecisionTwin AI Backend
APP_DESCRIPTION=Backend foundation for DecisionTwin AI
APP_VERSION=0.1.0
```

## Running the Server

```bash
uvicorn app.main:app --reload
```

Open the interactive API docs at:

```text
http://localhost:8000/docs
```

## API Endpoints

- `GET /` - service status message
- `GET /api/v1/health` - PostgreSQL health check

## Database and Migrations

SQLAlchemy models live under `app/models` and the shared declarative base is exposed from `app/database/base.py`.
Alembic is configured under `alembic/` for future migrations.

## Project Structure

- `app/api` - API routers and versioned endpoints
- `app/core` - configuration, logging, and exception handling
- `app/database` - SQLAlchemy base, engine, and session management
- `app/models` - ORM model definitions
- `app/schemas` - Pydantic response and request schemas
- `app/services` - service layer for business logic
- `app/utils` - reusable helpers