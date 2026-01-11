# Data Model: The Hive - Multi-Agent Engineering System

**Feature**: [spec.md](./spec.md)
**Date**: 2026-01-11
**Phase**: Phase 1 - Design & Contracts

## Overview

This document defines the data model for The Hive Multi-Agent Engineering System, including entity definitions, relationships, validation rules, and state transitions. The model supports workflow orchestration, artifact management, decision provenance, and observability requirements.

---

## Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  ProjectContext │ 1───* │ DecisionRecord  │ *───1 │ WorkflowSession │
│                 │       │                 │       │                 │
└─────────────────┘       └─────────────────┘       └────────┬────────┘
                                                                  │
                                           ┌──────────────────────┼──────────────────┐
                                           │                      │                  │
                                   ┌───────▼────────┐   ┌───────▼────────┐  ┌────▼────────┐
                                   │ Artifact       │   │ AgentState     │  │ Sandbox      │
                                   │ (polymorphic)  │   │                │  │ Session      │
                                   └───────┬────────┘   └────────────────┘  └─────────────┘
                                           │
              ┌────────────┬───────────────┼──────────────┬─────────────┐
              │            │               │              │             │
        ┌─────▼─────┐ ┌───▼────┐  ┌──────▼──────┐ ┌────▼─────┐ ┌────▼─────┐
        │ Spec      │ │ Design │  │ Code        │ │ Review   │  │ Test      │
        │ Document  │ │ Doc    │  │ Artifact    │ │ Report   │  │ Suite     │
        └───────────┘ └────────┘  └─────────────┘ └──────────┘  └──────────┘
```

---

## Core Entities

### 1. WorkflowSession

Represents a complete end-to-end workflow execution from initial request to final deployment.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique workflow identifier |
| `project_context_id` | UUID | FOREIGN KEY → ProjectContext | Associated project context |
| `status` | Enum | NOT NULL | Current workflow status (see state transitions) |
| `input_request` | JSONB | NOT NULL | Original user feature request |
| `created_at` | Timestamptz | DEFAULT NOW() | Workflow creation timestamp |
| `updated_at` | Timestamptz | DEFAULT NOW() | Last update timestamp |
| `started_at` | Timestamptz | NULLABLE | Workflow start timestamp |
| `completed_at` | Timestamptz | NULLABLE | Workflow completion timestamp |
| `current_stage` | Enum | NULLABLE | Current workflow stage |
| `artifacts_summary` | JSONB | NULLABLE | Summary of generated artifacts |
| `performance_metrics` | JSONB | NULLABLE | Performance metrics (duration, tokens, cost) |
| `error_message` | Text | NULLABLE | Error details if failed |

**Status Values**:
- `PENDING` - Workflow queued, not yet started
- `RUNNING` - Workflow currently executing
- `PAUSED` - Workflow paused (awaiting user input)
- `COMPLETED` - Workflow completed successfully
- `FAILED` - Workflow failed with error
- `CANCELLED` - Workflow cancelled by user

**State Transitions**:
```
PENDING → RUNNING → PAUSED → RUNNING
    ↓         ↓
CANCELLED   COMPLETED
    ↓         ↓
  FAILED    (end)
