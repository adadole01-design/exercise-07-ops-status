import csv
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts" / "report.py"
sys.path.insert(0, str(SCRIPT.parent))
from report import COLUMNS, parse_date, read_tasks


class ReportTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "tasks.csv"

    def write_rows(self, *rows, header=COLUMNS):
        with self.path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(header)
            for row in rows:
                writer.writerow([row.get(column, "") for column in header])

    def run_cli(self, *args, path=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(path or self.path), *args],
            capture_output=True, text=True,
        )

    def assert_input_error(self, result, message):
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn(message, result.stderr)

    def test_supplied_boundaries(self):
        with (SKILL / "fixtures" / "boundary-tests.csv").open(newline="") as stream:
            for case in csv.DictReader(stream):
                with self.subTest(case=case["test"]):
                    self.write_rows(dict(case, task_id=case["test"]))
                    if case["overdue"] == "input error":
                        self.assert_input_error(self.run_cli(
                            "--check-date", case["check_date"]), "Input error: line 2")
                        continue
                    task, = read_tasks(self.path)
                    self.assertEqual(task.overdue(parse_date(case["check_date"])),
                                     case["overdue"] == "yes")
                    self.assertEqual(task.missing_evidence, case["missing_evidence"] == "yes")

    def test_supplied_sprint_report(self):
        result = self.run_cli(path=SKILL / "fixtures" / "sprint_tasks_dummy.csv")
        self.assertEqual(result.returncode, 0, result.stderr)
        late, evidence, followups = result.stdout.splitlines()
        self.assertTrue(all(line.startswith("• *") for line in (late, evidence, followups)))
        self.assertIn("as of 2026-01-16", late)
        self.assertIn("Task 1 (due 2026-01-15)", late)
        self.assertIn("Task 2 (due 2026-01-10)", late)
        self.assertNotIn("Task 3", result.stdout)
        self.assertNotIn("Task 1", evidence)
        self.assertIn("Task 2 (due 2026-01-10)", evidence)
        self.assertIn("Task 1 (due 2026-01-15) — Technical lead InspectOS", followups)
        self.assertIn("Task 2 (due 2026-01-10) — HR Lead", followups)

    def test_malformed_inputs(self):
        valid = dict(task_id="1", due_date="2026-01-15", status="In Progress")
        cases = (
            ("missing columns", ("task_id",), (valid,)),
            ("duplicate column", (*COLUMNS, "task_id"), (valid,)),
            ("duplicate task_id", COLUMNS, (valid, dict(valid, status="Done"))),
            ("status is blank", COLUMNS, (dict(valid, status=" "),)),
            ("task_id is blank", COLUMNS, (dict(valid, task_id=""),)),
            ("expected YYYY-MM-DD", COLUMNS, (dict(valid, due_date="20260115"),)),
        )
        for message, header, rows in cases:
            with self.subTest(message=message):
                self.write_rows(*rows, header=header)
                self.assert_input_error(self.run_cli(), message)

    def test_broken_csv(self):
        for row, message in [('1,"unterminated', "invalid CSV"), ("1,short", "number of fields")]:
            with self.subTest(row=row):
                self.path.write_text(",".join(COLUMNS) + "\n" + row, encoding="utf-8")
                self.assert_input_error(self.run_cli(), message)

    def test_empty_table(self):
        self.write_rows()
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(result.stdout.splitlines()), 3)
        self.assertTrue(all(line.endswith("None.") for line in result.stdout.splitlines()))

    def test_no_overdue_with_evidence_followup(self):
        self.write_rows(dict(task_id="D", status=" dOnE ", due_date="2026-01-15",
                             acceptance_evidence="  ", editorial_owner="Editorial"))
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        late, evidence, followups = result.stdout.splitlines()
        self.assertTrue(late.endswith("None."))
        self.assertIn("Task D", evidence)
        self.assertIn("Editorial: provide", followups)
        self.assertNotIn("expected completion", followups)

    def test_check_date_override_and_invalid_date(self):
        self.write_rows(dict(task_id="C", status="Cancelled", due_date="2026-01-17",
                             acceptance_evidence="link-present"))
        result = self.run_cli("--check-date", "2026-01-18")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Task C", result.stdout.splitlines()[0])
        self.assert_input_error(self.run_cli("--check-date", "2026-02-30"), "--check-date")


if __name__ == "__main__":
    unittest.main()
