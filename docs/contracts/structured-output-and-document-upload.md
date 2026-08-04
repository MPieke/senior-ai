---
title: Strict structured analysis output and document upload
linear_issue: MPI-18
linear_issue_url: https://linear.app/mpieke/issue/MPI-18/build-senior-ai-assistant-mvp
status: draft_for_review
---

# Strict structured output and document upload contract

## Purpose

Complete two missing MVP boundaries:

1. Every live LLM response must conform to a strict, versioned application
   schema before the API persists or returns it.
2. A user can select an image, PDF, or supported document in the Warm Paper
   interface, review the selected item, submit it, and receive the same
   analysis result flow as pasted text.

OpenAI is the only live provider in this change. The existing provider
interface remains so another provider can be added later, but Anthropic is not
configured or called.

## 1. Current-state architecture

```text
[React app]
  |- pasted text works
  `- picture/document controls are disabled
          |
          v
[FastAPI text endpoint]
  |- accepts JSON { text }
  |- parses generic JSON from provider
  `- persists/returns an unvalidated dictionary
          |
          v
[OpenAI provider]
  `- requests broad JSON object (strict=false)
```

The current boundary does not guarantee required fields, allowed enums,
limited actions, or compatible frontend content. It also cannot accept a file.

## 2. Target-state architecture

```text
[React app]
  |- paste text
  |- choose image/PDF/document
  |- local review: filename, type, size, remove
  `- submit one normalized analysis request
          |
          v
[FastAPI analysis endpoint]
  |- accept JSON text OR multipart file
  |- enforce file type and byte limits
  |- normalize input to AnalysisInput
  `- reject unsupported/unreadable input with a clear next step
          |
          v
[OpenAI analysis provider]
  |- text -> input_text
  |- image -> input_image data URL
  `- PDF/document -> input_file base64 data
          |
          v
[Pydantic AnalysisResult schema]
  |- exported as OpenAI strict JSON Schema
  |- validate raw provider response
  |- apply deterministic safety policy
  `- validate final result again
          |
          v
[Repository] -> history/result API -> [React results screen]
```

```text
Sequence — document upload

User        React app        API        OpenAI        Repository
 | choose PDF  |              |             |               |
 |-----------> | preview      |             |               |
 | continue   | multipart    |             |               |
 |------------|------------> | validate    |               |
 |            |              | file input  |               |
 |            |              |-----------> |               |
 |            |              | strict JSON |               |
 |            |              |<----------- |               |
 |            |              | schema + safety policy         |
 |            |              |-----------------------------> |
 | result     |<------------ |               save result      |
```

## 3. Commit-by-commit breakdown

1. **Red tests: strict result schema and multipart input contract**
   - Files: backend schema/safety tests and API multipart tests.
   - Defines required response fields/enums, invalid-provider rejection,
     action cap/safety rules, accepted image/PDF types, size limit, and clear
     unsupported-file errors.
   - Reviewable alone: executable missing behavior before implementation.

2. **Backend: validated structured output and normalized file input**
   - Files: Pydantic schemas, analysis input normalization, OpenAI provider,
     API routes, safety policy, repository metadata.
   - Exports the Pydantic JSON Schema for OpenAI structured output; validates
     provider JSON before and after deterministic post-processing. Adds
     multipart image/PDF/document processing without logging raw content.
   - Reviewable alone: makes backend contract tests pass.

3. **Red tests: document selection, review, and submit flow**
   - Files: frontend component tests and Playwright upload flow.
   - Defines enabled document/photo controls, preview filename/type, removal,
     upload submission, error state, and safe result rendering.
   - Reviewable alone: documents the user flow before UI implementation.

4. **Frontend: document capture and review**
   - Files: API client, Home/Capture/Review components and styles.
   - Enables image/document selection, accessible file labels, a one-item
     review screen, and JSON/multipart submission while preserving pasted text.
   - Reviewable alone: makes the frontend tests pass.

5. **Evaluation and delivery hardening**
   - Files: document fixtures, live-evaluation runner, Docker/CI updates,
     deployment documentation.
   - Adds appointment/insurance PDF and unreadable-file evaluation fixtures;
     ensures CI discovers backend, component, and Playwright tests.
   - Reviewable alone: demonstrates the real provider boundary and deployment
     path.

## 4. Verification plan

Run all commands against a clean local stack:

```bash
uv run --directory backend pytest -v
npm run test --prefix frontend
npm run build --prefix frontend
npm run test:e2e --prefix frontend
docker compose up --build -d
curl --fail http://localhost:8000/health
```

The backend suite must prove:

- invalid/missing model fields are rejected rather than returned;
- red-risk outputs cannot include direct engagement with a suspicious sender;
- more than three or duplicate actions are removed;
- text, image, and PDF inputs normalize correctly;
- unsupported type, oversized file, and unreadable input return clear states.

The browser suite and mandatory manual Playwright pass must prove:

1. Upload a supported PDF and see its filename/type in the review screen.
2. Remove it and return to a clean capture state.
3. Submit a sample document and reach the result screen through the live API.
4. Verify original content remains collapsed until explicitly revealed.
5. Check mobile and tablet viewport layouts, keyboard focus, and a rejected
   file’s recovery message.

The final report records the real pass/fail result, model/prompt version, and
any live-provider evaluation variance. No implementation begins until this
contract is approved.
