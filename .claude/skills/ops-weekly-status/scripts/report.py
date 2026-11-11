"""Read sprint tasks and print three Slack mrkdwn bullets."""
import argparse
import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re

DEFAULT_DATE = date(2026, 1, 16)
COLUMNS = (
    "task_id", "title", "user", "output", "acceptance_evidence", "sprint",
    "due_date", "status", "venture_domain_owner", "editorial_owner",
    "programme_owner",
)


def parse_date(value):
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise ValueError(f"expected YYYY-MM-DD, got {value!r}")
    return date.fromisoformat(value)


@dataclass(frozen=True)
class Task:
    task_id: str
    due_date: date
    status: str
    evidence: str
    owner: str
    assignee: str

    def overdue(self, check_date):
        return self.due_date < check_date and self.status.casefold() != "done"

    @property
    def missing_evidence(self):
        return self.evidence.casefold() in ("", "missing acceptance evidence")


def read_tasks(path):
    tasks = []
    seen = set()
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        try:
            header = next(reader, [])
            if len(set(header)) != len(header):
                raise ValueError("duplicate column names")
            missing = set(COLUMNS) - set(header)
            if missing:
                raise ValueError(f"missing columns: {', '.join(sorted(missing))}")
            for fields in reader:
                if not fields:
                    continue
                try:
                    if len(fields) != len(header):
                        raise ValueError("row has a different number of fields than the header")
                    row = dict(zip(header, (field.strip() for field in fields)))
                    task_id = row["task_id"]
                    for name in ("task_id", "status"):
                        if not row[name]:
                            raise ValueError(f"{name} is blank")
                    if task_id in seen:
                        raise ValueError(f"duplicate task_id {task_id!r}")
                    tasks.append(Task(
                        task_id, parse_date(row["due_date"]), row["status"],
                        row["acceptance_evidence"], row["venture_domain_owner"]
                        or row["editorial_owner"] or row["programme_owner"],
                        row["user"],
                    ))
                    seen.add(task_id)
                except ValueError as error:
                    raise ValueError(f"line {reader.line_num}: {error}") from error
        except csv.Error as error:
            raise ValueError(f"line {reader.line_num}: invalid CSV: {error}") from error
    return tasks


def slack_text(value):
    return (" ".join(value.split()).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace("*", "＊").replace("_", "＿")
            .replace("~", "～").replace("`", "｀"))


def render(tasks, check_date):
    overdue = [task for task in tasks if task.overdue(check_date)]
    missing = [task for task in tasks if task.missing_evidence]

    def label(task):
        return f"Task {slack_text(task.task_id)} (due {task.due_date})"

    followups = []
    for task in tasks:
        actions = []
        if task.overdue(check_date):
            actions.append("confirm current status and expected completion date")
        if task.missing_evidence:
            actions.append("provide the acceptance evidence or confirm where to find it")
        if actions:
            contact = slack_text(task.owner or task.assignee or "Owner not listed")
            followups.append(f"{label(task)} — {contact}: {' and '.join(actions)}")

    late_text = "; ".join(map(label, overdue)) or "None."
    evidence_text = "; ".join(map(label, missing)) or "None."
    followup_text = "; ".join(followups) or "None."
    return "\n".join((
        f"• *Overdue tasks* (as of {check_date}): {late_text}",
        f"• *Missing acceptance evidence:* {evidence_text}",
        f"• *Owner follow-ups:* {followup_text}",
    ))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--check-date", type=parse_date, default=DEFAULT_DATE,
                        metavar="YYYY-MM-DD", help=f"default: {DEFAULT_DATE}")
    args = parser.parse_args()
    try:
        tasks = read_tasks(args.csv_path)
    except (OSError, ValueError) as error:
        parser.exit(2, f"Input error: {error}\n")
    print(render(tasks, args.check_date))


if __name__ == "__main__":
    main()
