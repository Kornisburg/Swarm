<!--
  Sync Impact Report
  ==================
  Version change: INITIAL → 1.0.0
  Rationale: Initial constitution ratification for The Hive multi-agent engineering system

  Modified principles: N/A (initial version)
  Added sections:
    - Core Principles (5 principles)
    - Architecture Standards
    - Development Workflow
    - Governance

  Templates status:
    ✅ plan-template.md - Reviewed, aligned with constitution
    ✅ spec-template.md - Reviewed, aligned with constitution
    ✅ tasks-template.md - Reviewed, aligned with constitution

  Follow-up TODOs: None
-->

# The Hive Constitution

## Core Principles

### I. Layered Architecture

The Hive MUST be implemented as a **layered, composable, and observable intelligence platform** with clear separation of concerns:

1. **Intelligence Layer** — LLM reasoning & workflows (LangGraph orchestrator, specialized agents)
2. **Infrastructure & Execution Layer** — Runtime, APIs, networking, security (FastAPI, Go service mesh)
3. **Memory & Knowledge Layer** — State + vector intelligence (Redis, PostgreSQL, Vector DB)
4. **Observability Layer** — Truth & introspection (LangSmith, Prometheus, Grafana, Jaeger)

**Rationale**: Prevents "toy agent systems" and builds toward production-grade engineering automation. Each layer has distinct responsibilities and clear interfaces.

### II. Deterministic Orchestration (NON-NEGOTIABLE)

**Mandatory Rules**:
- All agent workflows MUST be controlled by LangGraph (not free-flowing agent conversations)
- Orchestrator MUST use deterministic routing when logic is obvious (no unnecessary LLM calls)
- Branching and feedback loops MUST be explicitly defined in the graph structure
- Agent collaboration MUST be graph-controlled, not chatty

**Rationale**: Free-flowing agent conversations create unpredictable, unobservable systems. Deterministic orchestration ensures debuggability, cost control, and reliability.

### III. Security-First Execution

**Non-Negotiable Requirements**:
- ALL LLM-generated code MUST execute in isolated sandbox (E2B or Docker)
- Sandbox MUST enforce: no outbound internet, CPU/RAM limits, read-only mounts, timeout enforcement, kill switch
- Secrets MUST be stored in Kubernetes Secrets or Vault (NEVER ConfigMaps)
- Rate limits MUST be enforced to prevent infinite loops and runaway costs
- Prompt caching MUST be implemented to reduce latency and cost

**Rationale**: Generated code cannot be trusted. Isolation prevents system compromise, resource exhaustion, and cost overruns.

### IV. Observability & Transparency

**Mandatory Requirements**:
- ALL agent executions MUST be traceable via LangSmith
- Decision provenance MUST be tracked: who decided, based on what context, confidence scores
- Structured JSON logs with searchable request IDs MUST be produced
- Distributed tracing (Jaeger) MUST cover orchestrator, sidecars, and tool calls
- Metrics MUST be exposed: token burn, cost per run, model efficiency, error frequency

**Rationale**: You MUST see how your AI thinks. Without transparency, AI systems are black boxes that cannot be trusted or debugged in production.

### V. Incremental Delivery

**Mandatory Phases** (in order):
1. **Phase 1 — Core Brain Online**: LangGraph Orchestrator, Spec→Design→Code flow, Redis+Postgres, FastAPI endpoints
2. **Phase 2 — Real Developer Mode**: Review Agent, Test Agent, Vector DB memory, Observability MVP
3. **Phase 3 — Professionalism Mode**: CI/CD automation, Secure sandbox, Full tracing+dashboards, Go Mesh sidecar
4. **Phase 4 — Power Tools**: CLI Tool, AI IDE Mode, Local+Cloud hybrid execution

**Rationale**: Building incrementally prevents architectural overreach and ensures each phase delivers value. Each phase is independently testable and deployable.

## Architecture Standards

### Technology Stack

**Intelligence Layer**:
- Orchestrator: LangGraph (Python)
- LLM: OpenAI GPT-4 / Claude (configurable)
- Workflow Definitions: Structured LangGraph graphs

**Infrastructure Layer**:
- API Gateway: FastAPI (Python)
- Service Mesh: Go (sidecars for telemetry, rate limiting, token metering)
- Sandbox: E2B or Docker isolated runner

**Memory Layer**:
- Session State: Redis (fast, session-scoped)
- Persistent State: PostgreSQL (structured state)
- Vector Store: Chroma / FAISS / Milvus (three channels: Agent Cognitive Memory, RAG Knowledge Base, Code Semantic Search)

**Observability Layer**:
- Tracing: LangSmith (LLM traces), Jaeger (distributed tracing)
- Metrics: Prometheus + Grafana dashboards
- Logs: Structured JSON logs

### Module Structure

```
/core
    orchestrator/
    workflow_definitions/
    state_manager/

/agents
    spec/
    design/
    implement/
    review/
    test/
    deploy/

/infra
    fastapi_gateway/
    go_sidecars/
    sandbox/

/memory
    redis/
    postgres/
    vectorstore/

/observability
    exporters/
    dashboards/
    tracing/
```

**Rationale**: Clear separation enables parallel development, testing, and independent scaling of components.

## Development Workflow

### Agent Specialization

Each agent MUST have a single, well-defined responsibility:

| Agent            | Responsibility                           |
| ---------------- | ---------------------------------------- |
| Spec Agent       | Vague request → structured spec          |
| Design Agent     | Architecture & module planning           |
| Implementation   | Code generation                          |
| Review Agent     | Code quality + static analysis           |
| Test Agent       | Test generation + execution              |
| Deployment Agent | CI/CD + packaging                        |

**Rationale**: Specialized agents are more reliable, testable, and maintainable than generic "do everything" agents.

### Production Pitfalls to Avoid

**PROHIBITED**:
- Calling LLM for obvious routing decisions
- Trusting generated code without sandbox isolation
- Running code outside sandbox
- Skipping prompt caching
- Leaving agents generic without clear responsibility

**REQUIRED**:
- Specialize agents with clear contracts
- Continue reasoning in structured chains
- Maintain transparency at all times
- Embed budget governance
- Cache deterministic operations

**Rationale**: These practices prevent common failures in AI engineering systems.

## Governance

### Amendment Process

1. Proposals MUST document: change rationale, impact on existing principles, migration plan
2. Amendments require explicit approval (maintained in git history)
3. Constitution supersedes all other development practices
4. All PRs MUST verify compliance with current constitution

### Versioning Policy

- **MAJOR**: Backward incompatible governance/principle removals or redefinitions
- **MINOR**: New principle/section added or materially expanded guidance
- **PATCH**: Clarifications, wording, typo fixes, non-semantic refinements

### Compliance Review

- Phase completion MUST include constitution compliance check
- Complexity violations MUST be justified in plan.md "Complexity Tracking" section
- Use `.specify/templates/plan-template.md` for runtime development guidance

### Template Synchronization

When constitution is amended:
1. `.specify/templates/plan-template.md` - Update "Constitution Check" section
2. `.specify/templates/spec-template.md` - Update scope/requirements if constraints change
3. `.specify/templates/tasks-template.md` - Update task categorization if new principles added
4. `.claude/commands/*.md` - Verify no outdated references remain

**Version**: 1.0.0 | **Ratified**: 2026-01-11 | **Last Amended**: 2026-01-11
