# AGENTS.md — Claude + Codex review rules

Project: attendance_converter

## Purpose
Claude Code may propose implementation changes; Codex reviews pull requests independently. This file defines review standards and does not authorize deployment or access to production data.

## Project-specific safeguards
CSV attendance conversion tool: preserve source files, privacy, employee ID matching, time rounding, break detection, export format and cross-midnight calculations. Do not use generated calculations as final payroll without human verification.

## Review checklist
1. Review the actual PR diff and relevant tests, not only the PR description.
2. Flag security, authentication/authorization, personal data, financial arithmetic, data migration, destructive operations, missing tests, and deployment risks; use severity and file references.
3. Verify existing behavior and regression risk, and identify untested assumptions.
4. Never invent test results or claim production parity without evidence.
5. Do not request or expose passwords, API tokens, database credentials, LINE secrets or real customer/employee data.
6. Do not auto-merge, deploy, trigger data migrations, run writes against production, or approve financial/payroll changes without explicit owner sign-off.
7. Prefer the existing codebase and tests; never replace an existing website or database to solve a small issue.
8. PRs must include scope, test evidence, risk/rollback plan, and whether any live services or deployment branches are affected.

## Collaboration workflow
Claude works on a feature branch -> opens PR -> Codex reviews -> Claude fixes findings on the same PR -> Codex re-reviews -> owner approves merge and deployment separately. Draft PRs can be manually reviewed with `@codex review`; do not assume automatic review is active for every repository.

All dates for Taiwan business operations should use Asia/Taipei unless the feature explicitly requires another zone.
