# Productized Automation Agency – Internal Delivery Engine

## Overview

**Goal:** Build an internal, repeatable engine that turns raw "automation ingredients" (our n8n workflow vault + new components) into market-ready, productized automation packages.

### The Engine Process

1. Research a niche's pains
2. Map opportunities  
3. Assemble/adapt workflows
4. Validate & document
5. Package to Notion as sellable offers
6. Provide deploy/runbooks for client projects

## Core Capabilities

### 1. Niche Research Module

Given a niche keyword, gather pains, high-leverage processes, existing tools, and quick-win automations; output a structured "Niche Brief".

### 2. Opportunity Mapping Module  

Convert pains → candidate automations with ROI notes (time saved, cost impact, revenue lift), dependencies, and risk.

### 3. Assembly Module

- Pull candidate workflows from our Automation Vault (n8n JSON/TXT) and stitch + adapt
- Surface missing connectors or nodes; generate scaffolds for gaps  
- Enforce standards: naming, retries, idempotency keys, logging

### 4. Validation Module

- Lint n8n JSON, simulate test runs with fixture data, validate env vars, rate limits, and secrets presence
- Add success/failure hooks; produce a checklist + logs

### 5. Documentation & Packaging Module

- **Generate:** Implementation Guide, Config Guide (.env & secrets), Runbook, SOPs, Loom script outlines, and Client-facing one-pager (problem → outcome → KPIs)
- Publish structured records to Notion (databases defined below)

### 6. Deployment Module

- Export n8n workflows + environment template
- Create a deploy checklist  
- Generate a "First-Run Verification" task list

## Deliverables (per automation package)

Each package creates a `/packages/<slug>/` directory containing:

### File Structure

- **`workflows/`** - n8n JSON files
- **`docs/`** - Complete documentation suite:
  - `implementation.md`
  - `configuration.md`  
  - `runbook.md`
  - `sop.md`
  - `loom-outline.md`
  - `client-one-pager.md`
- **`tests/`** - Testing resources:
  - Fixtures
  - Happy-path scripts
  - Failure cases
- **`metadata.json`** - Package metadata including tags, niche, ROI notes, inputs/outputs, dependencies

### Notion Integration

Records created/updated in:

- **Automations** database
- **Components** database  
- **Clients** database (when applicable)
- **Deployments** database
- **Library** database (canonical package)

## Non-Goals (for v1)

- No multi-tenant web UI; all ops via repo + Notion + n8n
- No billing/invoicing integration (later)

## Success Criteria

1. **Speed:** Generate ≥1 complete, validated package from a chosen niche in ≤1 hour of operator time
2. **Quality:** All docs auto-produced, passing a "new engineer can deploy in one sitting" test  
3. **Reusability:** Packages are vertical-agnostic: 80% reusable across niches with ≤20% adaptation

## Examples & Patterns

Please read these patterns and mirror their structure when generating code/docs:

### Required Pattern Files

- **`examples/agent/plan_and_validate.md`** — Shows how to produce stepwise plans with validation gates
- **`examples/config/env_template.md`** — Illustrates env var catalogs and secrets policy  
- **`examples/n8n/patterns.md`** — Naming, retries, idempotency (email hash or external id), error routing, DLQ pattern, and observability fields
- **`examples/docs/style_guide.md`** — Headings, tone (client vs. internal), tables for inputs/outputs, and ROI callouts
- **`examples/tests/fixtures.md`** — How to define input samples and assertions for "first-run verification"

> **Note:** If any of these files don't exist yet, create lightweight stubs as part of the PRP so the generator has concrete patterns to follow (keep them small but prescriptive).

### Automation Vault Examples

Reference our Automation Vault (already extracted in this session) as ingredient examples when proposing assemblies:

**Examples:** HubSpot chat assistant, feedback analyzers, Notion appenders, Gmail→Drive PDF router, Twitter banner generator, Google Sheets summarizer, etc.

> **Important:** Use vault items as inspiration, not final deliverables.

## Documentation

### Template & Workflow Docs

- Context-Engineering Template (Quick Start, INITIAL.md spec, PRP workflow) — use repo content to align outputs with expected structure.

### Primary Tools & APIs

- n8n — workflow JSON schema, node catalog, env/secrets, import/export; see docs home and nodes reference
- Model Context Protocol (MCP) — servers list for integrations used via Claude Desktop
- Claude Code / Claude Desktop — commands for `/generate-prp` and `/execute-prp`; uses the template’s `.claude/commands` behavior
- Notion API — databases, relations, rollups, rate limits, auth
- Common SaaS targets — HubSpot, Slack, Google Drive, Gmail, Linear, Airtable

> In the PRP, link directly to the exact docs sections you use (endpoints, payloads, limits) so future maintainers can verify.

## Other Considerations

### Notion Business OS

Create via PRP if missing.

- Library (canonical automation packages)
  - Properties: Name, Slug, Niche Tags, Problem Statement, Outcomes, Inputs, Outputs, Dependencies, Security Notes, Status, Version, Links (Repo path, n8n export), ROI Notes, Last Validated
- Automations (instances) — relates to Library, Clients, and Deployments
- Components (reusable subflows/connectors) — tracks ownership, versions, and tests
- Clients — account, owner, stage, installed packages, KPIs
- Deployments — env, date, checklist status, first-run results, incidents

## Engineering Standards

- Idempotency — deterministic keys (email hash, external id) and dedupe nodes
- Retries & Backoff — 3× exponential, jitter; circuit-breakers on persistent failures
- PII & Compliance — encrypt at rest (Postgres/Turso if used), redact logs; EU residency option; document third-party processing (OpenAI justification when used)
- Observability — structured logs, per-node timings, error taxonomy, and success webhooks to Notion
- Performance Targets — median end-to-end run ≤3s for simple flows; ≥99% success over 30-day window with retries
- Packaging — every package ships with `metadata.json`, env template, and `first_run_checklist.md`

## Operator UX

- One command to generate from a niche keyword: `make niche="logistics 3PL" run discover→map→assemble→validate→package` (the PRP can simulate this via tasks)
- Clear upgrade path: any package can be re-generated with updated dependencies or docs via `/execute-prp` on the same PRP

## Risks / Gotchas

- SaaS API limits and auth quirks — include per-integration gotchas in docs
- Secrets drift across environments — ship a `secrets.example.json` and vault policy
- Over-fitting to a niche — enforce agnostic abstractions and config-driven mappings

## Acceptance Tests (must pass)

- Given a niche (“real estate brokerages”), engine produces a complete Niche Brief, Opportunity Map, and one packaged automation (e.g., “Lead Intake → Enrich → Qualify → CRM → Slack thread”) with:
  - n8n export, env template, tests, docs, and Notion entries created
  - First-run verification script completes with green checks and sample fixture data
  - Documentation is sufficient for a new engineer to deploy without help
