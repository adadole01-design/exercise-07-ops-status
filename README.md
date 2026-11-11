# Exercise 07 — Weekly sprint status

Use Python 3.8 or later. The tool uses Python's standard library. Extract the ZIP and open a terminal in the `exercise-07` directory. The `.claude` folder may be hidden in your file browser.

## Generate and view the report

```sh
skill=.claude/skills/ops-weekly-status
python3 "$skill/scripts/report.py" "$skill/fixtures/sprint_tasks_dummy.csv"
```

The saved sample is in `report.txt`. To save a new report, redirect stdout to a file. To report on another CSV or date, run:

```sh
python3 "$skill/scripts/report.py" "/path/to/tasks.csv" --check-date 2026-01-16
```

The default check date is January 16, 2026. A task is overdue when its date is earlier and its status differs from Done. Cancelled follows the same rule as any other status besides Done. Evidence is checked independently. Whitespace is trimmed and comparisons for Done and Missing acceptance evidence ignore case.

Use a UTF-8 CSV with the 11 headers in the sample. Column order can vary and extra columns are accepted. Task IDs, dates and statuses are required per row. All repeated IDs are rejected, including identical repeats. Malformed input exits with code 2, writes the error to stderr and produces no report. Follow-ups use the venture domain owner, then the editorial owner, programme owner or assignee, in that order.

## Run automated checks

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .claude/skills/ops-weekly-status/tests -v
```

The saved `test-results.txt` records seven passing tests on Python 3.15.2, including all four supplied boundary rows. The sample found overdue Tasks 1 and 2 and missing evidence for Task 2.

## Use in Claude Code

Open Claude Code from the extracted project root. Invoke `/ops-weekly-status` and ask for the Exercise 07 demo, or supply your CSV path and optional check date. The skill runs the same local Python command and returns its three bullets.

## Limits of the offline hand-in

The CSV evidence check tests field contents only. It does not open links or verify approvals. The CLI was tested locally. Live Claude Code invocation and Slack delivery remain unverified, and the assignment's Slack screenshot or link is pending user authorization. The supplied CSV contains fictional records.
