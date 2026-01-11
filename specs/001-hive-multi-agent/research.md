# Research & Technology Decisions: The Hive - Multi-Agent Engineering System

**Feature**: [spec.md](./spec.md)
**Date**: 2026-01-11
**Phase**: Phase 0 - Research & Technology Decisions

## Overview

This document captures research findings and technology decisions for The Hive Multi-Agent Engineering System. All decisions are aligned with the constitution's requirements for layered architecture, deterministic orchestration, security-first execution, and observability.

---

## 1. Orchestration Framework

### Decision: LangGraph for Workflow Orchestration

**Choice**: LangGraph (Python) as the primary workflow orchestration framework

**Rationale**:
- **Native Python Integration**: Seamless integration with LangChain ecosystem and LLM providers
- **Graph-Based Control**: Explicit state graph definition matches constitution's deterministic orchestration requirement
- **Built-in State Management**: Automatic state persistence and checkpointing across workflow stages
- **Visualization Support**: Built-in graph visualization for debugging and observability
- **Proven Production Use**: Battle-tested at scale by LangChain customers

**Alternatives Considered**:
1. **Temporal (Go)**: Rejected due to Python-heavy agent ecosystem and LLM integration complexity
2. **Prefect/CrewAI**: Rejected due to less explicit graph control and more free-flowing agent patterns
3. **Custom Orchestration**: Rejected due to reinventing complex state management and checkpointing

**Best Practices**:
- Use `StateGraph` for explicit state management with typed state schemas
- Implement conditional edges for deterministic routing (not LLM-based routing)
- Define clear node interfaces with Pydantic models for inputs/outputs
- Use checkpointers for workflow persistence and resumption
- Implement retry logic at node level for transient failures

**Implementation Notes**:
```python
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

class WorkflowState(BaseModel):
    input_request: str
    current_stage: str
    artifacts: Dict[str, Any]
    decisions: List[DecisionRecord]
    errors: List[str]

# Define graph structure
workflow = StateGraph(WorkflowState)
workflow.add_node("spec_agent", spec_agent_node)
workflow.add_node("design_agent", design_agent_node)
workflow.add_edge("spec_agent", "design_agent")
```

---

## 2. Sandbox Solution

### Decision: Docker SDK for MVP with E2B Upgrade Path

**Choice**: Docker Python SDK for Phase 1-2, E2B for Phase 3+

**Rationale**:
- **Docker SDK** (MVP phases):
  - Ubiquitous availability, no external dependencies
  - Full control over container configuration and resource limits
  - Straightforward integration with existing CI/CD pipelines
  - Low operational complexity for initial development

