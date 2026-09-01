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

## Run the full application with Docker

Copy `.env.example` to `.env` and replace `POSTGRES_PASSWORD`,
`JWT_SECRET_KEY`, and `BOOTSTRAP_ADMIN_PASSWORD` with local values. Then run:

```sh
docker compose up --build
```

The backend builds its PostgreSQL URL from the separate `POSTGRES_*` settings,
so `POSTGRES_PASSWORD` may contain URL-reserved characters such as `@`, `:`,
`/`, `?`, `#`, and `%`. When the backend runs on the host it connects to
`DATABASE_HOST=localhost`; Compose overrides that host to the `postgres` service.
`DATABASE_URL` remains available as an optional full override, but credentials in
that value must already be percent-encoded.

Open the frontend at http://localhost:5173. The API and its interactive docs are
also exposed at http://localhost:8000 and http://localhost:8000/docs.

### Optional AI ticket assistant

AI suggestions are disabled by default, and no API key is required to start or
use ServiceFlow. To enable the OpenAI provider, set `AI_PROVIDER=openai`,
`AI_API_KEY`, and `AI_MODEL`; `AI_TIMEOUT_SECONDS` controls the provider request
timeout (15 seconds by default). Compose passes these settings only to the
backend. The API key is never included in frontend configuration or responses.

Authenticated users can generate a non-persistent summary, suggested priority,
and recommended action from a ticket's stored title and description. Suggestions
are always presented for review and never change the ticket automatically. When
AI is disabled, misconfigured, or temporarily unavailable, the rest of the
ticket workflow remains operational.

The backend waits for PostgreSQL to become healthy, then runs `alembic upgrade
head` before starting Uvicorn. Consequently, all committed database migrations
are applied automatically on every container start. To create the initial admin
after startup, run:

```sh
docker compose exec backend python -m app.auth.bootstrap
```

The frontend is built as static assets and served by Nginx. Requests under
`/api` are proxied over the private Compose network to the backend, avoiding a
browser-visible container hostname.

### Changing the local PostgreSQL password

PostgreSQL uses `POSTGRES_PASSWORD` only when it initializes a new data
directory. Changing the value in `.env` does **not** change the password stored
in an existing `postgres_data` volume, and the backend will fail authentication
until the stored password and `.env` agree.

For disposable local development data, stop the stack and recreate its volumes:

```sh
docker compose down -v
docker compose up --build
```

`docker compose down -v` permanently deletes the local PostgreSQL volume and all
data in it. Use this reset only when that development data is safe to discard;
it is not an automatic upgrade step. To preserve local data, change the role's
password inside PostgreSQL before updating `.env` (or back up the data first),
then restart the stack with `docker compose up --build`.

## Run services individually

Start the development PostgreSQL service from the repository root:

```sh
docker compose up -d postgres
```

Install backend dependencies and apply migrations from `backend`:

```sh
python -m pip install -r requirements.txt
alembic upgrade head
```

Configure `JWT_SECRET_KEY`, then create the first administrator after migrating:

```sh
python -m app.auth.bootstrap
```

The command reads `BOOTSTRAP_ADMIN_EMAIL` and `BOOTSTRAP_ADMIN_PASSWORD` and is
safe to rerun when that email already exists. Log in through `POST /auth/login`
using OAuth2 form fields `username` (the email address) and `password`, then send
the returned token as `Authorization: Bearer <token>`.

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
