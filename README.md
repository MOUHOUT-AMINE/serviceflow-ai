# ServiceFlow AI

ServiceFlow AI is a full-stack customer service application built with React, TypeScript, FastAPI, and PostgreSQL. It brings customer records, service requests, agent assignments, and workload reporting into one interface, with an optional AI assistant to support ticket triage and draft customer replies.

The project demonstrates end-to-end software engineering: a typed frontend, a REST API with role-based access control, relational data modelling, database migrations, automated tests, and containerised local deployment.

## Live demo

| Service | Production URL |
| --- | --- |
| Frontend | Pending confirmation |
| Backend / API | Pending confirmation |
| API health endpoint | Pending backend URL confirmation; path: `/health` |

Production addresses are not recorded in this repository. These entries must be updated with the confirmed deployment URLs. No passwords or private demo credentials are published here.

The API exposes an unauthenticated `GET /health` endpoint returning `{"status":"ok"}`. This is an application liveness check; it does not check database connectivity or AI provider availability. Interactive API documentation is available at `/docs`, with the OpenAPI schema at `/openapi.json`.

## Key features

- **JWT authentication:** email/password login with expiring JWT bearer tokens and Argon2 password hashing. Inactive accounts cannot authenticate or continue using existing tokens.
- **Admin / Agent role-based access:** backend-enforced permissions restrict user management, ticket assignment, and record deletion to administrators. Agents can create, view, and edit customers and tickets and access their own workload dashboard.
- **Customer management:** create, view, and edit customer names and email addresses; administrators can delete records.
- **Service request management:** create, view, and edit tickets linked to customers, with creator and update metadata available through the API. Administrators can delete tickets.
- **Agent assignment:** administrators can assign tickets to active agents, reassign them, or remove an assignment.
- **Status and priority workflows:** update ticket statuses (`open`, `in_progress`, `resolved`, `closed`) and priorities (`low`, `medium`, `high`) as work progresses.
- **Search and filtering:** API filters for customer, assignee, status, and priority, plus frontend search across the titles and descriptions of loaded results.
- **Operational dashboards:** administrators see customer and request totals, status and priority breakdowns, unassigned requests, and workload by assignee. Agents see a summary of their own assigned work.
- **User administration:** administrators can create users, change roles, and activate or deactivate accounts, with safeguards against deactivating or demoting their own account.
- **AI Ticket Assistant:** optionally generate a summary, suggested priority, and recommended action from a stored ticket's title and description. AI is disabled by default, and the core application works without an API key.
- **Suggested customer reply:** review an AI-generated draft and copy it to the clipboard. The application does not send the reply.
- **Human-in-the-loop priority updates:** generating suggestions leaves the ticket unchanged. A user must explicitly select **Apply suggested priority** to save the recommended priority to the ticket.

Ticket statuses are `open`, `in_progress`, `resolved`, and `closed`; priorities are `low`, `medium`, and `high`. These values are shared by the API and database. Some interface labels and the ticket detail view are currently in French; other screens use English.

## Technology and architecture

| Layer | Implementation |
| --- | --- |
| Frontend | React 19, TypeScript, Vite, React Router |
| Data fetching and forms | TanStack Query, React Hook Form, Zod |
| Backend | Python 3.12, FastAPI, Pydantic, SQLAlchemy 2, Psycopg |
| Database | PostgreSQL 16, Alembic migrations |
| Authentication | PyJWT, pwdlib with Argon2 |
| AI integration | Optional OpenAI provider accessed from the backend via HTTPX |
| Deployment | Docker Compose; static frontend served by Nginx |
| Quality checks | Pytest, Vitest, React Testing Library, MSW, GitHub Actions |

In the Compose setup, the browser accesses the Nginx frontend, which proxies `/api` requests to FastAPI. The backend accesses PostgreSQL through SQLAlchemy. Route handlers, validation schemas, database models, and repositories are organised by feature. The AI assistant uses a provider interface with a disabled implementation so the core application can run without an API key.

