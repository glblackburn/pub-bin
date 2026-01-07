# Better Creds Management - Project Plan

## Project Overview

**Project Name:** Better Creds Management  
**Goal:** Build a production-ready application for managing credential rotation workflows, starting from the existing trufflehog scripts foundation.

**Core Value Proposition:**
- Centralized credential rotation management
- Tracking database for audit trails and state management
- Dual interface: CLI for automation, Web UI for human interaction
- Extensible architecture supporting multiple credential types and sources

---

## Current State Assessment

### Existing Assets (from trufflehog folder)

#### Core Scripts
1. **trufflehog-rotate-aws-key.py** (~2300 lines)
   - AWS key rotation with paired secret support
   - Pluggable credential loaders (file-based implemented, Keeper planned)
   - Git operations (clone, branch, commit, push, PR creation)
   - State management via JSON files
   - Resume functionality
   - Early repository validation

2. **trufflehog-analyze-results.py**
   - Parses trufflehog scan results
   - Generates markdown reports
   - Tokenized/raw mode support

3. **trufflehog-tokenize-secrets.py** / **trufflehog-detokenize-secrets.py**
   - Secret tokenization for safe processing
   - Reversible lookup tables

4. **Supporting Scripts**
   - `trufflehog-local-git-repos.sh` - Repository scanning
   - `create-trufflehog-aws-credentials.sh` - Credential file management
   - `audit-sensitive-data.py` - Data auditing

#### Existing Features
- ✅ AWS key rotation (single and paired secrets)
- ✅ Pluggable credential loaders (Phase 1: file-based)
- ✅ Git workflow automation (branch, commit, push, PR)
- ✅ State persistence (JSON files)
- ✅ Resume capability
- ✅ Repository validation
- ✅ Tokenization for safe processing

#### Limitations to Address
- ❌ No persistent database (JSON files only)
- ❌ No web interface
- ❌ Limited credential type support (AWS only)
- ❌ No centralized tracking across runs
- ❌ No user management or access control
- ❌ No audit logging beyond state files
- ❌ No scheduling/automation framework
- ❌ Limited error recovery and retry logic

---

## Architecture Vision

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Better Creds Management                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐         ┌──────────────┐                │
│  │   CLI Tool   │◄────────┤  Core Engine │                │
│  │  (Python)    │         │  (Python)    │                │
│  └──────────────┘         └──────┬───────┘                │
│                                   │                         │
│  ┌──────────────┐                │                         │
│  │   Web App    │◄───────────────┘                         │
│  │  (FastAPI +  │                                              │
│  │   React/Vue) │                                              │
│  └──────────────┘                                              │
│                                   │                         │
│  ┌──────────────┐         ┌──────▼───────┐                │
│  │   Database   │◄────────┤  API Layer    │                │
│  │  (PostgreSQL │         │  (FastAPI)    │                │
│  │   / SQLite)  │         └───────────────┘                │
│  └──────────────┘                                           │
│                                   │                         │
│  ┌──────────────┐         ┌──────▼───────┐                │
│  │  Credential  │◄────────┤  Plugins      │                │
│  │   Loaders    │         │  System       │                │
│  │  (File,      │         │               │                │
│  │   Keeper,    │         │               │                │
│  │   Vault)     │         │               │                │
│  └──────────────┘         └───────────────┘                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. Core Engine (Python)
- **Purpose:** Business logic for credential rotation workflows
- **Responsibilities:**
  - Workflow orchestration
  - Git operations
  - Credential management
  - State management
  - Plugin system

#### 2. Database Layer
- **Purpose:** Persistent storage for tracking, audit, and state
- **Schema Areas:**
  - Rotations (jobs, runs, status)
  - Repositories (metadata, access)
  - Credentials (metadata only, not actual secrets)
  - Audit logs (all actions)
  - Users/Teams (access control)
  - Schedules (automation)

