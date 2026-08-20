# ServiceFlow AI

ServiceFlow AI is a professional full-stack portfolio project for managing customers and their service requests. The project will demonstrate practical API design, relational data modeling, frontend development, automated testing, containerization, and continuous integration.

## Planned stack

- Python and FastAPI
- PostgreSQL
- React and TypeScript
- Docker and Docker Compose
- Pytest
- GitHub Actions

## MVP scope

The first release will support authentication for administrators and agents, customer management, service-request management, agent assignment, request priorities and statuses, search and filtering, and a small operational dashboard.

Advanced permissions, notifications, attachments, and real-time updates are intentionally outside the initial scope.

## Development roadmap

1. Establish the backend, frontend, database, and container foundations.
2. Build and test customer management.
3. Build and test the service-request workflow.
4. Add authentication and role-based access.
5. Connect the React interface to the API.
6. Add dashboard summaries, filtering, seed data, and CI checks.
7. Polish documentation and the demonstration environment.

## Backend database

Start the development PostgreSQL service from the repository root:

```sh
docker compose up -d postgres
```

Install backend dependencies and apply migrations from `backend`:

```sh
python -m pip install -r requirements.txt
alembic upgrade head
```

Create a migration after changing SQLAlchemy models with:

```sh
alembic revision --autogenerate -m "describe change"
```

Run backend tests against the isolated, temporary PostgreSQL service:

```sh
docker compose --profile test up -d postgres-test
cd backend
pytest
```
