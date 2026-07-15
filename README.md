# The Hive

The Hive is a proof-of-concept multi-agent engineering system for turning a product request into specification, design, implementation, review, test, and deployment artifacts. The repository combines a FastAPI gateway, Click-based CLI, LangGraph-style orchestration primitives, persistent memory backends, sandbox execution helpers, and observability integrations.

## Architecture at a glance

```text
User / CLI / API client
        |
        v
FastAPI gateway + Click CLI
        |
        v
Workflow orchestrator graph
        |
        +--> Spec agent
        +--> Design agent
        +--> Implementation agent
        +--> Review agent
        +--> Test agent
        +--> Deploy agent
        |
        v
State, memory, artifacts, telemetry
(Postgres, Redis, Chroma, Prometheus, Jaeger/LangSmith)
```

Key source areas:

- `infra/fastapi_gateway/` exposes HTTP routes for health checks, workflow submission, status, and artifacts.
- `cli/` exposes local workflow and configuration commands through the `hive` console script.
- `core/orchestrator/` contains graph, router, checkpoint, and workflow state primitives.
- `agents/` contains role-specific agent implementations.
- `memory/` contains Redis, Postgres, and vector-store adapters.
- `observability/` contains tracing and exporter helpers.
- `specs/001-hive-multi-agent/` documents the product requirements, contracts, quickstart, and implementation tasks.

## Local development setup

Requires Python 3.11+ and Docker if you want backing services.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Create a local environment file if you plan to run workflows against real LLM providers:

```bash
cp .env.example .env  # if you add one later, or create .env manually
cat > .env <<'ENV'
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=the_hive
POSTGRES_USER=hive_user
POSTGRES_PASSWORD=hive_password
REDIS_HOST=localhost
REDIS_PORT=6379
CHROMA_HOST=localhost
CHROMA_PORT=8001
ENV
```

## Run the system locally

Start infrastructure services:

```bash
docker compose up -d postgres redis chroma
```

Run the API gateway:

```bash
uvicorn infra.fastapi_gateway.app:app --host 0.0.0.0 --port 8000 --reload
```

Verify it is healthy:

```bash
curl http://localhost:8000/health
```

Use the CLI:

```bash
hive version
hive workflow run "Add user authentication"
hive workflow status <workflow-id>
hive workflow artifacts <workflow-id>
```

## Testing strategy

The POC is structured to support layered confidence:

1. **Unit tests** validate deterministic models and orchestrator primitives without external services.
2. **Contract tests** validate HTTP request/response shape for gateway endpoints.
3. **Integration tests** exercise the workflow path with mocked or local infrastructure.
4. **Container smoke tests** validate the production image starts and responds to `/health`.
5. **CI/CD gates** start with import smoke tests, deterministic unit coverage, image build, and optional deployment; lint, formatting, and type checks are called out as the next hardening step once the legacy codebase is normalized.

Recommended local checks:

```bash
python -m pytest tests/unit -q
python -m pytest tests/contract -q
python -m pytest --cov=. --cov-report=term-missing
ruff check .
black --check .
mypy core agents infra memory observability cli
```

## Refactoring roadmap

Use this roadmap to turn the POC into blog-friendly engineering evidence:

- **Stabilize import boundaries.** Keep package imports absolute from the repository root so the API works both as an installed package and under `uvicorn`.
- **Separate pure domain logic from side effects.** Keep agent routing, state transitions, and artifact selection unit-testable; move Postgres, Redis, Docker, and LLM calls behind interfaces.
- **Inject dependencies.** Replace module-level singletons with providers/factories that tests can override cleanly.
- **Define typed contracts.** Keep Pydantic schemas at the API boundary and dataclasses/Pydantic models in core workflow state.
- **Make observability first-class.** Emit workflow IDs, stage names, token counts, and artifact IDs in traces and logs.
- **Harden deployability.** Use immutable images, environment-specific configuration, health checks, and migrations as a release step.

## Deployment proof of concept

### Docker image

Build and run the API image locally:

```bash
docker build -t the-hive:local .
docker run --rm -p 8000:8000 --env-file .env the-hive:local
```

### GitHub Actions CI/CD

This repository includes a CI/CD workflow in `.github/workflows/ci-cd.yml` that demonstrates:

- dependency installation with Python 3.11 and 3.12,
- import smoke testing for the FastAPI application,
- deterministic unit-test coverage for the core workflow state model,
- Docker image build validation,
- container registry publish on `main` pushes,
- a placeholder production deployment job guarded by a protected GitHub environment.

The next CI hardening milestone is to promote `ruff check .`, `black --check .`, `mypy core agents infra memory observability cli`, and the full `python -m pytest` suite from local refactoring targets to required checks after the existing lint and async-test debt is addressed.

For a real deployment, add repository secrets such as cloud credentials and replace the placeholder deployment step with your target platform command, for example Kubernetes, ECS, Fly.io, Render, or a VM-based `docker compose pull && docker compose up -d` rollout.

## Blog narrative outline

A strong technical blog post can walk through:

1. **Problem:** engineering teams lose context between specification, implementation, review, tests, and deployment.
2. **Architecture:** a graph-orchestrated multi-agent system with explicit state and artifact contracts.
3. **Testing:** unit, contract, integration, and smoke tests mapped to risks.
4. **Refactoring:** dependency inversion, typed boundaries, and deterministic core logic.
5. **Delivery:** GitHub Actions as executable documentation for quality gates and release flow.
6. **Lessons learned:** what should stay deterministic, where LLM calls belong, and how observability makes agentic systems debuggable.