#### 3. API Layer (FastAPI)
- **Purpose:** RESTful API for web app and external integrations
- **Endpoints:**
  - `/api/v1/rotations` - Rotation management
  - `/api/v1/repositories` - Repository operations
  - `/api/v1/credentials` - Credential metadata
  - `/api/v1/audit` - Audit logs
  - `/api/v1/schedules` - Automation schedules

#### 4. CLI Tool
- **Purpose:** Command-line interface for automation and scripting
- **Commands:**
  - `better-creds rotate` - Start rotation
  - `better-creds status` - Check status
  - `better-creds resume` - Resume rotation
  - `better-creds list` - List rotations/repos
  - `better-creds audit` - View audit logs

#### 5. Web Application
- **Purpose:** Human-friendly interface for management
- **Features:**
  - Dashboard (overview, recent activity)
  - Rotation management (create, view, resume)
  - Repository browser
  - Audit log viewer
  - Settings (credentials, schedules)
  - User management (if multi-user)

#### 6. Plugin System
- **Purpose:** Extensible credential loaders and integrations
- **Types:**
  - Credential loaders (File, Keeper, Vault, AWS Secrets Manager)
  - Notification plugins (Slack, Email, PagerDuty)
  - Integration plugins (GitHub, GitLab, Bitbucket)

---

## Database Schema Design

### Core Tables

#### `rotations`
```sql
CREATE TABLE rotations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    identifier VARCHAR(255) NOT NULL,  -- e.g., RAW_abc123_def456
    secret_type VARCHAR(50) NOT NULL,  -- aws, github, etc.
    status VARCHAR(50) NOT NULL,       -- pending, in_progress, completed, failed
    mode VARCHAR(50) NOT NULL,         -- dry-run, commit
    paired_secret_mode BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_by VARCHAR(255),           -- user/script identifier
    metadata JSONB                     -- flexible storage
);
```

#### `rotation_runs`
```sql
CREATE TABLE rotation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rotation_id UUID REFERENCES rotations(id),
    run_number INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    summary JSONB,                    -- stats: total, completed, failed, skipped
    state_file_path TEXT,             -- path to state JSON (if still used)
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### `repositories`
```sql
CREATE TABLE repositories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization VARCHAR(255) NOT NULL,
    repository_name VARCHAR(255) NOT NULL,
    repository_url TEXT NOT NULL,
    validated BOOLEAN DEFAULT FALSE,
    last_validated_at TIMESTAMP,
    last_rotated_at TIMESTAMP,
    rotation_count INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(organization, repository_name)
);
```

#### `repository_rotations`
```sql
CREATE TABLE repository_rotations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rotation_run_id UUID REFERENCES rotation_runs(id),
    repository_id UUID REFERENCES repositories(id),
    status VARCHAR(50) NOT NULL,       -- pending, in_progress, completed, failed, skipped
    branch_name VARCHAR(255),
    changes_committed BOOLEAN DEFAULT FALSE,
    pushed BOOLEAN DEFAULT FALSE,
    pr_created BOOLEAN DEFAULT FALSE,
    pr_url TEXT,
    pr_number INTEGER,
    files_modified TEXT[],            -- array of file paths
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### `audit_logs`
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rotation_id UUID REFERENCES rotations(id),
    rotation_run_id UUID REFERENCES rotation_runs(id),
    repository_rotation_id UUID REFERENCES repository_rotations(id),
    action VARCHAR(100) NOT NULL,     -- rotation_started, file_modified, pr_created, etc.
    actor VARCHAR(255),               -- user/script identifier
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### `credential_loaders`
```sql
CREATE TABLE credential_loaders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    type VARCHAR(50) NOT NULL,        -- file, keeper, vault, etc.
    config JSONB NOT NULL,            -- loader-specific configuration
    enabled BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,      -- load order
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `schedules`
```sql
CREATE TABLE schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    identifier VARCHAR(255) NOT NULL,
    cron_expression VARCHAR(100) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## Feature Roadmap