```

**Validation Rules**:
- `id` must be a valid UUID v4
- `status` must be one of the defined enum values
- `completed_at` must be ≥ `started_at` if both set
- `performance_metrics` includes: `duration_seconds`, `total_tokens`, `cost_usd`

**Indexes**:
```sql
CREATE INDEX idx_workflow_sessions_status ON workflow_sessions(status);
CREATE INDEX idx_workflow_sessions_created ON workflow_sessions(created_at DESC);
CREATE INDEX idx_workflow_sessions_project ON workflow_sessions(project_context_id);
```

---

### 2. ProjectContext

Accumulated knowledge about a project across multiple workflow sessions.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique project context identifier |
| `project_name` | Varchar(255) | NOT NULL, UNIQUE | Human-readable project name |
| `project_metadata` | JSONB | NULLABLE | Project metadata (language, frameworks, etc.) |
| `created_at` | Timestamptz | DEFAULT NOW() | Context creation timestamp |
| `updated_at` | Timestamptz | DEFAULT NOW() | Last update timestamp |
| `codebase_index_id` | Varchar(255) | NULLABLE | Reference to vector store code index |
| `knowledge_base_id` | Varchar(255) | NULLABLE | Reference to vector store knowledge base |

**Validation Rules**:
- `project_name` must be unique across all projects
- `project_metadata` max size: 10MB

---

### 3. DecisionRecord

Record of a decision made by an agent during workflow execution.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique decision identifier |
| `workflow_id` | UUID | FOREIGN KEY → WorkflowSession, NOT NULL | Associated workflow |
| `agent_type` | Varchar(50) | NOT NULL | Agent that made the decision |
| `timestamp` | Timestamptz | DEFAULT NOW() | Decision timestamp |
| `decision_type` | Varchar(100) | NOT NULL | Type of decision (e.g., "architecture_choice", "error_handling") |
| `input_context` | JSONB | NOT NULL | Context input to the decision |
| `output_decision` | JSONB | NOT NULL | Decision output |
| `confidence` | Float | NULLABLE, 0.0-1.0 | Confidence score (if available) |
| `rationale` | Text | NULLABLE | Textual explanation of the decision |
| `dependencies` | JSONB | NULLABLE | Array of dependent decision IDs |
| `vector_embedding_id` | Varchar(255) | NULLABLE | Reference to vector store embedding |

**Agent Types**:
- `SPEC_AGENT` - Specification generation
- `DESIGN_AGENT` - Architecture design
- `IMPLEMENTATION_AGENT` - Code generation
- `REVIEW_AGENT` - Code review
- `TEST_AGENT` - Test generation
- `DEPLOYMENT_AGENT` - Deployment

**Validation Rules**:
- `confidence` must be between 0.0 and 1.0 if provided
- `dependencies` must reference valid DecisionRecord IDs
- `input_context` and `output_decision` max size: 5MB each

**Indexes**:
```sql
CREATE INDEX idx_decision_records_workflow ON decision_records(workflow_id);
CREATE INDEX idx_decision_records_agent ON decision_records(agent_type);
CREATE INDEX idx_decision_records_timestamp ON decision_records(timestamp DESC);
```

---

## Artifact Entities (Polymorphic)

Artifacts are generated by agents during workflow execution. All artifacts share a base structure with type-specific extensions.

### 4. Artifact (Base Table)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique artifact identifier |
| `workflow_id` | UUID | FOREIGN KEY → WorkflowSession, NOT NULL | Associated workflow |
| `artifact_type` | Enum | NOT NULL | Type of artifact (spec, design, code, review, test) |
| `stage` | Varchar(50) | NOT NULL | Workflow stage that generated this artifact |
| `content` | JSONB | NOT NULL | Artifact content (structure varies by type) |
| `file_path` | Varchar(500) | NULLABLE | File path for file-based artifacts |
| `created_at` | Timestamptz | DEFAULT NOW() | Artifact creation timestamp |
| `approval_status` | Enum | DEFAULT 'PENDING' | Approval status (PENDING, APPROVED, REJECTED) |
| `version` | Integer | DEFAULT 1 | Artifact version (for iterative refinement) |

**Artifact Types**:
- `SPECIFICATION` - Feature specification document
- `DESIGN` - Architecture design document
- `CODE` - Generated source code
- `REVIEW` - Code review report
- `TEST_SUITE` - Test cases and results

### 4a. SpecDocument (Specification Artifact)

| Field | Type | Description |
|-------|------|-------------|
| `user_stories` | JSONB | Array of user stories with priorities |
| `functional_requirements` | JSONB | Functional requirements list |
| `success_criteria` | JSONB | Success criteria metrics |
| `edge_cases` | JSONB | Edge cases identified |
| `assumptions` | JSONB | Assumptions made |

**Content Structure**:
```json
{
  "user_stories": [
    {
      "title": "Core Workflow Orchestration",
      "priority": "P1",
      "description": "...",
      "acceptance_criteria": ["..."]
    }
  ],
  "functional_requirements": [
    {"id": "FR-001", "description": "..."}
  ],
  "success_criteria": [
    {"id": "SC-001", "metric": "...", "target": "..."}
  ]
}
```

### 4b. DesignDocument (Design Artifact)

| Field | Type | Description |
|-------|------|-------------|
| `architecture` | JSONB | Architecture decisions and patterns |
| `modules` | JSONB | Module breakdown with dependencies |
| `data_model` | JSONB | Data structures and relationships |
| `api_contracts` | JSONB | API endpoint definitions |
| `technology_choices` | JSONB | Technology decisions with rationale |

### 4c. CodeArtifact (Code Artifact)

| Field | Type | Description |
|-------|------|-------------|
| `language` | Varchar(50) | Programming language |
| `file_path` | Varchar(500) | File path within project |
| `content` | Text | Source code content |
| `dependencies` | JSONB | Required dependencies/packages |
| `review_status` | Enum | Review status (PENDING, APPROVED, REJECTED)

### 4d. ReviewReport (Review Artifact)

| Field | Type | Description |
|-------|------|-------------|
| `issues_found` | JSONB | Array of issues with severity |
| `security_issues` | JSONB | Security vulnerabilities found |
| `code_smells` | JSONB | Code quality issues |
| `recommendations` | JSONB | Improvement suggestions |
| `overall_score` | Integer | Overall quality score (0-100) |

**Issue Structure**:
```json
{
  "issues_found": [
    {
      "severity": "HIGH",
      "type": "security",
      "file_path": "src/auth.py",
      "line": 42,
      "description": "SQL injection vulnerability",
      "recommendation": "Use parameterized queries"
    }
  ]
}
```

### 4e. TestSuite (Test Artifact)

| Field | Type | Description |
|-------|------|-------------|
| `test_framework` | Varchar(50) | Testing framework used |
| `test_cases` | JSONB | Array of test cases |
| `coverage_metrics` | JSONB | Code coverage data |
| `execution_results` | JSONB | Test execution results |

**Test Case Structure**:
```json
{
  "test_cases": [
    {
      "id": "TC-001",
      "name": "test_user_authentication",
      "given": "user with valid credentials",
      "when": "login endpoint called",
      "then": "returns 200 with auth token",
      "status": "PASS"
    }
  ]
}
```

---

## Runtime Entities

### 5. AgentState

Current state of an agent in the workflow.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique agent state identifier |
| `workflow_id` | UUID | FOREIGN KEY → WorkflowSession, NOT NULL | Associated workflow |
| `agent_type` | Varchar(50) | NOT NULL | Type of agent |
| `current_task` | Varchar(255) | NULLABLE | Current task being executed |
| `status` | Enum | NOT NULL | Agent status (IDLE, ACTIVE, ERROR, COMPLETED) |
| `cpu_usage_percent` | Float | NULLABLE | Current CPU usage |
| `memory_usage_bytes` | BigInt | NULLABLE | Current memory usage |
| `tokens_consumed` | Integer | DEFAULT 0 | Total tokens consumed |
| `last_heartbeat` | Timestamptz | DEFAULT NOW() | Last activity timestamp |

**Agent Status Values**:
- `IDLE` - Agent not currently processing
- `ACTIVE` - Agent actively processing a task
- `ERROR` - Agent encountered an error
- `COMPLETED` - Agent finished its tasks

**Indexes**:
```sql
CREATE INDEX idx_agent_states_workflow ON agent_states(workflow_id);
CREATE INDEX idx_agent_states_status ON agent_states(status);
```

---

### 6. SandboxSession

Isolated execution environment for generated code.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique sandbox session identifier |
| `workflow_id` | UUID | FOREIGN KEY → WorkflowSession, NOT NULL | Associated workflow |
| `agent_id` | UUID | FOREIGN KEY → AgentState, NULLABLE | Associated agent |
| `container_id` | Varchar(255) | NULLABLE | Container/sandbox ID |
| `image_name` | Varchar(255) | NOT NULL | Base image used |
| `status` | Enum | NOT NULL | Sandbox status (CREATING, RUNNING, COMPLETED, TERMINATED, FAILED) |
| `resource_limits` | JSONB | NOT NULL | Resource limits (CPU, memory, timeout) |
| `resource_usage` | JSONB | NULLABLE | Actual resource usage |
| `created_at` | Timestamptz | DEFAULT NOW() | Session creation timestamp |
| `started_at` | Timestamptz | NULLABLE | Execution start timestamp |
| `completed_at` | Timestamptz | NULLABLE | Execution completion timestamp |
| `stdout` | Text | NULLABLE | Standard output |
| `stderr` | Text | NULLABLE | Standard error |
| `exit_code` | Integer | NULLABLE | Process exit code |

**Resource Limits Structure**:
```json
{
  "cpu_limit": 0.5,
  "memory_limit": "512m",
  "timeout_seconds": 300,
  "network_enabled": false
}
```

**Resource Usage Structure**:
```json
{
  "cpu_used": 0.3,
  "memory_used": "256m",
  "duration_seconds": 45
}
```

**Indexes**:
```sql
CREATE INDEX idx_sandbox_sessions_workflow ON sandbox_sessions(workflow_id);
CREATE INDEX idx_sandbox_sessions_status ON sandbox_sessions(status);
```

---

## Vector Store Entities

The following entities are stored in the vector database (Chroma/Milvus) for semantic search and retrieval.

### 7. AgentCognitiveMemory (Vector Store)

Agent decisions and rationale for future reference.

| Field | Type | Description |
|-------|------|-------------|
| `id` | Varchar(255) | Unique identifier |
| `embedding` | Float[1536] | Vector embedding (OpenAI ada-002) |
| `decision_id` | UUID | Reference to DecisionRecord |
| `project_context_id` | UUID | Reference to ProjectContext |
| `agent_type` | Varchar(50) | Agent that made the decision |
| `decision_type` | Varchar(100) | Type of decision |
| `summary` | Text | Decision summary for embedding |
| `full_context` | JSONB | Full decision context |
| `timestamp` | Timestamptz | Decision timestamp |
| `metadata` | JSONB | Additional metadata for filtering |

**Metadata Structure**:
```json
{
  "project_id": "uuid",
  "agent_type": "IMPLEMENTATION_AGENT",
  "decision_type": "architecture_choice",
  "outcome": "success",
  "timestamp": "2026-01-11T10:00:00Z"
}
```

### 8. KnowledgeBase (Vector Store)

Engineering best practices, patterns, and documentation.

| Field | Type | Description |
|-------|------|-------------|
| `id` | Varchar(255) | Unique identifier |
| `embedding` | Float[1536] | Vector embedding |
| `title` | Varchar(255) | Knowledge title |
| `category` | Varchar(100) | Category (pattern, practice, anti-pattern) |
| `content` | Text | Knowledge content |
| `source` | Varchar(500) | Source reference |
| `tags` | JSONB | Tags for filtering |
| `created_at` | Timestamptz | Creation timestamp |

### 9. CodeSemanticIndex (Vector Store)

Code for impact analysis and refactor support.

| Field | Type | Description |
|-------|------|-------------|
| `id` | Varchar(255) | Unique identifier |
| `embedding` | Float[1536] | Vector embedding |
| `file_path` | Varchar(500) | File path |
| `language` | Varchar(50) | Programming language |
| `function_name` | Varchar(255) | Function/class name |
| `code_snippet` | Text | Code snippet for embedding |
| `ast_context` | JSONB | AST-derived context |
| `project_context_id` | UUID | Reference to ProjectContext |
| `dependencies` | JSONB | Dependencies on other code units |

---

## Redis Data Structures

Session-scoped data stored in Redis for fast access during active workflow execution.

### 10. WorkflowState (Redis Hash)

Active workflow state for LangGraph checkpointing.

| Field | Type | TTL | Description |
|-------|------|-----|-------------|
| `workflow_id:{id}` | Hash | 24h | Current workflow state |
| `workflow:{id}:stage` | String | 24h | Current stage |
| `workflow:{id}:artifacts` | List | 24h | Artifact references |
| `workflow:{id}:decisions` | List | 24h | Decision references |

**Example**:
```
HSET workflow:abc-123 current_stage "implementation" status "RUNNING"
LPUSH workflow:abc-123:artifacts "spec-uuid" "design-uuid"
EXPIRE workflow:abc-123 86400
```

### 11. AgentCache (Redis)

Cached agent responses for prompt caching.

| Field | Type | TTL | Description |
|-------|------|-----|-------------|
| `agent:{agent_type}:prompt:{hash}` | String | 7d | Cached agent response |
| `prompt_embeddings:{hash}` | String | 30d | Prompt embedding for similarity search |

---

## State Machine Diagrams

### Workflow Lifecycle

```
┌─────────┐
│ PENDING │
└────┬────┘
     │ start()
     ↓
