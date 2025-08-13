# n8n Workflow Patterns

## Naming Conventions
- Use `snake_case` for node names.
- Prefix integrations: `slack_notify_new_lead`.
- Prefix error handling: `error__<original_node>`.

## Idempotency
- Always hash unique identifiers (e.g., email) for deduplication.
- Store dedupe keys in external DB if cross-run consistency needed.

## Retries & Backoff
- Configure 3 retries with exponential backoff (200ms → 800ms) + jitter.
- Send failures to DLQ pattern node.

## Logging
- Use "Set" nodes to append timestamp + node ID to logs object.
- Forward logs to monitoring service or Notion Deployments DB.

## Observability
- Track execution time per node using `Date.now()` at start/end.
- Aggregate results in summary object for validation.

## Security
- No secrets in node params — always use env vars.
- Mask sensitive outputs before logging.