### Phase 1: Foundation (Weeks 1-4)
**Goal:** Migrate core functionality to database-backed system

- [ ] Database setup (PostgreSQL or SQLite for dev)
- [ ] Core engine refactoring (extract from trufflehog-rotate-aws-key.py)
- [ ] Database models and migrations (SQLAlchemy/Alembic)
- [ ] Basic CLI tool (`better-creds` command)
- [ ] State migration from JSON to database
- [ ] Basic API endpoints (FastAPI)
- [ ] Simple web UI (dashboard, rotation list)

**Deliverables:**
- Working CLI that uses database
- Basic web interface showing rotations
- Database-backed state management

### Phase 2: Enhanced Features (Weeks 5-8)
**Goal:** Add web UI and improved workflows

- [ ] Complete web UI (React/Vue frontend)
- [ ] Rotation creation via web UI
- [ ] Real-time status updates (WebSockets or polling)
- [ ] Audit log viewer
- [ ] Repository browser
- [ ] Enhanced error handling and retry logic
- [ ] Notification system (email, Slack)

**Deliverables:**
- Full-featured web application
- Real-time status tracking
- Comprehensive audit logging

### Phase 3: Advanced Features (Weeks 9-12)
**Goal:** Automation and extensibility

- [ ] Scheduling system (cron-based automation)
- [ ] Plugin system for credential loaders
- [ ] Keeper vault integration
- [ ] Multi-credential type support (GitHub tokens, API keys, etc.)
- [ ] User management and access control
- [ ] Team/organization support
- [ ] Advanced reporting and analytics

**Deliverables:**
- Automated rotation scheduling
- Extensible plugin architecture
- Multi-tenant support

### Phase 4: Production Readiness (Weeks 13-16)
**Goal:** Hardening and optimization

- [ ] Performance optimization
- [ ] Security audit and hardening
- [ ] Comprehensive testing (unit, integration, e2e)
- [ ] Documentation (user guides, API docs)
- [ ] Deployment guides (Docker, Kubernetes)
- [ ] Monitoring and alerting
- [ ] Backup and recovery procedures

**Deliverables:**
- Production-ready application
- Complete documentation
- Deployment automation

---

## Technology Stack

### Backend
- **Language:** Python 3.11+
- **Framework:** FastAPI (API) + Core engine (standalone)
- **Database:** PostgreSQL (production), SQLite (development)
- **ORM:** SQLAlchemy
- **Migrations:** Alembic
- **Task Queue:** Celery (for async operations) or asyncio
- **Authentication:** JWT tokens (if multi-user)

### Frontend
- **Framework:** React or Vue.js
- **UI Library:** Material-UI, Ant Design, or Tailwind CSS
- **State Management:** Redux/Zustand (React) or Pinia (Vue)
- **Real-time:** WebSockets or Server-Sent Events

### Infrastructure
- **Containerization:** Docker
- **Orchestration:** Docker Compose (dev), Kubernetes (prod)
- **CI/CD:** GitHub Actions
- **Monitoring:** Prometheus + Grafana (or simpler solution)

### Development Tools
- **Testing:** pytest, pytest-asyncio
- **Linting:** ruff, mypy
- **Formatting:** black
- **Documentation:** Sphinx or MkDocs

---

## Migration Strategy

### Step 1: Extract Core Logic
- Refactor `trufflehog-rotate-aws-key.py` into modular components:
  - `core/workflow.py` - Workflow orchestration
  - `core/git_operations.py` - Git operations
  - `core/credential_management.py` - Credential handling
  - `core/repository_validation.py` - Validation logic
  - `plugins/credential_loaders/` - Plugin system

### Step 2: Add Database Layer
- Create database models
- Implement database operations alongside JSON file operations
- Dual-write mode (write to both DB and JSON during transition)

### Step 3: Build API Layer
- Create FastAPI application
- Implement endpoints that use database
- Maintain CLI compatibility