```text
frontend/src/
  api/                API client and endpoint functions
  auth/               Authentication state and route guards
  pages/              Dashboard, customers, requests, and users
  components/         Shared layout and interface components
  test/               Frontend tests and mock API setup
backend/
  app/
    auth/             Login, token verification, and admin bootstrap
    customers/        Customer API, schemas, models, and repository
    service_requests/ Ticket API, schemas, models, and repository
    dashboard/        Role-specific reporting
    users/            Administrator-only user management
    ai/               Optional ticket assistant and provider integration
  alembic/            Versioned database migrations
  tests/              API, database, authentication, and AI tests
.github/workflows/    Continuous integration
compose.yaml          Application and isolated test database services
```

## Run locally

### Docker Compose

Prerequisites: Docker with the Compose plugin.

1. Copy `.env.example` to `.env` in the repository root.
2. Set your own `POSTGRES_PASSWORD`, a random `JWT_SECRET_KEY` of at least 32 characters, and your local `BOOTSTRAP_ADMIN_EMAIL` and `BOOTSTRAP_ADMIN_PASSWORD`.
3. Build and start the application:

   ```sh
   docker compose up --build -d
   ```

4. Once the backend is running, create the initial administrator:

   ```sh
   docker compose exec backend python -m app.auth.bootstrap
   ```

5. Open the frontend and sign in with the local administrator account you configured.

| Local service | Default address |
| --- | --- |
| Frontend | http://localhost:5173 |
| API base | http://localhost:8000 |
| API documentation | http://localhost:8000/docs |
| API health | http://localhost:8000/health |

Compose waits for PostgreSQL health and runs `alembic upgrade head` before starting the API. Database data persists in the `postgres_data` volume. Changing `POSTGRES_PASSWORD` in `.env` does not update the password of an already initialised database.

The bootstrap command can be rerun. For an existing account with the configured email, it ensures that the account is active and has the administrator role.

### Frontend development server

With the backend running, use Node.js 22 and run:

```sh
cd frontend
npm ci
```

Copy `frontend/.env.example` to `frontend/.env` to use the local API at `http://localhost:8000`, then run `npm run dev`. Stop the Compose frontend first if it occupies port 5173. The backend's default CORS origin is `http://localhost:5173`.

### Optional AI configuration

AI is disabled by default. To enable it, configure `AI_PROVIDER=openai`, `AI_API_KEY`, and `AI_MODEL` in the root `.env`, then recreate the backend with `docker compose up -d backend`. `AI_TIMEOUT_SECONDS` defaults to 15 seconds.

When enabled, the backend sends the selected ticket's title and description to the provider. The API key remains in backend configuration. Provider responses are validated against a structured schema; disabled, invalid, or unavailable AI responses produce an error state while the rest of the ticket workflow remains usable. Suggestions are returned without being persisted.

## Testing and continuous integration

The [GitHub Actions workflow](.github/workflows/ci.yml) runs on pushes and pull requests. It applies migrations to PostgreSQL and runs backend tests, then separately runs frontend type checking, tests, and a production build.

Backend tests cover authentication, permissions, customer and ticket operations, assignment rules, filtering, dashboard aggregation, migration round trips, and AI success and failure handling. Frontend tests use React Testing Library and MSW to exercise the interface against mocked API responses.

To run backend tests locally, use Python 3.12 with a virtual environment and start the isolated test database from the repository root:

```sh
docker compose --profile test up -d --wait postgres-test
cd backend
python -m pip install -r requirements.txt
python -m pytest
```

The default test configuration targets the Compose test database on port 5433. If you customise its connection settings, set `TEST_DATABASE_URL` accordingly in your shell. The test suite requires a database name ending in `_test` and clears its application tables between tests.

To run frontend checks:

```sh
cd frontend
npm ci
npm run typecheck
npm test
npm run build
```