┌─────────┐    pause()    ┌─────────┐
│ RUNNING │──────────────→│ PAUSED  │
└────┬────┘               └────┬────┘
     │ resume()                │
     └────────────────────────┘
     │
     ├─→ COMPLETED (all stages finished)
     ├─→ FAILED (error encountered)
     └─→ CANCELLED (user cancelled)
```

### Sandbox Lifecycle

```
┌──────────┐
│ CREATING │
└────┬─────┘
     │ container started
     ↓
┌─────────┐
│ RUNNING │
└────┬────┘
     │
     ├─→ COMPLETED (finished normally)
     ├─→ TERMINATED (timeout/kill switch)
     └─→ FAILED (error/crash)
```

---

## Data Validation Rules

### Cross-Field Validation

1. **WorkflowSession**:
   - `started_at` must be set before `current_stage`
   - `completed_at` must be set if status is COMPLETED, FAILED, or CANCELLED
   - `error_message` must be set if status is FAILED

2. **DecisionRecord**:
   - `confidence` required if `agent_type` is IMPLEMENTATION_AGENT or DESIGN_AGENT
   - `dependencies` must reference decisions from earlier stages only

3. **Artifact**:
   - `version` increments on regeneration
   - `approval_status` transitions: PENDING → APPROVED or PENDING → REJECTED

4. **SandboxSession**:
   - `resource_usage.cpu_used` ≤ `resource_limits.cpu_limit`
   - `resource_usage.duration_seconds` ≤ `resource_limits.timeout_seconds`

---

## Migration Strategy

### Phase 1 (MVP)
- Create core tables: WorkflowSession, DecisionRecord, Artifact (base)
- Implement SpecDocument, DesignDocument, CodeArtifact
- Set up Redis for session state
- Chroma for vector stores

### Phase 2
- Add ReviewReport, TestSuite artifact types
- Extend DecisionRecord with vector embedding references
- Implement AgentState tracking

### Phase 3
- Add SandboxSession with full resource tracking
- Migrate Chroma to Milvus for scale
- Implement ProjectContext with full codebase indexing

---

## Performance Considerations

### Indexing Strategy
- Index on frequently queried fields: status, timestamps, workflow_id
- Composite indexes for common query patterns
- Partial indexes for active workflows (status = 'RUNNING')

### Partitioning (Future)
- Partition WorkflowSession by month on `created_at`
- Partition DecisionRecord by workflow_id range for large deployments

### Caching Strategy
- Redis cache for active workflow state (24h TTL)
- Prompt response cache (7d TTL)
- Vector embedding cache (30d TTL)

### Cleanup Policies
- Archive completed workflows after 30 days to cold storage
- Delete decision records for cancelled workflows after 7 days
- Cleanup sandbox sessions after 24 hours
