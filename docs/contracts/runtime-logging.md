---
title: Safe runtime logging for local testing
linear_issue: MPI-18
linear_issue_url: https://linear.app/mpieke/issue/MPI-18/build-senior-ai-assistant-mvp
status: draft_for_review
---

# Safe runtime logging for local testing contract

## Purpose

Make it easy to observe local testing flows without exposing message text,
uploaded document bytes, filenames, API keys, or other sensitive content.
`make logs` remains the all-service tail command, with focused API and web log
commands added for faster diagnosis.

## 1. Current-state architecture

```text
Browser -> FastAPI -> provider -> SQLite
                 |
                 v
       standard library exception logger
                 |
                 v
          Docker Compose logs

Developer -> make logs -> docker compose logs --follow
```

Successful analysis creation, result safety normalization, and action attempts
produce no consistent visible event. Exception logs do not provide a uniform
event format for local flow testing.

## 2. Target-state architecture

```text
Browser -> FastAPI -> provider -> SQLite
                 |
                 v
          Loguru event logger
          |- analysis.received: input metadata only
          |- analysis.completed: analysis ID, risk, action types
          |- analysis.failed: safe failure category
          `- action.attempted: analysis ID, requested type, confirmation state
                 |
                 v
           Docker stdout/stderr
                 |
                 v
docker compose logs --follow
  ^             ^             ^
  |             |             |
make logs   make logs-api  make logs-web
```

Log events exclude document text, filenames, extracted facts, raw provider
responses, upload bytes, and environment values. IDs, enum states, media type,
and byte count are sufficient to understand the flow safely.

```text
Sequence — observable document analysis

User -> API: upload PDF
API -> Loguru: analysis.received (media_type, byte_count)
API -> Provider: analyze
Provider -> API: validated structured result
API -> Loguru: analysis.completed (analysis_id, risk_level, action_types)
API -> User: result JSON
Developer -> make logs-api: sees the two events, never document contents
```

No database schema changes are introduced.

## 3. Commit-by-commit breakdown

1. **Add logging contract**
   - Files: `docs/contracts/runtime-logging.md`
   - Adds the design and MPI-18 cross-reference.
   - Reviewable independently because it defines the sensitive-data boundary.

2. **Add failing safe-event tests**
   - Files: `backend/tests/test_api.py`
   - Assert completed analysis logs contain safe identifiers/state and do not
     contain submitted message content; assert an action attempt is logged.
   - Reviewable independently because it defines observable logging behavior
     before changing implementation.

3. **Implement Loguru events and focused Make targets**
   - Files: `backend/pyproject.toml`, `backend/app/main.py`, `Makefile`,
     `README.md`
   - Add Loguru, replace the application logger, emit safe lifecycle events,
     and add `make logs-api` / `make logs-web` while preserving `make logs`.
   - Reviewable independently because it delivers the complete local
     observability surface.

4. **Run CI-facing and manual verification**
   - Files: no production-file changes expected.
   - Run `make test`, rebuild with `make up`, submit the family fixture, use
     `make logs-api`, and run `make test-e2e`.
   - Reviewable independently because it demonstrates events from the real
     container boundary.

## 4. Verification plan

```sh
make test
make up
make smoke
curl --fail --form 'file=@backend/tests/fixtures/family-emergency-scam.pdf;type=application/pdf' http://localhost:8000/v1/analyses
docker compose logs --no-color api
make test-e2e
```

Manual log review must show `analysis.received` and `analysis.completed` with
safe metadata, and must not contain any line from the submitted document or
the `OPENAI_API_KEY` value. `make logs-api` must tail only the API service and
`make logs` must continue to tail both services.
