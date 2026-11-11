---
name: ops-weekly-status
description: Generate a three-bullet Slack status report from a sprint task CSV, covering overdue work, missing acceptance evidence, and owner follow-ups.
---

# Weekly sprint status

Use the CSV path and optional check date supplied with the request. For an Exercise 07 demo, use `fixtures/sprint_tasks_dummy.csv` inside this skill. Ask for a CSV path if neither applies.

From the project root, run `python3 .claude/skills/ops-weekly-status/scripts/report.py "PATH_TO_CSV"`. Add `--check-date YYYY-MM-DD` when the user supplies a check date. The default is January 16, 2026.

Use the three bullets from stdout as the report. If the script exits with an input error, share the error and request corrected input. The script evaluates overdue work and missing evidence independently. Treat evidence text as a record of what the CSV contains. Preserve the listed IDs, dates and owners, and avoid inferring causes or approvals.

Keep the report local. Any external operation requires the user's prior permission.
