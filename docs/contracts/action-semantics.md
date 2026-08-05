---
title: Separate safety guidance from user actions
linear_issue: MPI-18
linear_issue_url: https://linear.app/mpieke/issue/MPI-18/build-senior-ai-assistant-mvp
status: draft_for_review
---

# Separate safety guidance from user actions contract

## Purpose

Prevent advisory statements such as “Do not send money” from appearing as
clickable actions. A result must distinguish information the person should
know from a specific operation they can choose to start.

## 1. Current-state architecture

```text
OpenAI / fixture provider
          |
          v
AnalysisPayload.recommendedActions[]
  |- verify_with_organization
  |- report_suspicious
  `- take_no_action (may be labelled “Do not send money”)
          |
          v
FastAPI validation and basic safety normalization
          |
          v
React Results renderer
  `- renders every recommended action as a clickable button
          |
          v
Generic stub confirmation dialog
```

The `take_no_action` enum represents a conclusion or safety instruction, but
the UI treats it as an operation. This gives a misleading confirmation flow
for advice that should need no confirmation.

```text
Sequence — current red-risk result

Model -> API: recommendedActions includes “Do not send money”
API -> Web: returns it unchanged
Web -> User: clickable “Do not send money”
User -> Web: confirms an action that did not do anything
```

## 2. Target-state architecture

```text
OpenAI / fixture provider
          |
          v
AnalysisPayload.recommendedActions[]
          |
          v
Backend action normalization
  |- interactive operations -> recommendedActions
  |    verify_with_organization, report_suspicious,
  |    call_trusted_contact, share_with_trusted_contact,
  |    create_reminder, draft_reply, save_item
  `- advisory take_no_action -> result safety guidance
          |
          v
React Results renderer
  |- non-clickable “What to do now” guidance
  `- buttons only for interactive/stubbed operations
          |
          v
Action confirmation dialog for a real/stubbed operation only
```

```text
Sequence — target red-risk result

Model -> API: action list may include “Do not send money”
API -> API: remove take_no_action from clickable actions; retain its label as guidance
API -> Web: interactive actions + safety guidance
Web -> User: visible safety instruction and only meaningful action buttons
User -> Web: confirmation only for a chosen operation
```

No database tables or persisted response schema change is required; the API
adds an optional presentation field to the stored result for safety guidance.

## 3. Commit-by-commit breakdown

1. **Add action-semantics contract**
   - Files: `docs/contracts/action-semantics.md`
   - Adds this contract and the MPI-18 cross-reference.
   - Reviewable independently because it records the UI/API boundary before
     behavior changes.

2. **Add failing action-normalization and rendering tests**
   - Files: `backend/tests/test_api.py`, `frontend/src/App.test.tsx`
   - Define that `take_no_action` does not appear as a button, remains visible
     as plain safety guidance, and interactive actions still receive a
     confirmation dialog.
   - Reviewable independently because it establishes the observable behavior
     before implementation.

3. **Normalize guidance in the backend and render it distinctly**
   - Files: `backend/app/main.py`, `frontend/src/App.tsx`,
     `frontend/src/styles.css`
   - Move `take_no_action` labels from `recommendedActions` into a dedicated
     safety-guidance field; render it as text and restrict confirmation buttons
     to interactive action types.
   - Reviewable independently because it makes the test-defined safety
     distinction in one complete vertical slice.

4. **Run CI-facing verification**
   - Files: no production-file changes expected.
   - Run the backend/frontend suites, the existing browser suite, and a manual
     Playwright red-risk flow using the family-emergency fixture.
   - Reviewable independently because it records real end-to-end results.

## 4. Verification plan

Run from repository root:

```sh
make test
make up
make smoke
make test-e2e
curl --fail --form 'file=@backend/tests/fixtures/family-emergency-scam.pdf;type=application/pdf' http://localhost:8000/v1/analyses
make down
```

Manual Playwright flow:

1. Start the app with `make up` and open `http://localhost:4173`.
2. Upload `backend/tests/fixtures/family-emergency-scam.pdf`.
3. Confirm “Do not send money or gift card codes” (or equivalent model advice)
   appears as text, not a button.
4. Confirm “Verify with trusted family member” remains a button and its
   confirmation dialog still states that no external contact will be made.

Expected invariant: every clickable recommended action corresponds to a
backend action attempt; plain safety advice never opens an action dialog.
