# Shared AI collaboration rules — GPT lead, Claude review, dot operations

## Roles
- GPT / Codex is the **primary developer**. Implement on a feature branch, test and open a Draft PR; no direct pushes to main.
- Claude Code is the **independent reviewer**, not the default developer. It checks PR changes, business logic, security, regressions and tests. Its GitHub access and automated triggering require separate configuration; this document does not activate them.
- dot handles LINE receipt reconciliation monitoring, missing inputs and daily exceptions **only after its own access to the receipt service and finance source is verified**. Do not assume dot is connected just because this document exists.
- The owner alone approves merging, production deployment, data migrations, payroll, financial posting and real LINE messages.

## Guardrails
- Do not deploy, merge, send real notifications, change secrets, alter production data, or perform destructive operations without explicit separate approval.
- No API keys, real receipts, employee information or confidential exports in Git.
- Source photos, store/date, POS, product prices and reconciliation rules must be confirmed before treating OCR results as financial facts; missing values are unknown, not zero.
- Every PR documents scope, tests, risks, rollback and any unknown hosting/source mapping.

## Project-specific constraints
**Attendance CSV converter** — Utility for transforming attendance files. Treat employee rows as confidential. Use synthetic fixtures, never commit real attendance CSV, salary spreadsheets or identifiers.

## Acceptance
1. Document which GitHub repo, cloud environment and domain correspond to the requested feature.
2. GPT/Codex implements and tests; Claude independently reviews when authorized; record the actual status.
3. Owner approves any merge/deployment separately.
