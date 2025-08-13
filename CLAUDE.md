# PROJECT RULES & STANDARDS

These rules apply to all code, documentation, and assets generated in this project.
They are binding constraints for Claude Code when processing PRPs or producing deliverables.

## 1. Output Philosophy

- **Solution-first**: Every output should solve a business problem — no "demo tech" without ROI context.
- **Niche-agnostic**: Packages should be configurable to work across multiple industries without hardcoding industry-specific values.
- **Reusable**: Code, docs, and workflows must be modular; prefer creating reusable components over hardcoded one-offs.

## 2. Automation Packaging Standards

### Directory Structure (per package):

```
/packages/<slug>/
  workflows/     → n8n JSON exports
  docs/          → implementation.md, configuration.md, runbook.md, sop.md, loom-outline.md, client-one-pager.md
  tests/         → fixtures, happy-path script, failure cases
  metadata.json  → tags, niche, ROI notes, inputs, outputs, dependencies
```

### metadata.json fields:

- `name`
- `slug`
- `niche_tags` (array)
- `problem_statement`
- `outcomes` (measurable)
- `roi_notes` (time saved, cost saved, revenue potential)
- `inputs`
- `outputs`
- `dependencies` (integrations, connectors)
- `security_notes`
- `last_validated`

## 3. Engineering Standards

### Idempotency
All flows must have deterministic keys (e.g., email hash, external ID) to avoid duplicates.

### Retries
Use 3× exponential backoff with jitter; fail gracefully into a dead-letter queue (DLQ) pattern.

### Logging
- Structured JSON logs with timestamps, node IDs, durations
- Log both success and failure events

### Observability
- Include per-node timing metrics
- Hook success/failure webhooks into Notion Deployments DB

### Performance
- Median run-time for simple flows ≤ 3 seconds
- ≥ 99% success rate over 30 days with retries

### Security
- All secrets stored in .env or a secrets manager
- PII encrypted at rest; redact from logs
- EU data residency option documented

### Versioning
- Every automation has a version property in metadata
- Version bumps for any breaking change

## 4. Documentation Standards

### Required Documents
- **Implementation Guide**: Step-by-step with screenshots/diagrams
- **Configuration Guide**: Env vars, API keys, rate limit notes, integration "gotchas"
- **Runbook**: How to monitor, troubleshoot, and roll back
- **SOPs**: Task-level how-tos for team members
- **Loom Outline**: Script for a 3–5 minute video walkthrough
- **Client One-Pager**: Problem → Solution → Benefits → KPIs → ROI projection

### Style Guidelines
- Clear, concise, action-oriented
- Use tables for inputs/outputs
- **Bold key actions and warnings**
- Keep internal docs separate from client-facing docs

## 5. Notion Business OS Schema

Claude must maintain compatibility with these core databases:

### Library – Canonical packages
**Properties**: Name, Slug, Niche Tags, Problem Statement, Outcomes, Inputs, Outputs, Dependencies, Security Notes, Status, Version, Links (Repo path, n8n export), ROI Notes, Last Validated.

### Automations – Client-specific instances
Relates to Library, Clients, and Deployments.

### Components – Reusable subflows/connectors
Tracks ownership, versions, and tests.

### Clients – Accounts and engagement details
Tracks installed packages, KPIs.

### Deployments – Environment details
Environment details, dates, checklist status, first-run results.

## 6. PRP Behavior Requirements

### When `/generate-prp` is run:
- Always create or update relevant Notion DB schemas if they are missing
- Use Automation Vault workflows as inspiration, not as final outputs without adaptation
- Enforce naming conventions, retries, and logging in generated n8n JSON
- Include test fixtures for first-run verification

### When `/execute-prp` is run:
- Validate all workflows before packaging
- Populate all docs in /docs subfolder
- Generate/update metadata.json with current date as last_validated
- Push records to Notion with the correct relations and rollups

## 7. Quality Gates

A package cannot be marked complete unless:

- ✅ All metadata fields are filled
- ✅ Workflow passes simulated run with fixture data
- ✅ Documentation is complete and clear enough for a new engineer to deploy without help
- ✅ Notion entries are created/updated for Library, Components, and Deployments

## 8. Prohibited Practices

- ❌ No hardcoded API keys, secrets, or credentials in code or docs
- ❌ No untested workflows in the /packages directory
- ❌ No client PII in repo commits
- ❌ No deployment without updating last_validated in metadata

## ACCEPTANCE TESTS

Before committing a package:

1. **Run validation**: `make validate PACKAGE=<slug>` — all tests pass
2. **Review documentation**: Generated docs against style guide
3. **Confirm Notion sync**: Notion records reflect the latest package state
4. **Log traceability**: Ensure Automation Vault reference is logged in metadata