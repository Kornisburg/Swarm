# Build Retrospective: The Hive (Swarm)

## Overview

Multi-agent engineering workflow platform running on GKE Autopilot.
Agents (Spec → Design → Implement → Review → Test → Deploy) chained via LangGraph,
backed by Cloud SQL, Memorystore Redis, and Chroma vector store.

## Architecture

```
┌─ Ingress (136.68.98.171:80) ─────────────────────────┐
│  FastAPI (GKE Autopilot, 2 replicas)                  │
│  ┌─ Startup: register 6 agents with orchestrator      │
│  ├─ POST /workflows → background task                 │
│  ├─ GET  /health                                       │
│  ├─ GET  /metrics (Prometheus)                        │
│  └─ GET  /workflows/{id}/status (Redis-backed)        │
├─ Cloud SQL (PostgreSQL 15, private IP 10.96.0.3)     │
├─ Memorystore (Redis 7.0, private IP 10.96.12.115)    │
├─ Chroma (in-cluster pod, port 8001)                   │
└─ Vertex AI / Gemini API (via Google Generative AI)    │
```

## Key Decisions & Rationale

| Decision | Choice | Why |
|----------|--------|-----|
| LLM Provider | Gemini 2.5 Flash (Google AI API) | Vertex AI models not accessible in this project; switched from Vertex AI SDK to `langchain-google-genai` |
| Agent orchestration | Sequential in-process loop | `langgraph.ainvoke()` dropped fields between nodes in LangGraph 1.2.9; sequential loop with explicit `WorkflowState(**merge)` works reliably |
| Agent registration | FastAPI startup event | Agents registered once at pod startup via `_register_all_agents()` in `on_event("startup")` |
| Decision tracking | Sync logging (no event loop) | `asyncio.run()` inside an already-running event loop crashes; `_track_decision_sync()` avoids this |
| State passing | `getattr(state, field, {})` | Pydantic v2 `BaseModel` has no `.get()` method — `state.get("code_artifact")` raises `AttributeError` |
| Deploy | Stub agent | Actual deployment handled externally via Cloud Build + GKE; agent is a placeholder |

## Issues Encountered & Resolutions

### 1. No models accessible via Vertex AI
- **Symptom**: 404 on all `ChatVertexAI` model names
- **Root cause**: Vertex AI API (`aiplatform.googleapis.com`) was not enabled on the project
- **Fix**: `gcloud services enable aiplatform.googleapis.com` — but models still returned 404 (project lacks access)
- **Resolution**: Switched to `ChatGoogleGenerativeAI` using a Google AI Studio API key

### 2. Agents returning instantly (0.0s)
- **Symptom**: All agents except spec returned `duration_seconds=0.0`
- **Root cause**: `asyncio.run()` in `@track_decision` decorator called inside running event loop → immediate crash caught by `BaseAgent.invoke()` bare `except`
- **Fix**: Replaced with `_track_decision_sync()` helper

### 3. `state.get()` → `AttributeError`
- **Symptom**: Review and test agents returned instant failures
- **Root cause**: `state.get("code_artifact")` on a Pydantic v2 `BaseModel` (no `.get()` method)
- **Fix**: Changed to `getattr(state, "code_artifact", {})`

### 4. No ruff/mypy/pytest in container
- **Symptom**: Review agent subprocess calls failed silently; test agent couldn't execute tests
- **Fix**: Added LLM-based fallback methods (`_llm_review_fallback`, `_llm_test_fallback`)

### 5. Code artifact shape mismatch
- **Symptom**: Test agent got empty `code` field
- **Root cause**: Implementation agent returns `{files: [{content: "...", path: "..."}]}` not `{code: "..."}` 
- **Fix**: Extract `code` from `files[0].content` when direct `code` key is absent

### 6. Cloud Build deploy step failed
- **Symptom**: `kubectl apply` can't connect to GKE API
- **Root cause**: `gcr.io/cloud-builders/kubectl` needs explicit `gcloud container clusters get-credentials`
- **Fix**: Added that command to the deploy step; also added `--validate=false`

### 7. Workflow ID mismatch
- **Symptom**: API returns one workflow ID but orchestrator uses another
- **Root cause**: `WorkflowOrchestrator.execute()` always generates a new UUID
- **Fix**: Added optional `workflow_id` parameter to `execute()`

## Running Pipeline Measurements

Last successful run (workflow `99939f56`):

| Stage | Duration | Model | Status |
|-------|----------|-------|--------|
| Spec | 6.26s | gemini-2.5-flash | COMPLETED |
| Design | 16.17s | gemini-2.5-flash | COMPLETED |
| Implement | 12.10s | gemini-2.5-flash | COMPLETED |
| Review | 19.02s | gemini-2.5-flash | COMPLETED |
| Test | 0.19s | gemini-2.5-flash | COMPLETED |
| Deploy | 0.00s | (stub) | DEPLOYED |
| **Total** | **53.73s** | | **DEPLOYED** |

## Cost Estimate (Monthly)

| Resource | Est. Monthly Cost |
|----------|-------------------|
| GKE Autopilot (2 pods × 2 vCPU/2Gi) | ~$40-60 |
| Cloud SQL PostgreSQL (1 vCPU, 10GB) | ~$25 |
| Memorystore Redis (1GB Basic) | ~$15 |
| Static IP (unused) | ~$3 |
| Artifact Registry (images) | ~$1 |
| Cloud Build (build minutes) | ~$2 |
| **Total** | **~$85-105/mo** |

## Infrastructure

### GCP Resources Created
- **Project**: `the-hive-dev-1784365808`
- **GKE Cluster**: `hive-dev-cluster` (us-central1, Autopilot)
- **Namespace**: `hive`
- **Workload Identity**: KSA `hive-sa` → GSA `hive-vertex-ai-sa`
- **Cloud SQL**: `hive-dev-postgres` (PostgreSQL 15, private IP)
- **Memorystore**: `hive-dev-redis` (Redis 7.0, 1GB Basic)
- **Static IP**: `hive-ingress-ip` (136.68.98.171)
- **Artifact Registry**: `us-central1-docker.pkg.dev/the-hive-dev-1784365808/hive-dev-images`
- **IAM**: GSA `hive-vertex-ai-sa` with `roles/aiplatform.user`

### Kubernetes Resources
- `hive-deployment.yaml` (2 replicas, FastAPI)
- `hive-service.yaml` (ClusterIP, port 8000)
- `hive-ingress.yaml` (Global external HTTP LB)
- `configmap.yaml` (env vars)
- `secret.yaml` (API keys, DB credentials)
- `hpa.yaml` (CPU-based autoscaling)
- `chroma-deployment.yaml` + `chroma-service.yaml`

## Lingering Issues
- Review agent `_run_static_analysis` subprocess calls (`ruff`, `mypy`) fail silently; always falls through to LLM
- Test agent falls through to LLM fallback (pytest not installed in container)
- Deploy agent is a stub — real deploy needs to be wired to Cloud Build
- Workflow status endpoint (`GET /workflows/{id}/status`) doesn't work (Redis key format mismatch)
- LangSmith telemetry produces 403 errors (placeholder API key) — harmless but noisy
- `hive_tokens_total` and `hive_cost_total_usd_total` Prometheus metrics always zero (no instrumentation wired)
