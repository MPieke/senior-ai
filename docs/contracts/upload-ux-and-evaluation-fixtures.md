---
title: Upload UX recovery and runnable evaluation fixtures
linear_issue: MPI-18
linear_issue_url: https://linear.app/mpieke/issue/MPI-18/build-senior-ai-assistant-mvp
status: draft_for_review
---

# Upload UX recovery and runnable evaluation fixtures contract

## Purpose

Make file upload reliable and calm for older users, then add a repeatable test
set that exercises the same safety contract against deterministic fixtures and
the live OpenAI provider.

This amendment also separates the current file-picker capability from future
camera capture, and makes uploaded originals viewable from Results and History.

## 1. Current-state architecture

```text
[Home]
  |- Paste a message
  `- Upload a document / Take a picture use the same file-picker path
          |
          v
[Single upload state]
  |- browser file control inside a label
  |- selected file can survive unexpected navigation paths
  `- review/remove affordances are not consistently available
          |
          v
[Processing screen]
  `- text-only “I'm reading this…” state

[Tests]
  |- hand-written API/component/browser tests
  `- no named evaluation fixture catalogue or evaluation runner
```

Uploaded file bytes are currently not retained after analysis, so a document
cannot be viewed again from Results or History.

## 2. Target-state architecture

```text
[Home]
  |- Paste a message
  |- Take a picture — disabled, labelled “Coming soon”
  `- Upload a document — active
          |
          v
[Capture]
  |- visible “Choose a file” button -> hidden native file input
  |- optional drag-and-drop target
  `- supported-type guidance
          |
          v
[Review]
  |- filename, type, size, thumbnail/image preview or PDF first-page preview
  |- Choose another file
  |- Remove file
  `- Continue
          |
          v
[Processing]
  |- calm text
  |- reduced-motion-aware pulse animation
  `- Back/cancel clears pending capture state
          |
          v
[Results]
  |- Show original message/document
  `- accessible image/PDF viewer panel

[Original-upload storage]
  |- app-managed local data directory
  |- analysis record stores an opaque file reference
  `- deleting an analysis deletes its retained original

[Fixture catalogue]
  |- source text/PDF/images
  |- expected safety assertions
  `- fixture/live evaluation runner -> JSON + readable report
```

```text
Sequence — safe file recovery

User          Web app
 | choose file    |
 |--------------> | Capture state
 |                |-> Review state
 | remove/back    |
 |--------------> | clear File + preview + error state
 |                |-> Capture/Home
 | choose file    |
 |--------------> | only the newly selected file can be submitted
```

```text
Sequence — view retained original

User             Results/History        API/storage
 | Show original       |                     |
 |-------------------> | fetch file reference |
 |                     |--------------------> |
 | image/PDF viewer   | <------------------- |
 |<------------------ |                     |
 | delete analysis    |--------------------> |
 |                     | delete record + file |
```

## 3. Commit-by-commit breakdown

1. **Red tests: capture/review/reset and reduced-motion behavior**
   - Files: frontend unit tests and Playwright upload-flow tests.
   - Defines click-to-open file selection, selection review, remove, replace,
     back/cancel state clearing, keyboard access, and processing animation
     behavior with reduced motion enabled.
   - Reviewable alone: executable UX specification before state/UI changes.

2. **Upload state-machine and processing UX implementation**
   - Files: capture/review components or feature module, API client, styles,
     accessibility helpers.
   - Replaces the mixed upload state with explicit Capture, Review, and
   Processing states. Uses a button-triggered native file input, keeps
   drag-and-drop optional, clears state on exit, and adds a non-distracting,
   reduced-motion-aware animation. Leaves Take a picture visibly disabled as
   a future capability rather than presenting a duplicate file-picker path.
   - Reviewable alone: makes the UX tests pass without changing analysis rules.

3. **Red tests: evaluation fixture contract**
   - Files: backend evaluation tests and fixture expectation files.
   - Defines fixture format, deterministic expected results, required/forbidden
     actions, fact extraction assertions, readable report output, and live-run
     result recording.
   - Reviewable alone: prevents the runner becoming an unasserted demo script.

4. **Original-document retention and viewer**
   - Files: backend storage/repository layer, analysis deletion API, result and
     History viewer components, accessibility/browser tests.
   - Retains original image/PDF files in an app-managed local data directory,
     linked by an opaque analysis reference. Adds image and PDF viewer panels
     from Results and reopened History items; deleting an analysis removes its
     original file and record together.
   - Reviewable alone: introduces a bounded privacy-preserving retention
     feature without changing LLM analysis behavior.

5. **Fixture catalogue and evaluation runner**
   - Files: `backend/tests/fixtures/`, evaluation service/CLI, documentation,
     CI workflow.
   - Adds scam SMS, insurance notice, appointment notice, unreadable input,
     and personal message fixtures. Implements `fixture` and `live` modes;
     fixture mode is deterministic and CI-safe, while live mode records model
     and prompt version plus pass/fail differences.
   - Reviewable alone: makes the evaluation contract tests pass and provides
     reproducible demo/test inputs.

## 4. Verification plan

```bash
uv run --directory backend pytest -v
npm run test --prefix frontend
npm run build --prefix frontend
npm run test:e2e --prefix frontend
uv run --directory backend python -m app.evaluation --provider fixture
uv run --directory backend python -m app.evaluation --provider live
```

Mandatory manual Playwright verification:

1. Click **Choose a file** and select a real PDF; do not rely on drag-and-drop.
2. Verify filename/type/size, Remove, and Choose another file are visible and
   keyboard-operable.
3. Select another file, then navigate back/cancel; reopen upload and confirm
   no previous file remains.
4. Submit a document and inspect the calm processing animation at desktop,
   mobile, and tablet widths.
5. Enable reduced motion and confirm the animation becomes static or minimal.
6. Attempt an unsupported file and confirm the clear recovery action.
7. Confirm Take a picture is visibly disabled and says “Coming soon.”
8. Open an original image/PDF from Results and from a reopened History item;
   delete the item and confirm the viewer is no longer available.

The evaluation output must list every fixture, expected vs actual safety state,
and actionable pass/fail status. The final report records real command output
and manual verification results.
