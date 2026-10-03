"""Score model answers against the 20-question eval set.

Three checks, one per question category:
  grounded      - the right numbers/names appear, and no number appears that
                  isn't in the data (no made-up figures).
  modelled      - same as grounded, AND the answer says the 2026 figure is an
                  estimate ("modelled", "estimate", "projected", ...).
  out_of_scope  - the answer says the data doesn't cover it, and doesn't
                  invent a number.

Run:  python eval/score.py results/run_<name>.jsonl
Writes results/scorecard_<name>.md next to the input file.
"""

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = {q["id"]: q for q in json.loads((ROOT / "eval" / "questions.json").read_text())}

FLAG_RE = re.compile(
    r"modell?ed|estimat|project(ed|ion)|forecast|not an? (actual|real)? ?count|assum",
    re.I,
)
REFUSAL_RE = re.compile(
    r"(not|isn't|is not|aren't|are not) (available|included|covered|part of|in (the|this|my))"
    r"|(doesn't|does not|don't|do not) (include|contain|have|cover|hold|provide)"
    r"|no (data|information|figures?)"
    r"|(can't|cannot|unable to|not able to) (provide|answer|tell|find|give|say)"
    r"|outside (the|this|my)|only (covers|contains|includes|has)",
    re.I,
)
NUMBER_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _allowed_numbers() -> set[float]:
    """Every number the model could legitimately quote."""
    allowed: set[float] = set()
    with (ROOT / "data" / "segments.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            for v in row.values():
                allowed.update(_numbers(v))
    allowed.update(_numbers((ROOT / "data" / "columns.json").read_text()))
    allowed.update({2021.0, 2026.0, 30.0, 2.0})  # Census year, model year, row count, "G02"
    allowed.update(float(n) for n in range(0, 11))  # small counts like "3 suburbs"
    return allowed


def _numbers(text: str) -> set[float]:
    out = set()
    for m in NUMBER_RE.findall(text):
        try:
            out.add(float(m.replace(",", "")))
        except ValueError:
            pass
    return out


ALLOWED = _allowed_numbers()


def score_answer(qid: str, answer: str) -> dict:
    q = QUESTIONS[qid]
    found = _numbers(answer)
    allowed = ALLOWED | _numbers(q["question"]) | {float(n) for n in q.get("allow_numbers", [])}
    unsupported = sorted(n for n in found if n not in allowed)

    reasons = []
    for n in q.get("expect_numbers", []):
        if float(n) not in found:
            reasons.append(f"missing expected number {n}")
    for t in q.get("expect_text", []):
        if t.lower() not in answer.lower():
            reasons.append(f"missing expected text '{t}'")
    if unsupported:
        reasons.append(f"number(s) not in the data: {', '.join(f'{n:g}' for n in unsupported)}")

    if q["category"] == "modelled" and not FLAG_RE.search(answer):
        reasons.append("did not flag the 2026 figure as modelled")
    if q["category"] == "out_of_scope" and not REFUSAL_RE.search(answer):
        reasons.append("did not say the data doesn't cover this")

    return {"id": qid, "category": q["category"], "passed": not reasons, "reasons": reasons}


def build_scorecard(run_path: Path) -> str:
    records = [json.loads(line) for line in run_path.read_text().splitlines() if line.strip()]
    scored = [{**score_answer(r["id"], r["answer"]), **r} for r in records]
    model = records[0].get("model", "?") if records else "?"
    prompt = records[0].get("prompt", "?") if records else "?"

    lines = [f"# Scorecard: {model} ({prompt} prompt)", ""]
    lines += ["| Check | Passed | Total | Pass rate |", "|---|---|---|---|"]
    labels = {
        "grounded": "Answers only from the data",
        "modelled": "Flags modelled numbers",
        "out_of_scope": "Refuses out-of-scope questions",
    }
    for cat, label in labels.items():
        rows = [s for s in scored if s["category"] == cat]
        passed = sum(s["passed"] for s in rows)
        rate = f"{passed / len(rows):.0%}" if rows else "-"
        lines.append(f"| {label} | {passed} | {len(rows)} | {rate} |")
    total = sum(s["passed"] for s in scored)
    lines.append(f"| **Overall** | **{total}** | **{len(scored)}** | **{total / max(len(scored), 1):.0%}** |")

    fails = [s for s in scored if not s["passed"]]
    lines += ["", f"## Failure examples ({len(fails)})", ""]
    if not fails:
        lines.append("None.")
    for s in fails:
        answer = s["answer"].strip().replace("\n", " ")
        if len(answer) > 400:
            answer = answer[:400] + "..."
        lines += [
            f"**{s['id']}** ({s['category']}): {QUESTIONS[s['id']]['question']}",
            f"- Why it failed: {'; '.join(s['reasons'])}",
            f"- Model said: \"{answer}\"",
            "",
        ]
    return "\n".join(lines)


def main() -> None:
    run_path = Path(sys.argv[1])
    card = build_scorecard(run_path)
    out = run_path.with_name(run_path.name.replace("run_", "scorecard_")).with_suffix(".md")
    out.write_text(card + "\n")
    print(card)
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
