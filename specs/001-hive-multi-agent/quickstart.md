# Quick Start Guide: The Hive - Multi-Agent Engineering System

**Feature**: [spec.md](./spec.md)
**Date**: 2026-01-11
**Phase**: Phase 1 - MVP (Core Brain Online)

## Overview

This guide provides step-by-step instructions for setting up and running The Hive Multi-Agent Engineering System MVP. The MVP delivers the core workflow orchestration: specification → design → implementation with basic observability and state management.

---

## Prerequisites

### Required Software

- **Python**: 3.11 or higher
- **Go**: 1.21 or higher (for service mesh sidecars)
- **Docker**: 20.10+ for container services
- **Docker Compose**: 2.0+ for local development stack
- **Git**: For version control

### Required Accounts

- **LLM Provider API Key**: OpenAI or Anthropic API key
  - OpenAI: https://platform.openai.com/api-keys
  - Anthropic: https://console.anthropic.com/

### Optional (Recommended)

- **LangSmith API Key**: For LLM tracing (https://smith.langchain.com/)
- **PostgreSQL Client**: pgAdmin, psql, or similar for database inspection
- **Redis Client**: redis-cli for cache inspection

---

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd Swarm
```

### 2. Install Python Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Install Go Dependencies

```bash
cd infra/go_sidecars
go mod download
cd ../..
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# LLM Provider Configuration
LLM_PROVIDER=openai  # or 'anthropic'
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=the_hive
POSTGRES_USER=hive_user
POSTGRES_PASSWORD=hive_password

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Vector Store Configuration
VECTOR_STORE_TYPE=chroma  # Options: chroma, faiss
CHROMA_PERSIST_DIR=./data/chroma

# Observability Configuration
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_PROJECT=hive-mvp

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Sandbox Configuration
SANDBOX_TYPE=docker  # Options: docker, e2b
```

### 5. Start Infrastructure Services

```bash
# Start PostgreSQL, Redis, and vector store
docker-compose up -d

# Verify services are running
docker-compose ps
```

Expected output:
```
NAME                STATUS    PORTS
swarm-postgres-1    Up        5432->5432
swarm-redis-1       Up        6379->6379
```

### 6. Initialize Database

```bash
# Run database migrations
python -m memory.postgres.migrations migrate
```

---

## Running the System

### Option 1: API Server (Recommended for MVP)

Start the FastAPI gateway:

```bash
# Start API server
python -m infra.fastapi_gateway.app

# Or with uvicorn directly
uvicorn infra.fastapi_gateway.app:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: http://localhost:8000

API Documentation: http://localhost:8000/docs

### Option 2: CLI Tool (Phase 4)

```bash
# Submit a workflow
python -m cli.main run "Add user authentication with OAuth2"

# Check status
python -m cli.main status <workflow-id>

# Retrieve artifacts
python -m cli.main artifacts <workflow-id>
```

---

## Your First Workflow

### Submit a Workflow Request

Using curl:

```bash
curl -X POST http://localhost:8000/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "input_request": "Add user authentication with OAuth2 support using Google provider"
  }'
```

Using Python:

```python
import requests

response = requests.post(
    "http://localhost:8000/workflows",
    json={
        "input_request": "Add user authentication with OAuth2 support using Google provider",
        "priority": "MEDIUM"
    }
)

workflow = response.json()
print(f"Workflow ID: {workflow['workflow_id']}")
print(f"Status: {workflow['status']}")
```

**Response**:
```json
{
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PENDING",
  "created_at": "2026-01-11T10:00:00Z",
  "estimated_completion": "2026-01-11T10:25:00Z"
}
```

### Monitor Workflow Progress

```bash
# Check status
curl http://localhost:8000/workflows/{workflow_id}/status
```

**Response**:
```json
{
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "RUNNING",
  "current_stage": "design",
  "progress": {
    "current_stage_index": 1,
    "total_stages": 3,
    "stage_percent_complete": 65.0,
    "overall_percent_complete": 35.0
  },
  "agent_states": [
    {
      "agent_type": "SPEC_AGENT",
      "status": "COMPLETED",
      "tokens_consumed": 1523
    },
    {
      "agent_type": "DESIGN_AGENT",
      "status": "ACTIVE",
      "current_task": "Generating architecture diagram"
    }
  ]
}
```

### Retrieve Generated Artifacts

```bash
# List all artifacts
curl http://localhost:8000/workflows/{workflow_id}/artifacts

# Get specific artifact
curl http://localhost:8000/workflows/{workflow_id}/artifacts/{artifact_id}
```

**Artifact Response**:
```json
{
  "artifact_id": "650e8400-e29b-41d4-a716-446655440000",
  "artifact_type": "SPECIFICATION",
  "content": {
    "user_stories": [
      {
        "title": "User Authentication",
        "priority": "P1",
        "description": "Users can authenticate using OAuth2",
        "acceptance_criteria": ["Redirect to Google", "Receive callback", "Create session"]
      }
    ],
    "functional_requirements": [
      {"id": "FR-001", "description": "System MUST support OAuth2 with Google provider"},
      {"id": "FR-002", "description": "System MUST create user sessions on successful auth"}
    ]
  },
  "approval_status": "PENDING",
  "version": 1
}
```

---

## Development Workflow

### 1. Make Changes

Edit agent logic, orchestrator, or API routes as needed.

### 2. Restart Services

```bash
# Restart API server
uvicorn infra.fastapi_gateway.app:app --reload

# Restart Go telemetry service (if running)
cd infra/go_sidecars/telemetry
go run main.go exporter.go
```

### 3. Run Tests

```bash
# Run all tests
pytest

# Run specific test category
pytest tests/unit/test_agents/
pytest tests/integration/test_full_workflow.py
pytest tests/contract/test_workflow_api.py

# Run with coverage
pytest --cov=. --cov-report=html
```

### 4. View Logs

```bash
# API logs (if running with uvicorn)
# Logs are printed to stdout

# Container logs
docker-compose logs -f postgres
docker-compose logs -f redis

# Agent decisions (via LangSmith)
# Visit: https://smith.langchain.com/
```

---

## Observability

### LangSmith Tracing

1. Visit https://smith.langchain.com/
2. Navigate to your project
3. View workflow traces, agent decisions, and performance metrics

### Database Inspection

```bash
# Connect to PostgreSQL
docker exec -it swarm-postgres-1 psql -U hive_user -d the_hive

# View workflows
SELECT id, status, current_stage, created_at
FROM workflow_sessions
ORDER BY created_at DESC
LIMIT 10;

# View agent decisions
SELECT agent_type, decision_type, confidence, rationale
FROM decision_records
WHERE workflow_id = '...'
ORDER BY timestamp;
```

### Redis Inspection

```bash
# Connect to Redis
docker exec -it swarm-redis-1 redis-cli

# View active workflow state
GET workflow:abc-123

# View workflow stage
GET workflow:abc-123:stage

# View artifacts list
LRANGE workflow:abc-123:artifacts 0 -1
```

---

## Troubleshooting

### Issue: "Connection refused" errors

**Solution**: Ensure infrastructure services are running:
```bash
docker-compose ps
docker-compose up -d
```

### Issue: "LLM API key not found"

**Solution**: Verify `.env` file exists with valid API keys:
```bash
cat .env | grep API_KEY
```

### Issue: Workflow stuck in PENDING status

**Solution**: Check orchestrator logs and ensure LangGraph is properly initialized:
```bash
# Check orchestrator health
curl http://localhost:8000/health

# View logs for errors
tail -f logs/orchestrator.log
```

### Issue: Sandbox execution fails

**Solution**: Verify Docker is running and accessible:
```bash
docker ps
docker run --rm hello-world
```

### Issue: High token costs

**Solution**: Enable prompt caching in `.env`:
```bash
ENABLE_PROMPT_CACHE=true
CACHE_TTL_SECONDS=604800  # 7 days
```

---

## Next Steps

### Phase 2 Features (Post-MVP)

- **Review Agent**: Automated code review and quality analysis
- **Test Agent**: Test generation and execution
- **Vector Memory**: Enhanced context retention and semantic search
- **Observability MVP**: Grafana dashboards and metrics

### Migration Path

When ready to scale beyond MVP:

1. **Migrate to E2B** for sandbox isolation
2. **Deploy to Kubernetes** for orchestration
3. **Add Go service mesh** for telemetry and rate limiting
4. **Implement distributed tracing** with Jaeger

---

## Additional Resources

- **Full API Documentation**: http://localhost:8000/docs
- **Architecture Overview**: [docs/architecture.md](../docs/architecture.md)
- **Agent Documentation**: [docs/agents.md](../docs/agents.md)
- **Constitution**: [.specify/memory/constitution.md](../../.specify/memory/constitution.md)
- **Implementation Plan**: [plan.md](./plan.md)
- **Data Model**: [data-model.md](./data-model.md)

---

## Support

For issues or questions:
- Check troubleshooting section above
- Review logs in `logs/` directory
- Inspect traces in LangSmith
- Check database state for workflow history
