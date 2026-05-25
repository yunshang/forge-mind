# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ForgeMind is an AI Agent-based smart contract collaborative development platform. Users describe contracts in natural language, and an agent system generates Solidity code, audits it, visualizes the contract topology, and deploys to a local Anvil sandbox.

## Commands

### Backend (Python / Litestar)

```bash
# Install dependencies
uv sync

# Run backend locally
uv run uvicorn backend.main:app --reload

# Run all tests
uv run pytest tests/ -v

# Run a single test file
uv run pytest tests/test_security_audit.py -v

# Run a single test
uv run pytest tests/test_orchestrator.py::TestOrchestrator::test_healing_loop_fixes_vulnerabilities -v

# Lint
uv run ruff check backend/
```

### Frontend (Next.js)

```bash
cd frontend

npm run dev      # Dev server on :3000
npm run build    # Production build
npm run lint     # ESLint
npx tsc --noEmit # Type check only
```

### Docker (Anvil sandbox)

```bash
docker compose up -d          # Start Anvil
docker compose up -d --build backend  # Rebuild + start backend
docker compose down            # Stop all
```

### Full local stack (no Docker for backend)

```bash
# Terminal 1: Anvil
docker compose up anvil

# Terminal 2: Backend
uv run uvicorn backend.main:app --reload

# Terminal 3: Frontend
cd frontend && npm run dev
```

## Environment

Required env vars (set in `.env`, copied from `.env.example`):

- `FORGE_ANTHROPIC_API_KEY` — API key for LLM provider
- `FORGE_ANTHROPIC_BASE_URL` — LLM API endpoint (Anthropic-compatible)
- `FORGE_ANTHROPIC_MODEL` — Model name
- `FORGE_ANVIL_URL` — Anvil RPC URL (default: `http://localhost:8545`)

Config is loaded via pydantic-settings with `env_prefix="FORGE_"`. The `.env` file path is resolved relative to the project root (`backend/config.py`).

## Architecture

### Backend: Skill-based Agent System

The core abstraction is **BaseSkill** (`backend/skills/base.py`) — an async `execute(**kwargs) -> dict` interface. Four skills implement it:

1. **SolidityGenerationSkill** — Calls LLM (Anthropic-compatible API) with a strict JSON prompt. Has retry logic (8 attempts, exponential backoff) for rate limits. Parser has 3 fallback layers for malformed JSON responses.
2. **SecurityAuditSkill** — Regex-based static analysis. No external dependencies. Checks reentrancy, selfdestruct, tx.origin, floating pragma, unchecked arithmetic, missing events, missing access control.
3. **AstVisualSkill** — Regex parser that extracts functions, state variables, inheritance, modifiers from Solidity code. Outputs React Flow graph JSON (`{nodes, edges}`).
4. **SandboxSimulationSkill** — Compiles via `solc --combined-json`, deploys to Anvil via Web3.py. Returns ABI, contract address, and callable function list.

**Agents** wrap skills:
- **CoderAgent** — wraps SolidityGenerationSkill
- **ReviewerAgent** — wraps SecurityAuditSkill, formats feedback for re-prompting

**Orchestrator** (`backend/agents/orchestrator.py`) runs the self-healing loop:
```
Coder → Reviewer → if FAIL: feed audit back to Coder (max 3 iterations) → then AST Visual + Sandbox Deploy
```

### Backend: Session Management

**SessionStore** (`backend/store.py`) is a thread-safe in-memory dict keyed by session ID. Each **Session** (`backend/models/session.py`) accumulates conversation history. When generating within a session, the orchestrator receives the last 6 messages as context so the LLM can iterate on prior work.

### Backend: Routes (Litestar)

- `POST /api/contracts/generate` — stateless one-shot generation
- `POST /api/sessions` / `GET` / `GET /{id}` / `DELETE /{id}` — session CRUD
- `POST /api/sessions/{id}/generate` — generate within session context
- `POST /api/sandbox/call` — execute function on deployed contract

### Frontend: Three-panel Dashboard

- **Left panel** — ChatPanel (session selector + chat input) + TerminalLog (agent state stream)
- **Center panel** — Tabbed: CodeViewer (syntax-highlighted Solidity) / FlowCanvas (React Flow topology graph)
- **Right panel** — SandboxPlayground (ABI-driven dynamic form inputs for contract interaction)

State management is in `useAgent` hook — manages session lifecycle, generation calls, and result state. No external state library.

### Key Patterns

- LLM calls use `default_headers={"api-key": ...}` because MiMo API uses `api-key` header instead of Anthropic's `x-api-key`.
- Security audit is pure regex — no AST parser dependency. If adding new checks, follow the existing pattern in `security_audit.py`.
- Frontend uses `@xyflow/react` (v12+) for the graph canvas, not the older `reactflow` package directly.
- All async tests use `asyncio_mode = "auto"` via pytest-asyncio — no need for `@pytest.mark.asyncio` decorators.
