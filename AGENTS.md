# AI collaboration operating rules (Claude Code / OpenAI Codex / ChatGPT / dot)

## Workflow
- Claude Code may investigate and propose changes on a dedicated feature branch. Open a Draft PR; do not push to main, merge, release or deploy without explicit owner approval.
- OpenAI Codex reviews PR diffs, test evidence, data integrity, access control, and regressions. Codex review configuration is **external**; this file does not enable automatic reviews. A manual `@codex review` may be used on GitHub when enabled. Review results are not proof of deployment safety.
- ChatGPT helps coordinate requirements and verify source-of-truth data. The personal dot can track reconciliation status and surface exceptions only if its relevant connector and permissions are independently configured. Do not assume dot can read this repository or execute changes because this file exists.
- Report status accurately: repository connected, PR opened, Codex review triggered/completed, tests passed, merged, and deployed are separate milestones.

## Safety / approvals
- No production deployments, database migrations, destructive commands, credential changes, payment changes, LINE messages, salary writes, or automatic merges without separate explicit approval.
- Never store API keys, access tokens, LINE channel secrets, customer data, employee data, receipts, or financial exports in Git. Use host-managed secret storage and least-privilege access.
- Read existing code and README before changes; prefer small PRs, synthetic test fixtures and reproducible commands. Do not assert a live website corresponds to this repo until verified from the hosting provider.
- Preserve all existing workflows; new reconciliation must not replace or break the original LINE ordering flow.
- Each PR must state scope, source of truth, risk, tests, rollback, migration requirements, and any unverified assumptions. No silent correction of source data.

## Project-specific constraints
**Attendance CSV converter** — Utility for transforming attendance files. Treat employee rows as confidential. Use synthetic fixtures, never commit real attendance CSV, salary spreadsheets or identifiers.

## Acceptance
1. Document which GitHub repo, cloud environment and domain correspond to the requested feature.
2. Run available checks, state missing checks, and request Codex review for substantive changes.
3. Owner approves any merge/deployment separately.
