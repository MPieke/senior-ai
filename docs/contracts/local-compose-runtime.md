---
title: One-command local Docker runtime
linear_issue: MPI-18
linear_issue_url: https://linear.app/mpieke/issue/MPI-18/build-senior-ai-assistant-mvp
status: draft_for_review
---

# One-command local Docker runtime contract

## Purpose

Make the MVP easy to run locally and repeatable in deployment-like
environments. Docker Compose remains the runtime definition; a Makefile gives
short, discoverable commands for starting, stopping, testing, and inspecting
the application. OpenAI credentials remain in an ignored local `.env` file.

## 1. Current-state architecture

```text
Developer
  |
  | remembers individual Docker Compose commands
  v
docker-compose.yml
  |                         |
  v                         v
api container            web container
FastAPI :8000            Vite preview :4173
  |                         |
  | SQLite + uploads         | browser calls localhost:8000
  v                         v
named Docker volume      Senior AI browser UI

OPENAI_API_KEY is read from the shell environment if present.
```

The compose file already builds both containers and persists the API data, but
there is no documented one-command interface, health-gated startup, example
environment file, or consistent test command.

```text
Sequence — current local start

Developer -> Docker Compose: manually run up/build command
Docker Compose -> API: start API container
Docker Compose -> Web: start independently of API readiness
Developer -> Browser: open a port they must know
Browser -> API: call localhost:8000
```

## 2. Target-state architecture

```text
Developer
  |
  | make up / make down / make test / make logs
  v
Makefile (command interface)
  |
  v
docker compose (canonical runtime definition)
  |                         |
  v                         v
api container [healthy]   web container [healthy]
FastAPI :8000             Vite preview :4173
  |                         |
  | SQLite + retained files  | browser calls localhost:8000
  v                         v
named Docker volume       Senior AI browser UI

.env (ignored) ----> OPENAI_API_KEY / OPENAI_MODEL
.env.example ----> documented safe variable names only
```

```text
Sequence — target local start and smoke check

Developer -> Makefile: make up
Makefile -> Docker Compose: up --build --detach
Docker Compose -> API: build and start
API -> API: /health succeeds
Docker Compose -> Web: start after API is healthy
Developer -> Browser: http://localhost:4173
Browser -> API: submit analysis through localhost:8000

Developer -> Makefile: make smoke
Makefile -> Docker Compose: verify API health and web HTTP response
```

No application database schema changes are introduced. The existing named
volume remains the only persistence boundary.

## 3. Commit-by-commit breakdown

1. **Add runtime contract**
   - Files: `docs/contracts/local-compose-runtime.md`
   - Adds this implementation contract and cross-links MPI-18.
   - Reviewable independently because it makes the intended operational
     interface and verification criteria explicit without changing runtime
     behavior.

2. **Add runtime command tests**
   - Files: `scripts/test-runtime.sh`, `Makefile`
   - Add a shell-level verification harness and initial `make` test targets.
     It will assert that the expected targets exist and that the smoke command
     fails clearly before health checks are implemented.
   - Reviewable independently because it records the CLI contract before
     Compose behavior is changed.

3. **Implement Compose health checks and Makefile interface**
   - Files: `docker-compose.yml`, `Makefile`, `.env.example`,
     `scripts/test-runtime.sh`, `README.md`
   - Add API and web health checks, make web wait for API health, add `up`,
     `down`, `logs`, `status`, `smoke`, `test`, and `help` targets, document
     exact startup and API-key setup, and expose only non-secret environment
     variable names in `.env.example`.
   - Reviewable independently because it is the complete runtime behavior that
     satisfies the already-defined CLI assertions.

4. **Run the CI-facing test suite**
   - Files: CI configuration only if a repository CI workflow already exists
     or must be added after inspection.
   - Ensure the existing backend and frontend test discovery runs through
     `make test`; add the runtime harness to the same command. If CI does not
     exist, add a minimal GitHub Actions workflow that runs `make test`.
   - Reviewable independently because it turns the local verification surface
     into a repeatable repository check.

## 4. Verification plan

Run these commands from repository root, recording actual results:

```sh
make help
make test
make up
make smoke
docker compose ps
curl --fail http://localhost:8000/health
curl --fail http://localhost:4173/
make down
```

Manual Playwright verification after `make up`:

1. Open `http://localhost:4173`.
2. Choose **Paste a message**, paste the committed scam fixture, and continue.
3. Confirm a result screen renders with the red risk state and no browser/API
   network errors.
4. Open **Upload a document**, choose `backend/tests/fixtures/notice.pdf`,
   verify the review screen shows the filename, then submit it.

Security checks:

```sh
git check-ignore .env
test ! -e .env.example || ! rg --fixed-strings 'sk-' .env.example
```

The OpenAI request itself is not invoked by this smoke flow when no API key is
configured: the API deliberately uses its deterministic fixture provider.
