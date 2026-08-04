---
title: Senior AI Assistant MVP
linear_issue: MPI-18
linear_issue_url: https://linear.app/mpieke/issue/MPI-18/build-senior-ai-assistant-mvp
status: draft_for_review
---

# Senior AI Assistant MVP contract

## Purpose and agreed boundaries

Build a deployable, local-first MVP for helping older adults understand an
everyday message, letter, image, or document. The product is a calm document
assistant, not a chatbot. The first complete flow is a pasted scam SMS.

The normal experience and demo samples make real multimodal LLM calls. A
controlled provider is used only for fast, deterministic unit and browser
tests. The UI never decides risk or invents actions: it renders the validated,
post-processed backend result.

The visual direction is the supplied **Warm Paper** handoff: cream surface,
serif display headings, warm charcoal text, terracotta/sage accents, generous
spacing, large targets, and only Home and History in bottom navigation.

Original content is collapsed by default and is shown only after an explicit
user action. Stubbed actions must never imply that an external action occurred.

## 1. Current-state architecture

The repository is a new, empty Git repository. There is no application, API,
database, deployment configuration, test suite, or CI workflow.

```text
C4 container view — current

[Senior user]
      |
      | no deployed product
      v
[Empty repository]
```

## 2. Target-state architecture

SQLite is the initial persistence adapter. Application services depend on a
repository interface, not SQLite, allowing a future PostgreSQL or hosted
database adapter without changing API, analysis, action, or UI logic.

```text
C4 container view — target

[Senior user]
      |
      | mobile/tablet browser
      v
[React web application]
      |
      | HTTPS JSON + multipart upload
      v
[Python API]
      |---------------------------> [Multimodal LLM API]
      |
      |---------------------------> [Persistence repository]
                                      |
                                      v
                                  [SQLite initially]
```

```text
C4 component view — Python API

[Analysis routes]
  |- input size/type validation
  |- create/get/list analyses
  `- confirmed action endpoint
          |
          v
[Analysis service]
  |- normalize text, image, and document input
  |- construct a versioned product instruction
  |- call the LLM-provider interface
  `- parse a structured model response
          |
          v
[Validation and safety policy]
  |- validate response schema and response length
  |- remove invalid, duplicate, and unsafe actions
  |- cap and order actions at three
  |- downgrade unsafe confidence/risk combinations
  `- return a single frontend-ready result
          |
          v
[Analysis/action repository interface]
  `- SQLite adapter (MVP)
```

```text
Sequence — pasted scam SMS

User        Web app          API              LLM           Repository
 |             |              |                |                |
 | paste SMS   |              |                |                |
 |-----------> | create input |                |                |
 |             |------------> | normalize      |                |
 |             |              |--------------> |                |
 |             |              | structured     |                |
 |             |              |<-------------- |                |
 |             |              | validate + apply safety policy   |
 |             |              |-------------------------------> |
 |             | validated result                 save result    |
 |             |<------------ |                                 |
 | result      |              |                                 |
 |<----------- |              |                                 |
 | show original on explicit request                             |
 |-----------> |                                                     
```

```text
ER view — persistence boundary

Analysis 1 -------- * ActionAttempt
  |                    |
  |- id                |- id
  |- source_kind       |- analysis_id
  |- original_ref      |- action_type
  |- result_json       |- parameters_json
  |- model_version     |- confirmation_status
  |- prompt_version    |- execution_status
  |- audit_metadata    `- created_at
  `- created_at
```

## 3. Target behavior

The initial demo/evaluation scenarios are:

1. A scam text message: red risk, “Stop and verify before responding,” no
   suspicious-sender engagement action, and up to three safe actions.
2. An insurance letter: green or mild yellow state depending on response
   timing, with facts and reminder/share/save actions where appropriate.
3. A medication label: yellow caution state, with no medical diagnosis or
   dosage advice beyond clearly extracted document content and a pharmacist
   verification option.
4. An unreadable item: uncertainty is explicit, no confident conclusion, and
   a clear retry path.

The first vertical slice is:

```text
Home -> Paste a message -> Review -> “I'm reading this…”
     -> live LLM analysis -> safe red-risk result -> reveal original
     -> confirm stubbed “Verify with organization” action -> History
```

## 4. Commit-by-commit breakdown

1. **Approved contract and runnable project foundation**
   - Files: contract, root documentation, Docker/development configuration,
     frontend and backend project skeletons, CI skeleton.
   - Establishes a deployable local stack, environment-variable configuration,
     and commands shared by development and CI.
   - Reviewable alone: no product behavior; it only makes the project runnable.