### Step 4: Build Web UI
- Create frontend application
- Connect to API
- Implement core workflows

### Step 5: Migrate State
- Script to migrate existing JSON state files to database
- Validate migration
- Deprecate JSON file usage

---

## Project Structure

```
better-creds-management/
├── backend/
│   ├── app/
│   │   ├── core/              # Core business logic
│   │   │   ├── workflow.py
│   │   │   ├── git_operations.py
│   │   │   ├── credential_management.py
│   │   │   └── repository_validation.py
│   │   ├── api/               # FastAPI application
│   │   │   ├── routes/
│   │   │   ├── models/
│   │   │   └── dependencies.py
│   │   ├── db/                # Database layer
│   │   │   ├── models.py
│   │   │   ├── session.py
│   │   │   └── migrations/
│   │   ├── plugins/           # Plugin system
│   │   │   └── credential_loaders/
│   │   └── utils/
│   ├── cli/                   # CLI tool
│   │   └── better_creds.py
│   ├── tests/
│   └── alembic.ini
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── store/
│   └── package.json
├── docs/
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
├── scripts/
│   └── migrate_state.py       # Migration from JSON to DB
├── .github/
│   └── workflows/
├── README.md
└── pyproject.toml
```

---

## Key Design Decisions

### 1. Database vs JSON Files
- **Decision:** Use database as primary storage, JSON files as optional backup/export
- **Rationale:** Better querying, relationships, audit trails, scalability

### 2. Monorepo vs Separate Repos
- **Decision:** Monorepo (backend, frontend, CLI together)
- **Rationale:** Easier development, shared types, unified versioning

### 3. API-First Design
- **Decision:** Build API first, CLI and Web UI consume API
- **Rationale:** Consistent behavior, easier testing, future integrations

### 4. Plugin Architecture
- **Decision:** Extensible plugin system for credential loaders
- **Rationale:** Support multiple credential sources without core changes

### 5. State Management
- **Decision:** Database for persistent state, in-memory for active operations
- **Rationale:** Resume capability, audit trails, better error recovery

---

## Success Metrics

### Technical Metrics
- Rotation success rate > 95%
- API response time < 200ms (p95)
- Database query performance < 50ms (p95)
- Test coverage > 80%

### User Experience Metrics
- Time to create rotation < 2 minutes
- Web UI load time < 3 seconds
- CLI command execution < 5 seconds (for status checks)

### Business Metrics
- Number of rotations managed
- Average time to complete rotation
- Error rate and recovery time
- User adoption rate

---

## Risks and Mitigations

### Risk 1: Database Migration Complexity
- **Mitigation:** Dual-write period, comprehensive testing, rollback plan

### Risk 2: Breaking Changes to Existing Workflows
- **Mitigation:** Maintain CLI compatibility, gradual migration, clear documentation

### Risk 3: Performance Issues with Large Scale
- **Mitigation:** Database indexing, query optimization, caching strategy

### Risk 4: Security Concerns
- **Mitigation:** Security audit, credential encryption, access controls, regular updates

---

## Next Steps

1. **Review and Refine Plan** - Get feedback on architecture and approach
2. **Set Up Repository** - Create new repository structure
3. **Database Design** - Finalize schema, create migration scripts
4. **Extract Core Logic** - Begin refactoring from trufflehog scripts
5. **Build MVP** - Get basic CLI + database working first

---

## Questions to Resolve

1. **Database Choice:** PostgreSQL (production-ready) vs SQLite (simpler dev)?
2. **Frontend Framework:** React vs Vue.js?
3. **Deployment Target:** Self-hosted, cloud, or both?
4. **Multi-user from Start:** Single-user MVP first, or multi-user from beginning?
5. **Credential Storage:** How to handle actual secrets? (Never in DB, only metadata)
6. **License:** Open source, proprietary, or hybrid?

---

**Document Status:** Draft - Planning Phase  
**Last Updated:** 2026-01-06  
**Next Review:** After stakeholder feedback