- **E2B** (Production phases):
  - Specialized for AI code execution with pre-configured environments
  - Built-in security hardening and network isolation
  - Faster cold start times (< 2 seconds vs Docker's ~5 seconds)
  - Managed service reduces operational overhead

**Alternatives Considered**:
1. **gVisor/Firecracker**: Rejected due to complexity overhead for initial phases
2. **AWS Lambda**: Rejected due to cold start latency and execution time limits
3. **Nomad job isolation**: Rejected due to additional infrastructure complexity

**Best Practices**:
- Implement resource limits via Docker API: `mem_limit`, `cpu_quota`, `blkio_config`
- Use read-only filesystem mounts with `/tmp` as writable tmpfs
- Drop all capabilities and run as non-root user
- Implement health checks and timeout enforcement
- Log stdout/stderr for debugging while preventing escape attempts

**Security Configuration**:
```python
import docker

client = docker.from_env()

container = client.containers.run(
    image="python:3.11-slim",
    command=code_to_execute,
    mem_limit="512m",
    cpu_quota=50000,  # 0.5 CPU
    network_mode="none",  # No network access
    read_only=True,
    tmpfs={"/tmp": "size=100m"},
    security_opt=["no-new-privileges"],
    cap_drop=["ALL"],
    user="nobody",
    timeout=300,  # 5 minutes
    remove=True
)
```

---

## 3. Vector Store Selection

### Decision: Chroma for MVP with Migration Path to Milvus

**Choice**: Chroma DB for Phases 1-2, Milvus for Phase 3+ scale

**Rationale**:
- **Chroma** (MVP phases):
  - Embeddable in-process (no separate infrastructure)
  - Simple API for quick development
  - Native Python integration
  - Sufficient for single-machine deployment

- **Milvus** (Production scale):
  - Distributed architecture for horizontal scaling
  - Advanced indexing (IVF, HNSW) for sub-100ms queries at scale
  - Cloud-native with Kubernetes support
  - Proven at billion-vector scale

**Alternatives Considered**:
1. **FAISS**: Rejected due to lack of persistence and built-in serving API
2. **Pinecone**: Rejected due to vendor lock-in and cost at scale
3. **Qdrant**: Rejected due to smaller community and ecosystem

**Best Practices**:
- Maintain three separate collections per constitution:
  1. `agent_cognitive_memory` - Agent decisions and rationale
  2. `knowledge_base` - Engineering best practices and patterns
  3. `code_semantic_index` - Code for impact analysis and refactor support
- Use OpenAI `text-embedding-3-small` (cheaper, faster) or `sentence-transformers` (self-hosted)
- Implement metadata filtering for efficient querying (e.g., by project, agent type, timestamp)
- Set up periodic compaction to remove outdated embeddings

**Schema Design**:
```python
import chromadb

client = chromadb.Client()

# Agent Cognitive Memory Collection
cognitive_memory = client.create_collection(
    name="agent_cognitive_memory",
    metadata={"hnsw:space": "cosine", "hnsw:M": 16}
)

# Knowledge Base Collection
knowledge_base = client.create_collection(
    name="knowledge_base",
    metadata={"hnsw:space": "cosine"}
)

# Code Semantic Index Collection
code_index = client.create_collection(
    name="code_semantic_index",
    metadata={"hnsw:space": "cosine"}
)
```

---

## 4. Go-Python Interoperability

### Decision: gRPC for Service Mesh Communication

**Choice**: gRPC for communication between Python orchestrator and Go sidecars

**Rationale**:
- **Type Safety**: Protocol Buffers ensure type-safe contracts
- **Performance**: Binary serialization faster than JSON
- **Streaming**: Built-in bidirectional streaming for real-time metrics
- **Code Generation**: Auto-generated client/server stubs reduce boilerplate
- **Ecosystem**: First-class support in both Go and Python

**Alternatives Considered**:
1. **REST/JSON**: Rejected due to serialization overhead and lack of streaming
2. **NATS/RabbitMQ**: Rejected due to additional infrastructure complexity
3. **Shared Memory**: Rejected due to complexity and cross-language limitations

**Best Practices**:
- Define service interfaces in `.proto` files in `/infra/go_sidecars/proto`
- Use unary RPCs for control plane operations (start/stop workflow)
- Use server streaming for metrics and logs (continuous telemetry push)
- Implement keepalive pings for connection health
- Use TLS for inter-service communication

**Service Definition**:
```protobuf
// telemetry.proto
syntax = "proto3";

package telemetry;

service TelemetryService {
    rpc StreamMetrics(MetricsRequest) returns (stream MetricsResponse);
    rpc GetAgentDecision(DecisionRequest) returns (DecisionResponse);
}

message MetricsRequest {
    string workflow_id = 1;
    string agent_id = 2;
}

message MetricsResponse {
    double cpu_percent = 1;
    int64 memory_bytes = 2;
    int64 tokens_used = 3;
    double cost_estimate = 4;
}
```

---

## 5. LLM Provider Abstraction

### Decision: Factory Pattern with Provider-Specific Adapters

**Choice**: Abstract LLM provider interface with adapters for OpenAI, Anthropic, and future providers

**Rationale**:
- **Vendor Flexibility**: Avoid lock-in to single provider
- **Cost Optimization**: Route requests based on cost/quality requirements
- **Redundancy**: Failover between providers during outages
- **A/B Testing**: Compare model quality across providers

**Alternatives Considered**:
1. **Direct OpenAI-only**: Rejected due to vendor lock-in and single point of failure
2. **LangX Provider Abstraction**: Using LangChain's built-in abstraction (chosen approach)

**Best Practices**:
- Implement `LLMProvider` abstract base class with `complete()` and `stream()` methods
- Use environment variables for default provider selection
- Implement request queuing and rate limiting per provider
- Cache prompts using semantic similarity (not exact string matching)
- Track token usage and cost per provider for budget governance

**Implementation Pattern**:
```python
from abc import ABC, abstractmethod
from enum import Enum

class LLMProviderType(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> str:
        pass

    @abstractmethod
    async def stream(self, prompt: str, **kwargs):
        pass

    @abstractmethod
    def estimate_cost(self, prompt: str, response: str) -> float:
        pass

class ProviderFactory:
    @staticmethod
    def create(provider_type: LLMProviderType) -> LLMProvider:
        if provider_type == LLMProviderType.OPENAI:
            return OpenAIProvider()
        elif provider_type == LLMProviderType.ANTHROPIC:
            return AnthropicProvider()
        else:
            raise ValueError(f"Unknown provider: {provider_type}")
```

---

## 6. State Management Strategy

### Decision: Hybrid Redis + PostgreSQL with LangGraph Checkpointers

**Choice**:
- **Redis**: Fast, session-scoped state for active workflow execution
- **PostgreSQL**: Persistent storage for workflow history, artifacts, and decision records
- **LangGraph Checkpointers**: Automatic state persistence and recovery

**Rationale**:
- **Redis**: Sub-millisecond read/write for active workflow state
- **PostgreSQL**: ACID guarantees for artifact persistence and querying
- **Checkpointing**: Built-in to LangGraph for workflow resumption

**Best Practices**:
- Store workflow state in Redis with TTL (24 hours) for cleanup
- Archive completed workflows to PostgreSQL for historical analysis
- Use PostgreSQL JSONB for flexible artifact storage
- Implement workflow versioning for schema evolution
- Set up periodic cleanup of abandoned workflows

**Schema Design**:
```sql
-- Workflow Sessions Table
CREATE TABLE workflow_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(50) NOT NULL,
    input_request JSONB NOT NULL,
    artifacts JSONB,
    decisions JSONB,
    performance_metrics JSONB
);

-- Decision Records Table
CREATE TABLE decision_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflow_sessions(id),
    agent_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    input_context JSONB NOT NULL,
    output_decision JSONB NOT NULL,
    confidence FLOAT,
    rationale TEXT
);

CREATE INDEX idx_decision_records_workflow ON decision_records(workflow_id);
CREATE INDEX idx_decision_records_agent ON decision_records(agent_type);
```

---

## 7. Observability Strategy

### Decision: OpenTelemetry + LangSmith + Prometheus Stack

**Choice**:
- **LangSmith**: LLM-specific tracing and decision provenance
- **OpenTelemetry**: Unified metrics and tracing collection
- **Prometheus**: Metrics storage and querying
- **Grafana**: Dashboard visualization
- **Jaeger**: Distributed tracing for service interactions

**Rationale**:
- **LangSmith**: Purpose-built for LLM application observability
- **OpenTelemetry**: Vendor-neutral standard for observability
- **Prometheus/Grafana**: Industry-standard metrics stack
- **Jaeger**: Distributed tracing for microservice debugging

**Best Practices**:
- Instrument all agent calls with LangSmith tracing
- Export OpenTelemetry metrics to Prometheus
- Use semantic attributes for span naming (not dynamic values)
- Implement RED metrics (Rate, Errors, Duration) for all endpoints
- Create Grafana dashboards for: token burn, cost per workflow, agent latency
- Set up alerts for: high error rates, long-running workflows, cost thresholds

**Key Metrics to Track**:
```python
from prometheus_client import Counter, Histogram, Gauge

# Token usage and cost
tokens_used = Counter('hive_tokens_total', 'Total tokens consumed', ['provider', 'model'])
cost_incurred = Counter('hive_cost_total_usd', 'Total cost in USD', ['provider'])

# Workflow performance
workflow_duration = Histogram('hive_workflow_duration_seconds', 'Workflow duration', ['stage'])
workflow_status = Counter('hive_workflow_status_total', 'Workflow completion status', ['status'])

# Agent performance
agent_invocations = Counter('hive_agent_invocations_total', 'Agent invocations', ['agent_type'])
agent_duration = Histogram('hive_agent_duration_seconds', 'Agent duration', ['agent_type'])

# Resource usage
active_workflows = Gauge('hive_active_workflows', 'Number of active workflows')
sandbox_containers = Gauge('hive_sandbox_containers', 'Number of running sandbox containers')
```

---

## 8. Testing Strategy

### Decision: Pyramid with Contract, Integration, and Unit Tests

**Choice**:
- **Contract Tests**: Verify API contracts between services
- **Integration Tests**: End-to-end workflow testing with testcontainers
- **Unit Tests**: Agent logic and orchestration rules

**Best Practices**:
- Use `pytest` for Python tests, `go test` for Go tests
- Mock LLM responses for deterministic unit testing
- Use `testcontainers` for real PostgreSQL, Redis, and Chroma instances
- Implement contract tests for all gRPC services
- Test failure modes: network failures, LLM outages, sandbox crashes
- Use property-based testing (hypothesis) for state management logic

**Test Organization**:
```text
/tests/
├── contract/
│   ├── test_workflow_api.py      # FastAPI contract tests
│   ├── test_telemetry_service.py # gRPC contract tests
│   └── test_sandbox_api.py       # Sandbox contract tests
├── integration/
│   ├── test_full_workflow.py     # End-to-end workflow
│   ├── test_agent_collaboration.py # Agent interaction tests
│   └── test_failure_recovery.py  # Failure scenario tests
└── unit/
    ├── test_agents/
    │   ├── test_spec_agent.py
    │   ├── test_design_agent.py
    │   └── test_implementation_agent.py
    ├── test_orchestrator/
    │   ├── test_graph_routing.py
    │   └── test_state_management.py
    └── test_memory/
        ├── test_vector_store.py
        └── test_decision_tracking.py
```

---

## 9. CLI Design

### Decision: Click-based CLI with Structured Output

**Choice**: Click (Python) for CLI framework with JSON output option

**Rationale**:
- **Click**: Declarative CLI syntax with automatic help generation
- **Rich**: Formatted output with progress bars and tables
- **JSON Output**: Machine-parsable for CI/CD integration

**Best Practices**:
- Implement subcommands: `run`, `status`, `artifacts`, `logs`
- Support `--output json|table` flag for output format
- Use `.env` file for configuration (not flags)
- Implement progress bars for long-running workflows
- Provide colored output for human readability

**CLI Structure**:
```python
import click

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """The Hive - Multi-Agent Engineering System"""
    pass

@cli.command()
@click.argument("feature_description", nargs=-1)
@click.option("--output", type=click.Choice(["json", "table"]), default="table")
def run(feature_description, output):
    """Run a workflow from a feature description"""
    description = " ".join(feature_description)
    workflow_id = submit_workflow(description)
    watch_workflow(workflow_id, output_format=output)

@cli.command()
@click.argument("workflow_id")
def status(workflow_id):
    """Get workflow status"""
    display_status(get_workflow_status(workflow_id))

@cli.command()
@click.argument("workflow_id")
@click.option("--artifact", type=str)
def artifacts(workflow_id, artifact):
    """Retrieve workflow artifacts"""
    download_artifacts(workflow_id, artifact)
```

---

## Summary

| Area | Technology | Phase |
|------|-----------|-------|
| Orchestration | LangGraph | 1-4 |
| Sandbox | Docker SDK (1-2) → E2B (3-4) | Upgrade path |
| Vector Store | Chroma (1-2) → Milvus (3-4) | Upgrade path |
| API Gateway | FastAPI | 1-4 |
| Service Mesh | Go + gRPC | 3-4 |
| State | Redis + PostgreSQL | 1-4 |
| Observability | LangSmith + OpenTelemetry + Prometheus + Grafana | 1-4 |
| LLM Providers | OpenAI, Anthropic (via LangChain) | 1-4 |
| Testing | pytest, testcontainers, contract tests | 1-4 |
| CLI | Click + Rich | 4 |

All decisions align with constitution principles and support incremental delivery through four phases.