2. **Red tests: shared analysis contract and safety policy**
   - Files: response schema, API-contract tests, safety tests, evaluation
     fixtures, CI test-discovery configuration.
   - Defines expected scam-SMS states: valid schema, red risk, safe actions,
     prohibited actions, malformed-model failures, and uncertainty behavior.
   - Reviewable alone: failing tests are the executable specification before
     the implementation exists.

3. **Backend: live LLM analysis and repository-backed history**
   - Files: API routes, provider interface and live adapter, Pydantic schemas,
     analysis/safety services, repository interface, SQLite adapter, migrations
     or initialization, and API documentation.
   - Implements text/image/document submission, one real multimodal call per
     analysis, validation/retry policy, deterministic safety processing,
     persisted results, and History endpoints.
   - Reviewable alone: makes the prior backend behavior tests pass while
     keeping provider and storage implementations replaceable.

4. **Red tests: capture, results, and accessibility flow**
   - Files: frontend unit tests, Playwright tests, accessibility assertions.
   - Defines the user-visible scam-SMS flow: review, calm loading state, red
     risk banner, collapsed original, safe actions, focus order, and responsive
     layouts.
   - Reviewable alone: failing UI tests specify behavior before UI code exists.

5. **Frontend: Warm Paper core flow**
   - Files: React routes, API client, design tokens, Home/Capture/Processing/
     Results components, responsive styles, and accessibility primitives.
   - Implements the first complete live-LLM vertical slice and renders only
     backend-approved structured content.
   - Reviewable alone: makes the prior user-flow tests pass without actions or
     History complexity.

6. **Red tests: confirmed actions, History, and errors**
   - Files: API/action tests, frontend and Playwright user-flow tests, error
     fixtures.
   - Defines explicit confirmation, truthful stub completion copy, stored
     action attempts, reopened History items, deletion, unreadable input,
     provider timeout, invalid provider response, and offline/retry states.
   - Reviewable alone: specifies all remaining MVP behavior before its code.

7. **Actions, History, demo scenarios, and delivery hardening**
   - Files: action registry/handlers, History UI, sample gallery/fixtures,
     deployment configuration, CI workflow, setup/evaluation documentation.
   - Adds stubbed actions, three live-model demo scenarios, history reopening
     and deletion, health checks, and deployable configuration.
   - Reviewable alone: completes the MVP using the established contracts.

8. **Evaluation and accessibility hardening**
   - Files: real-model evaluation runner, Playwright viewport/accessibility
     tests, reporting documentation.
   - Runs curated inputs through the real LLM path and records schema validity,
     broad classification, risk, extraction, uncertainty, and action safety.
   - Reviewable alone: strengthens measurable quality without broadening
     product scope.

## 5. Verification plan

### Automated verification

The project will expose and run these commands:

```bash
docker compose up --build -d
docker compose ps
curl --fail http://localhost:8000/health
docker compose exec api uv run pytest -v
docker compose exec web npm run test
docker compose exec web npm run test:e2e
docker compose exec api uv run python -m app.evaluation --provider live
```

The live-model evaluation reports per fixture:

- schema validity;
- expected broad classification and risk state;
- deadline/amount extraction where applicable;
- required uncertainty;
- allowed actions; and
- prohibited unsafe actions.

### Mandatory manual Playwright verification

Automated browser tests do not replace this gate. Before completion, run the
actual local stack and use the Playwright MCP browser to manually verify:

1. Home -> paste scam SMS -> review -> “I'm reading this…” -> live result.
2. The red result states “Stop and verify before responding,” includes no
   suspicious-sender reply/click path, and offers only approved actions.
3. The original SMS is not visible until its explicit reveal control is used.
4. A stubbed action requires confirmation and accurately states that no
   external action occurred.
5. The result appears in History and reopens correctly.
6. The insurance, medication, and unreadable-item scenarios behave as defined.
7. Mobile and tablet viewports are visually inspected with screenshots for
   legibility, spacing, Warm Paper fidelity, labels, and risk presentation.
8. Keyboard navigation verifies visible focus, logical order, and operable
   controls; critical error/retry states are also manually inspected.

The final implementation handoff reports actual command output and a concise
pass/fail result for every manual flow. It does not report assumed success.

## Approval and traceability

The implementing Linear issue is [MPI-18](https://linear.app/mpieke/issue/MPI-18/build-senior-ai-assistant-mvp).
The approved contract must be committed before implementation begins. No
implementation code begins until this contract is approved.
