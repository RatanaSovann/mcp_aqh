"""Who checks what: rules on every answer, the AI judge on risky ones, a person on disagreements.

This is the "both, smart" set-up a live service would run, replayed on an eval run:

1. Rules (score.py) grade every answer. They are free.
2. The AI judge (judge.py) grades only answers worth a second look:
   - the rules failed it, or
   - it is risky: a list of 3+ items (rankings), a refusal (out-of-scope
     wording), or an explanation ("reflects", "because", "typical", "located"...),
     which is where outside facts and wrong reasoning hide, or
   - a random 5% sample of the rest, to measure what the routing misses.
3. A person reviews every answer the judge or the rules failed, disagreements
   first, in review_queue.csv.

Run after judge.py has graded the run (the judge's verdicts are reused, so this
costs nothing):

    python eval/review_queue.py results/<run folder>/run.jsonl

Writes review_queue.csv next to the input and prints how many judge calls and
human reviews the routing needs, and how many judge-found problems it would catch.
"""

import csv
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score import QUESTIONS, REFUSAL_RE, load_scored  # noqa: E402

EXPLAINS_RE = re.compile(
    r"reflect|because|due to|indicat|suggest|typical|likely|probabl|known for|located|council|region",
    re.I,
)
LIST_ITEM_RE = re.compile(r"^\s*(\d+\.|[-*])\s", re.M)
SAMPLE_RATE = 0.05


def risk_reason(answer: str) -> str:
    """Why an answer is risky enough for the judge, or '' if it isn't."""
    if len(LIST_ITEM_RE.findall(answer)) >= 3:
        return "list or ranking"
    if REFUSAL_RE.search(answer):
        return "refusal"
    if EXPLAINS_RE.search(answer):
        return "explanation"
    return ""


def main() -> None:
    run_path = Path(sys.argv[1])
    judge_path = run_path.parent / "judge.jsonl"
    if not judge_path.exists():
        raise SystemExit(f"Run eval/judge.py on {run_path} first.")
    judge = {}
    for line in judge_path.read_text(encoding="utf-8").splitlines():
        j = json.loads(line)
        judge[(j["id"], j["repeat"])] = j

    rng = random.Random(0)  # same sample every time, so results are repeatable
    rows, judge_calls = [], 0
    judge_fails = caught = 0
    for s in load_scored(run_path):
        j = judge.get((s["id"], s["repeat"]))
        if j is None or j["verdict"] == "error":
            continue
        risk = risk_reason(s["answer"])
        if not s["passed"]:
            route = "rules failed"
        elif risk:
            route = f"risky: {risk}"
        elif rng.random() < SAMPLE_RATE:
            route = "random sample"
        else:
            route = ""
        judged = bool(route)
        judge_calls += judged
        judge_says = j["verdict"] if judged else "not asked"

        judge_fails += j["verdict"] == "fail"
        caught += judged and j["verdict"] == "fail"

        rules_says = "pass" if s["passed"] else "fail"
        if judged and (rules_says == "fail" or judge_says == "fail"):
            rows.append({
                "priority": "1 disagree" if rules_says != judge_says else "2 both fail",
                "id": s["id"], "run": s["repeat"], "question": QUESTIONS[s["id"]]["question"],
                "model_answer": s["answer"].strip(), "why_judged": route,
                "rules": rules_says, "rules_reasons": "; ".join(s["reasons"]),
                "judge": judge_says, "judge_reason": j["reason"],
                "your_verdict": "", "your_notes": "",
            })

    rows.sort(key=lambda r: (r["priority"], r["id"], r["run"]))
    out = run_path.parent / "review_queue.csv"
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["priority"])
        w.writeheader()
        w.writerows(rows)

    total = len([k for k, v in judge.items() if v["verdict"] != "error"])
    print(f"{total} answers. Rules graded all of them.")
    print(f"The judge was asked about {judge_calls} ({judge_calls / total:.0%}).")
    print(f"It would have caught {caught} of the {judge_fails} problems it finds when it reads everything.")
    print(f"A person reviews {len(rows)} ({len(rows) / total:.0%}): "
          f"{sum(r['priority'].startswith('1') for r in rows)} disagreements first, then the rest.")
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
