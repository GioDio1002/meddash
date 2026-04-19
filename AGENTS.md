# MedDash Agent Guidance

## Working Rules

- Keep the system clinician-assistive only.
- Prefer typed structured outputs over freeform text.
- Do not implement autonomous diagnosis flows without explicit human-review branches.
- Keep changes small, reviewable, and test-backed.
- Add observability and tests with feature work instead of deferring them.
- Prefer deletion and simplification over adding new abstraction layers.

## Required Quality Gates

- Frontend: lint, typecheck, build
- Backend: lint, tests
- Full stack: Playwright E2E for core consultation paths
- Observability: logs, traces, and workflow correlation must be verifiable

## Architecture Defaults

- Frontend: Bun + Vite + React + TypeScript + Ant Design
- Backend: Python 3.12.11 + FastAPI + LangGraph
- E2E: Playwright
- Observability: OpenTelemetry
- Prompt Ops: Agenta remains optional and disabled by default

## Safety Defaults

- Urgent or unsafe cases must route to clinician handoff.
- Medication safety checks are blocking, not advisory-only, when a direct conflict is found.
- Audit events are required for clinician override and workflow handoff.
