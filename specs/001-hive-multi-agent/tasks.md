# Tasks: The Hive - Multi-Agent Engineering System

**Input**: Design documents from `/specs/001-hive-multi-agent/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are included for production readiness following constitution quality requirements

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Multi-service distributed system with layered architecture per constitution:
- `/core` - Orchestrator and state management
- `/agents` - Specialized agent implementations
- `/infra` - FastAPI gateway, Go sidecars, sandbox
- `/memory` - Redis, PostgreSQL, VectorStore
- `/observability` - Exporters, dashboards, tracing
- `/cli` - Command-line interface (Phase 4)
- `/tests` - Contract, integration, and unit tests

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create directory structure per constitution: /core, /agents, /infra, /memory, /observability, /cli, /tests, /docs
- [X] T002 Initialize Python project with pyproject.toml and dependencies (langgraph, langchain, fastapi, uvicorn, pydantic, redis, psycopg2-binary, chromadb, prometheus-client, opentelemetry, pytest)
- [X] T003 Initialize Go module for service mesh with go.mod (grpc-go, prometheus/client_golang)
- [X] T004 [P] Create docker-compose.yml for local development (PostgreSQL, Redis, Chroma)
- [X] T005 [P] Create .env.example with all required environment variables
- [X] T006 [P] Create Dockerfile for production container image
- [X] T007 [P] Configure Python development tools (black, ruff, mypy, pytest)
- [X] T008 [P] Create requirements.txt from pyproject.toml dependencies

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Memory Layer Setup

- [X] T009 Create WorkflowSession SQLAlchemy model in memory/postgres/models.py
- [X] T010 Create DecisionRecord SQLAlchemy model in memory/postgres/models.py
- [X] T011 Create Artifact SQLAlchemy model (base table) in memory/postgres/models.py
- [X] T012 Create AgentState SQLAlchemy model in memory/postgres/models.py
- [X] T013 Create SandboxSession SQLAlchemy model in memory/postgres/models.py
- [X] T014 Create ProjectContext SQLAlchemy model in memory/postgres/models.py
- [X] T015 Create database indexes for workflow_sessions table in memory/postgres/models.py
- [X] T016 Create database indexes for decision_records table in memory/postgres/models.py
- [X] T017 [P] Implement PostgreSQL client wrapper in memory/postgres/client.py
- [X] T018 [P] Implement Redis client wrapper in memory/redis/client.py
- [X] T019 [P] Implement Chroma vector store wrapper in memory/vectorstore/chroma_store.py
- [X] T020 Create database migration scripts in memory/postgres/migrations/

### Core Orchestrator Foundation

- [X] T021 Create WorkflowState Pydantic model in core/orchestrator/state.py
- [X] T022 Implement LangGraph StateGraph wrapper in core/orchestrator/graph.py
- [X] T023 Define workflow stage enums in core/workflow_definitions/stages.py
- [X] T024 Implement base workflow template in core/workflow_definitions/base_workflow.py
- [X] T025 Create deterministic routing logic in core/orchestrator/router.py

### Observability Foundation

- [X] T026 Implement LangSmith trace exporter in observability/exporters/langsmith.py
- [X] T027 [P] Implement Prometheus metrics exporter in observability/exporters/prometheus.py
- [X] T028 [P] Implement structured JSON logging with request IDs in observability/exporters/jaeger.py
- [X] T029 [P] Create decision tracker for provenance in observability/tracing/decision_tracker.py

### Configuration & Error Handling

- [X] T030 Implement environment configuration loader in core/config.py
- [X] T031 Create global error handlers and exception classes in core/exceptions.py
- [X] T032 [P] Setup health check endpoint structure in infra/fastapi_gateway/routes/health.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Workflow Orchestration (Priority: P1) 🎯 MVP

**Goal**: Deliver foundational MVP capability - spec → design → implementation workflow through deterministic LangGraph orchestration

**Independent Test**: Submit a feature request and verify: (1) structured specification produced, (2) workflow progresses through stages, (3) intermediate outputs inspectable

### Implementation for User Story 1

#### Base Agent Interface

- [X] T033 [P] [US1] Create base Agent abstract class in agents/base.py
- [X] T034 [P] [US1] Implement LLM provider factory in core/llm/providers.py
- [X] T035 [P] [US1] Implement prompt cache manager in core/llm/cache.py

#### Spec Agent

- [X] T036 [P] [US1] Create SpecAgent implementation in agents/spec/spec_agent.py
- [X] T037 [US1] Implement spec generation logic with LangGraph node in agents/spec/spec_agent.py
- [X] T038 [US1] Add SpecAgent to workflow graph in core/orchestrator/graph.py

#### Design Agent

- [X] T039 [P] [US1] Create DesignAgent implementation in agents/design/design_agent.py
- [X] T040 [US1] Implement architecture design logic with LangGraph node in agents/design/design_agent.py
- [X] T041 [US1] Add DesignAgent to workflow graph with conditional edge in core/orchestrator/graph.py

#### Implementation Agent

- [X] T042 [P] [US1] Create ImplementationAgent in agents/implement/implementation_agent.py
- [X] T043 [US1] Implement code generation logic with LangGraph node in agents/implement/implementation_agent.py
- [X] T044 [US1] Add ImplementationAgent to workflow graph in core/orchestrator/graph.py

#### Workflow State Management

- [X] T045 [US1] Implement Redis session store for active workflows in core/state_manager/session_store.py
- [X] T046 [US1] Implement PostgreSQL persistent store for completed workflows in core/state_manager/persistent_store.py
- [X] T047 [US1] Create workflow checkpointing with LangGraph in core/orchestrator/checkpoint.py

#### FastAPI Gateway - Workflow Endpoints

- [X] T048 [P] [US1] Create Pydantic schemas for API in infra/fastapi_gateway/models/schemas.py
- [X] T049 [US1] Implement workflow submission endpoint in infra/fastapi_gateway/routes/workflows.py
- [X] T050 [US1] Implement workflow status endpoint in infra/fastapi_gateway/routes/status.py
- [X] T051 [US1] Implement workflow cancellation endpoint in infra/fastapi_gateway/routes/workflows.py
- [X] T052 [US1] Create FastAPI application and register routes in infra/fastapi_gateway/app.py

**Checkpoint**: Core workflow orchestration complete - MVP delivers spec → design → code flow

---

## Phase 4: User Story 3 - Secure Code Execution (Priority: P1) 🔒

**Goal**: Execute all AI-generated code in isolated Docker sandbox with resource limits and network blocking

**Independent Test**: Trigger code execution and verify: (1) isolated environment, (2) resource limits enforced, (3) network blocked, (4) can be terminated

### Implementation for User Story 3

#### Docker Sandbox Runner

- [X] T053 [P] [US3] Create Docker sandbox runner wrapper in infra/sandbox/docker_runner.py
- [X] T054 [US3] Implement container resource limits (CPU, memory, timeout) in infra/sandbox/docker_runner.py
- [X] T055 [US3] Implement network isolation (network_mode="none") in infra/sandbox/docker_runner.py
- [X] T056 [US3] Implement read-only filesystem with tmpfs in infra/sandbox/docker_runner.py
- [X] T057 [US3] Implement kill switch for immediate termination in infra/sandbox/docker_runner.py
- [X] T058 [US3] Add security hardening (no-new-privileges, cap_drop) in infra/sandbox/docker_runner.py

#### Sandbox Lifecycle Management

- [X] T059 [US3] Implement sandbox manager in infra/sandbox/manager.py
- [X] T060 [US3] Create sandbox session state tracking in infra/sandbox/manager.py
- [X] T061 [US3] Implement stdout/stderr capture from sandbox in infra/sandbox/manager.py
- [X] T062 [US3] Add sandbox health checks and timeout enforcement in infra/sandbox/manager.py

#### Integration with Implementation Agent

- [X] T063 [US3] Modify ImplementationAgent to use sandbox for code execution in agents/implement/implementation_agent.py
- [X] T064 [US3] Store sandbox session records in PostgreSQL via SandboxSession model
- [X] T065 [US3] Add sandbox status endpoint in infra/fastapi_gateway/routes/status.py

**Checkpoint**: Secure code execution complete - all generated code runs in isolated sandbox

---

## Phase 5: User Story 2 - Workflow Observability and Transparency (Priority: P2)

**Goal**: Provide complete visibility into agent decisions, execution graph, performance metrics, and error context

**Independent Test**: Run workflow and verify: (1) all decisions logged, (2) decision context available, (3) execution graph visible, (4) metrics displayed

### Implementation for User Story 2

#### Decision Provenance Tracking

- [ ] T066 [P] [US2] Create decision recording decorator in observability/tracing/decision_tracker.py
- [ ] T067 [US2] Implement decision context capture (input, output, confidence) in observability/tracing/decision_tracker.py
- [ ] T068 [US2] Store decision records in PostgreSQL DecisionRecord table in observability/tracing/decision_tracker.py
- [ ] T069 [US2] Add vector embedding for semantic search of decisions in observability/tracing/decision_tracker.py

#### Agent Telemetry

- [ ] T070 [P] [US2] Create agent state tracker in observability/telemetry/agent_tracker.py
- [ ] T071 [US2] Track agent resource usage (CPU, memory, tokens) in observability/telemetry/agent_tracker.py
- [ ] T072 [US2] Store agent state in PostgreSQL AgentState table in observability/telemetry/agent_tracker.py
- [ ] T073 [US2] Implement agent heartbeat mechanism in observability/telemetry/agent_tracker.py

#### Execution Graph Visualization

- [ ] T074 [P] [US2] Implement LangGraph execution graph exporter in observability/tracing/graph_exporter.py
- [ ] T075 [US2] Create decision retrieval endpoint in infra/fastapi_gateway/routes/artifacts.py
- [ ] T076 [US2] Implement progress calculation in core/orchestrator/state.py

#### Performance Metrics

- [ ] T077 [US2] Define Prometheus metrics (token usage, cost, duration) in observability/exporters/prometheus.py
- [ ] T078 [US2] Collect workflow performance metrics in core/orchestrator/graph.py
- [ ] T079 [US2] Implement cost estimation per provider in core/llm/providers.py

#### Error Tracing

- [ ] T080 [US2] Implement detailed error context capture in core/exceptions.py
- [ ] T081 [US2] Add error traceback to workflow state in core/orchestrator/state.py
- [ ] T082 [US2] Create error details retrieval endpoint in infra/fastapi_gateway/routes/status.py

**Checkpoint**: Full observability complete - all agent decisions traceable with context

---

## Phase 6: User Story 4 - Memory and Context Persistence (Priority: P2)

**Goal**: Retain context across sessions with project memory, decision history, and semantic search

**Independent Test**: Run multiple related workflows and verify: (1) past decisions accessible, (2) project context maintained, (3) artifacts referenceable, (4) memory clearable

### Implementation for User Story 4

#### Project Context Management

- [ ] T083 [P] [US4] Implement ProjectContext creation and retrieval in memory/postgres/client.py
- [ ] T084 [US4] Create project metadata storage in memory/postgres/models.py
- [ ] T085 [US4] Add project association to workflow submission in infra/fastapi_gateway/routes/workflows.py

#### Vector Memory Channels

- [ ] T086 [P] [US4] Implement agent cognitive memory collection in memory/vectorstore/cognitive_memory.py
- [ ] T087 [US4] Implement RAG knowledge base collection in memory/vectorstore/knowledge_base.py
- [ ] T088 [US4] Implement code semantic index in memory/vectorstore/code_index.py
- [ ] T089 [US4] Create semantic search interface in memory/vectorstore/chroma_store.py

#### Decision History Retrieval

- [ ] T090 [US4] Implement decision similarity search in memory/vectorstore/cognitive_memory.py
- [ ] T091 [US4] Add context injection to agent calls in agents/base.py
- [ ] T092 [US4] Create decision history query endpoint in infra/fastapi_gateway/routes/artifacts.py

#### Artifact Persistence

- [ ] T093 [P] [US4] Implement artifact versioning in memory/postgres/models.py
- [ ] T094 [US4] Store all artifact types in PostgreSQL Artifact table
- [ ] T095 [US4] Create artifact retrieval endpoint in infra/fastapi_gateway/routes/artifacts.py

#### Memory Management

- [ ] T096 [US4] Implement selective memory clearing API in infra/fastapi_gateway/routes/workflows.py
- [ ] T097 [US4] Add project timeline query endpoint in infra/fastapi_gateway/routes/artifacts.py

**Checkpoint**: Memory persistence complete - context retained across sessions

---

## Phase 7: User Story 5 - Code Review and Quality Assurance (Priority: P2)

**Goal**: Automated code review and testing for AI-generated code with issue detection and quality gates

**Independent Test**: Generate code and verify: (1) review identifies issues, (2) tests generated/executed, (3) results reported, (4) issues flaggable

### Implementation for User Story 5

#### Review Agent

- [ ] T098 [P] [US5] Create ReviewAgent implementation in agents/review/review_agent.py
- [ ] T099 [US5] Implement static analysis integration (ruff, mypy) in agents/review/review_agent.py
- [ ] T100 [US5] Implement security vulnerability detection in agents/review/review_agent.py
- [ ] T101 [US5] Implement code smell detection in agents/review/review_agent.py
- [ ] T102 [US5] Create ReviewReport artifact model in memory/postgres/models.py
- [ ] T103 [US5] Add ReviewAgent to workflow graph in core/orchestrator/graph.py

#### Test Agent

- [ ] T104 [P] [US5] Create TestAgent implementation in agents/test/test_agent.py
- [ ] T105 [US5] Implement test generation logic in agents/test/test_agent.py
- [ ] T106 [US5] Implement test execution in isolated environment in agents/test/test_agent.py
- [ ] T107 [US5] Create TestSuite artifact model in memory/postgres/models.py
- [ ] T108 [US5] Add TestAgent to workflow graph in core/orchestrator/graph.py

#### Quality Gates

- [ ] T109 [US5] Implement quality score calculation in agents/review/review_agent.py
- [ ] T110 [US5] Add approval workflow for artifacts in infra/fastapi_gateway/routes/workflows.py
- [ ] T111 [US5] Implement auto-fix suggestions in agents/review/review_agent.py

**Checkpoint**: Code review and QA complete - generated code quality validated

---

## Phase 8: User Story 6 - CLI Interface for Developer Integration (Priority: P3)

**Goal**: Command-line interface for workflow submission, status queries, and artifact retrieval

**Independent Test**: Install CLI and verify: (1) workflows runnable, (2) status queryable, (3) results retrievable in multiple formats, (4) help available

### Implementation for User Story 6

#### CLI Framework

- [ ] T112 [P] [US6] Install Click and Rich dependencies in pyproject.toml
- [ ] T113 [US6] Create CLI entry point in cli/main.py
- [ ] T114 [US6] Implement base CLI structure with command groups in cli/main.py

#### Workflow Commands

- [ ] T115 [US6] Implement "run" command in cli/commands/run.py
- [ ] T116 [US6] Implement "status" command in cli/commands/status.py
- [ ] T117 [US6] Implement "artifacts" command in cli/commands/artifacts.py
- [ ] T118 [US6] Add progress bars for long-running workflows in cli/commands/run.py

#### Output Formatting

- [ ] T119 [US6] Implement table output formatting in cli/commands/status.py
- [ ] T120 [US6] Implement JSON output option in cli/main.py
- [ ] T121 [US6] Add colored output and formatting in cli/commands/run.py

#### Configuration

- [ ] T122 [US6] Implement .env file support in cli/main.py
- [ ] T123 [US6] Create CLI configuration file support in cli/main.py

**Checkpoint**: CLI interface complete - developers can integrate system into workflows

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

### Documentation

- [ ] T124 [P] Create architecture overview in docs/architecture.md
- [ ] T125 [P] Create agent documentation in docs/agents.md
- [ ] T126 [P] Create API documentation in docs/api.md
- [ ] T127 Update README.md with quickstart instructions

### Testing

- [ ] T128 [P] Create contract test for workflow API in tests/contract/test_workflow_api.py
- [ ] T129 [P] Create contract test for sandbox in tests/contract/test_sandbox.py
- [ ] T130 [P] Create integration test for full workflow in tests/integration/test_full_workflow.py
- [ ] T131 [P] Create integration test for agent collaboration in tests/integration/test_agent_collab.py
- [ ] T132 [P] Create unit tests for SpecAgent in tests/unit/test_agents/test_spec_agent.py
- [ ] T133 [P] Create unit tests for orchestrator in tests/unit/test_orchestrator/test_graph.py
- [ ] T134 [P] Create unit tests for state management in tests/unit/test_orchestrator/test_state.py
- [ ] T135 [P] Create unit tests for memory layer in tests/unit/test_memory/test_postgres_client.py
- [ ] T136 [P] Create unit tests for vector store in tests/unit/test_memory/test_chroma_store.py

### Security Hardening

- [ ] T137 Add secrets management via environment variables in core/config.py
- [ ] T138 Implement rate limiting middleware in infra/fastapi_gateway/middleware/rate_limit.py
- [ ] T139 Add input validation for all API endpoints in infra/fastapi_gateway/models/schemas.py
- [ ] T140 Add authentication middleware (optional) in infra/fastapi_gateway/middleware/auth.py

### Performance Optimization

- [ ] T141 Implement connection pooling for PostgreSQL in memory/postgres/client.py
- [ ] T142 Implement connection pooling for Redis in memory/redis/client.py
- [ ] T143 Add prompt caching for LLM calls in core/llm/cache.py
- [ ] T144 Optimize vector search queries in memory/vectorstore/chroma_store.py

### Deployment

- [ ] T145 [P] Create production Dockerfile with multi-stage build
- [ ] T146 [P] Create Kubernetes deployment manifests
- [ ] T147 [P] Setup CI/CD pipeline in .github/workflows/
- [ ] T148 [P] Create Grafana dashboard JSON configs in observability/dashboards/grafana/

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - User stories can proceed in parallel (if staffed)
  - Or sequentially in priority order: US1 (P1) → US3 (P1) → US2 (P2) → US4 (P2) → US5 (P2) → US6 (P3)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 3 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Enhances US1 but not required
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Benefits all stories
- **User Story 5 (P2)**: Requires US1 (needs code to review)
- **User Story 6 (P3)**: Can start after US1 (needs working workflow)

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational [P] tasks can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 and US3 can start in parallel
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all foundational database models together:
Task: "Create WorkflowSession SQLAlchemy model in memory/postgres/models.py"
Task: "Create DecisionRecord SQLAlchemy model in memory/postgres/models.py"
Task: "Create Artifact SQLAlchemy model in memory/postgres/models.py"
Task: "Create AgentState SQLAlchemy model in memory/postgres/models.py"

# Launch all agent implementations in parallel:
Task: "Create SpecAgent implementation in agents/spec/spec_agent.py"
Task: "Create DesignAgent implementation in agents/design/design_agent.py"
Task: "Create ImplementationAgent in agents/implement/implementation_agent.py"

# Launch all memory layer clients in parallel:
Task: "Implement PostgreSQL client wrapper in memory/postgres/client.py"
Task: "Implement Redis client wrapper in memory/redis/client.py"
Task: "Implement Chroma vector store wrapper in memory/vectorstore/chroma_store.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 3 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Core Workflow Orchestration)
4. Complete Phase 4: User Story 3 (Secure Code Execution)
5. **STOP and VALIDATE**: Test core workflow with sandbox security
6. Deploy/demo if ready

**MVP delivers**: Spec → Design → Implementation workflow with secure sandbox execution

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US1 (Core Orchestration) → Test independently → Deploy/Demo (MVP core!)
3. Add US3 (Secure Execution) → Test independently → Deploy/Demo (MVP complete!)
4. Add US2 (Observability) → Test independently → Deploy/Demo
5. Add US4 (Memory) → Test independently → Deploy/Demo
6. Add US5 (Review & QA) → Test independently → Deploy/Demo
7. Add US6 (CLI) → Test independently → Deploy/Demo
8. Add Polish → Final production release

Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Core Orchestration)
   - Developer B: User Story 3 (Secure Execution) - can run parallel to US1
   - Developer C: User Story 2 (Observability) - can run parallel to US1/US3
3. Stories complete and integrate independently

---

## Task Summary

| Phase | Tasks | Focus |
|-------|-------|-------|
| Phase 1: Setup | 8 tasks | Project initialization |
| Phase 2: Foundational | 24 tasks | Core infrastructure (BLOCKS user stories) |
| Phase 3: US1 - Core Orchestration | 20 tasks | Spec → Design → Code workflow |
| Phase 4: US3 - Secure Execution | 13 tasks | Docker sandbox with resource limits |
| Phase 5: US2 - Observability | 17 tasks | Decision provenance & metrics |
| Phase 6: US4 - Memory | 15 tasks | Context persistence & semantic search |
| Phase 7: US5 - Review & QA | 14 tasks | Automated code review & testing |
| Phase 8: US6 - CLI | 12 tasks | Command-line interface |
| Phase 9: Polish | 25 tasks | Tests, docs, security, deployment |
| **Total** | **148 tasks** | Complete production system |

### Parallel Opportunities

- **57 tasks** marked [P] can run in parallel within their phases
- **3 major parallel tracks** after foundational: US1, US3, US2 can start simultaneously
- **Unit test suites** can all be developed in parallel

### MVP Scope (Recommended)

- **Phase 1 + 2**: 32 tasks (Setup + Foundational)
- **Phase 3 (US1)**: 20 tasks (Core Orchestration)
- **Phase 4 (US3)**: 13 tasks (Secure Execution)
- **Total MVP**: **65 tasks** - delivers fully functional workflow with sandbox security

### Independent Test Criteria

Each user story can be independently validated:

- **US1**: Submit feature request → receive spec, design, code artifacts
- **US3**: Execute code → verify isolated sandbox, resource limits, network blocked
- **US2**: Run workflow → view all decisions, context, metrics
- **US4**: Run two workflows → second workflow references first
- **US5**: Generate code → receive review report and test results
- **US6**: Run CLI commands → submit workflow, query status, get artifacts

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Foundational phase (Phase 2) must complete before any user story work
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Tests are included for production readiness per constitution requirements
