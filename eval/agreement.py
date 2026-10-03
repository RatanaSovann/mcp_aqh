"""Compare your own pass/fail marks with the scorer's, to see if the scorer can be trusted.

1. Open a run's marking_sheet.csv in Excel.
2. For as many rows as you like, type pass or fail in the your_verdict column.
3. Save it (keep it as CSV) and run:

    python eval/agreement.py results/<run folder>/marking_sheet.csv

Rows you left blank are skipped.
"""

import csv
import json
import sys
from pathlib import Path


def read_rows(path: Path) -> list[dict]:
    # Excel may save as UTF-8 or as the Windows default, depending on the "Save as" type.
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            with path.open(newline="", encoding=encoding) as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    raise SystemExit(f"Couldn't read {path}: save it from Excel as 'CSV UTF-8'.")


def main() -> None:
    rows = [
        r for r in read_rows(Path(sys.argv[1]))
        if r["your_verdict"].strip().lower() in ("pass", "fail")
    ]
    if not rows:
        raise SystemExit("No rows marked yet: type pass or fail in the your_verdict column.")

    # If eval/judge.py has graded this run, see how the AI judge does against you too.
    judge_path = Path(sys.argv[1]).parent / "judge.jsonl"
    if judge_path.exists():
        judge = {}
        for line in judge_path.read_text(encoding="utf-8").splitlines():
            j = json.loads(line)
            judge[(j["id"], str(j["repeat"]))] = j["verdict"]
        judged = [r for r in rows if judge.get((r["id"], r["run"])) in ("pass", "fail")]
        if judged:
            hits = sum(judge[(r["id"], r["run"])] == r["your_verdict"].strip().lower() for r in judged)
            print(f"The AI judge agreed with you on {hits} of {len(judged)} ({hits / len(judged):.0%}).")

    agree = [r for r in rows if r["your_verdict"].strip().lower() == r["scorer_verdict"]]
    too_strict = [r for r in rows if r["your_verdict"].strip().lower() == "pass" and r["scorer_verdict"] == "fail"]
    too_lenient = [r for r in rows if r["your_verdict"].strip().lower() == "fail" and r["scorer_verdict"] == "pass"]

    print(f"You marked {len(rows)} answers. The rule-based scorer agreed with you on {len(agree)} ({len(agree) / len(rows):.0%}).")
    print(f"- Scorer too strict (you said pass, it said fail): {len(too_strict)}")
    print(f"- Scorer too lenient (you said fail, it said pass): {len(too_lenient)}")
    print("  Too lenient is the worse kind: a bad answer the score would hide.")
    for label, group in (("Too strict", too_strict), ("Too lenient", too_lenient)):
        for r in group:
            note = f" Your note: {r['your_notes']}" if r.get("your_notes", "").strip() else ""
            print(f"\n[{label}] {r['id']} run {r['run']}: {r['question']}")
            print(f"  Scorer said: {r['scorer_reasons'] or 'pass'}.{note}")


if __name__ == "__main__":
    main()
