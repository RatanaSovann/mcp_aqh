"""Score model answers against the 20-question eval set.

Three checks, one per question category:
  grounded      - the right numbers/names appear, the model looked the data up
                  (called the tool), and no number appears that isn't in the
                  data or worked out from it (no made-up figures).
  modelled      - same as grounded, AND the answer says the 2026 figure is an
                  estimate ("modelled", "estimate", "projected", ...).
  out_of_scope  - the answer says the data doesn't cover it, and doesn't
                  invent a number.

"Worked out from it" means simple sums on numbers the answer itself quotes from
the data: rounding, a difference, a total, a percentage, or a weekly/monthly/yearly switch. They
are listed as "calculated" so you can check them, but don't fail the answer.

Run:  python eval/score.py results/<run folder>/run.jsonl
Writes scorecard.md and marking_sheet.csv next to the input file.
"""

import csv
import json
import re
import sys
from itertools import permutations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = {
    q["id"]: q for q in json.loads((ROOT / "eval" / "questions.json").read_text(encoding="utf-8"))
}

FLAG_RE = re.compile(
    r"modell?ed|estimat|\best\.|project(ed|ion)|forecast|not an? (actual|real)? ?count|assum",
    re.I,
)
REFUSAL_RE = re.compile(
    r"(not|isn't|is not|aren't|are not) (available|included|covered|part of|in (the|this|my))"
    r"|(doesn't|does not|don't|do not|won't|will not) (include|contain|have|cover|hold|provide)"
    r"|no (data|information|figures?)"
    r"|(can't|cannot|unable to|not able to) (provide|answer|tell|find|give|say)"
    r"|outside (the|this|my)|only (covers|contains|includes|has)"
    r"|\b30 (sydney )?suburbs\b",  # scoping a "whole of Sydney" question to the table
    re.I,
)
# A numbered list line with a dollar value, e.g. "2. **Manly** - $3,164/week".
RANKED_LINE_RE = re.compile(r"^\s*\d+\.\s.*?\$([\d,]+)", re.M)
NUMBER_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")
SMALL_NUMBERS = {float(n) for n in range(0, 11)}  # small counts like "3 suburbs"


def _numbers(text: str) -> set[float]:
    out = set()
    for m in NUMBER_RE.findall(text):
        try:
            out.add(float(m.replace(",", "")))
        except ValueError:
            pass
    return out


def _allowed_numbers() -> set[float]:
    """Every number the model could legitimately quote."""
    allowed: set[float] = set()
    with (ROOT / "data" / "segments.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for v in row.values():
                allowed.update(_numbers(v))
    allowed.update(_numbers((ROOT / "data" / "columns.json").read_text(encoding="utf-8")))
    allowed.update({2021.0, 2026.0, 30.0, 2.0})  # Census year, model year, row count, "G02"
    return allowed | SMALL_NUMBERS


ALLOWED = _allowed_numbers()


def _modelled_numbers() -> set[float]:
    """Values of the modelled column: quoting one anywhere means flagging it."""
    with (ROOT / "data" / "segments.csv").open(newline="", encoding="utf-8") as f:
        return {float(row["est_population_2026"]) for row in csv.DictReader(f)}


MODELLED = _modelled_numbers()


def _calculations(quoted: set[float]) -> set[float]:
    """Results of simple sums on the data numbers an answer quotes."""
    base = [n for n in quoted if n not in SMALL_NUMBERS and n not in (2021.0, 2026.0)]
    out = set(base)  # with _close, this lets "about 30,000" stand for 30,070
    for a in base:
        # weekly/monthly <-> yearly, and weekly <-> monthly
        out.update({a * 52, a * 12, a / 52, a / 12, a * 52 / 12, a * 12 / 52})
    for a, b in permutations(base, 2):
        out.update({a - b, a + b, a / b * 100, (a - b) / b * 100})
    return out


def _close(n: float, targets: set[float]) -> bool:
    # Within 1% (or 0.5), so rounded figures like "about 3,100" for 3,129 count.
    return any(abs(n - t) <= max(0.5, 0.01 * abs(t)) for t in targets)


def score_answer(qid: str, answer: str, tool_calls: list | None = None) -> dict:
    """Score one answer. tool_calls=None means calls weren't recorded: skip that check."""
    q = QUESTIONS[qid]
    found = _numbers(answer)
    allowed = ALLOWED | _numbers(q["question"]) | {float(n) for n in q.get("allow_numbers", [])}
    not_quoted = found - allowed
    sums = _calculations(found & allowed)
    calculated = sorted(n for n in not_quoted if _close(n, sums))
    unsupported = sorted(n for n in not_quoted if n not in calculated)

    reasons = []
    for n in q.get("expect_numbers", []):
        if float(n) not in found:
            reasons.append(f"missing expected number {n}")
    any_of = q.get("expect_any_numbers", [])
    if any_of and not found & {float(n) for n in any_of}:
        reasons.append(f"missing any of the expected numbers {', '.join(map(str, any_of))}")
    for t in q.get("expect_text", []):
        if t.lower() not in answer.lower():
            reasons.append(f"missing expected text '{t}'")
    if unsupported:
        reasons.append(f"number(s) not in the data: {', '.join(f'{n:g}' for n in unsupported)}")
    ranked = [float(v.replace(",", "")) for v in RANKED_LINE_RE.findall(answer)]
    if len(ranked) >= 3 and ranked not in (sorted(ranked), sorted(ranked, reverse=True)):
        reasons.append(f"ranked list is out of order: {', '.join(f'{n:g}' for n in ranked)}")
    if q["category"] != "out_of_scope" and tool_calls is not None and not tool_calls:
        reasons.append("answered without looking up the data (no tool call)")

    if q["category"] == "modelled" and not FLAG_RE.search(answer):
        reasons.append("did not flag the 2026 figure as modelled")
    elif found & MODELLED and not FLAG_RE.search(answer):
        reasons.append("quoted a 2026 estimate without saying it's modelled")
    if q["category"] == "out_of_scope" and not REFUSAL_RE.search(answer):
        reasons.append("did not say the data doesn't cover this")

    return {
        "id": qid, "category": q["category"], "level": q.get("level", "basic"),
        "passed": not reasons, "reasons": reasons,
        "calculated": [f"{n:g}" for n in calculated],
    }


def load_scored(run_path: Path) -> list[dict]:
    records = [
        json.loads(line)
        for line in run_path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    return [
        {**r, **score_answer(r["id"], r["answer"], r.get("tool_calls")), "repeat": r.get("repeat", 1)}
        for r in records
    ]


LABELS = {
    "grounded": "Answers only from the data",
    "modelled": "Flags modelled numbers",
    "out_of_scope": "Refuses out-of-scope questions",
}


LEVELS = {"basic": "Basic questions", "hard": "Hard questions (trick wording, traps)"}


def tally(scored: list[dict]) -> dict:
    """Passes per group per repeat: {category, level or 'overall': (avg, min, max, total questions)}."""
    repeats = sorted({s["repeat"] for s in scored})
    out = {}
    for group in [*LABELS, *LEVELS, "overall"]:
        rows = [s for s in scored if group in ("overall", s["category"], s["level"])]
        if not rows:
            continue
        per_run = [sum(s["passed"] for s in rows if s["repeat"] == k) for k in repeats]
        out[group] = (sum(per_run) / len(per_run), min(per_run), max(per_run), len(rows) // len(repeats))
    return out


def _fmt(avg: float) -> str:
    return f"{avg:g}" if avg == int(avg) else f"{avg:.1f}"


def build_scorecard(run_path: Path) -> str:
    scored = load_scored(run_path)
    model, prompt = scored[0].get("model", "?"), scored[0].get("prompt", "?")
    n_runs = len({s["repeat"] for s in scored})
    counts = tally(scored)

    lines = [f"# Scorecard: {model} ({prompt} prompt)", ""]
    if n_runs > 1:
        lines += [
            f"Each question was asked **{n_runs} times**. \"Passed\" is the average per run; "
            "\"Range\" is the worst and best run, so you can see how much is luck.",
            "",
            "| Check | Passed (avg) | Total | Pass rate | Range |",
            "|---|---|---|---|---|",
        ]
    else:
        lines += ["| Check | Passed | Total | Pass rate |", "|---|---|---|---|"]
    levels = list(LEVELS.items()) if "hard" in counts else []
    for cat, label in [*LABELS.items(), *levels, ("overall", "**Overall**")]:
        if cat not in counts:  # e.g. a partial run with no modelled questions
            continue
        avg, lo, hi, total = counts[cat]
        bold = "**" if cat == "overall" else ""
        row = f"| {label} | {bold}{_fmt(avg)}{bold} | {bold}{total}{bold} | {bold}{avg / total:.0%}{bold} |"
        lines.append(row + (f" {lo}-{hi} |" if n_runs > 1 else ""))

    # One example per question that failed at least once.
    failed_ids = list(dict.fromkeys(s["id"] for s in scored if not s["passed"]))
    lines += ["", f"## Failure examples ({len(failed_ids)} questions)", ""]
    if not failed_ids:
        lines += ["None.", ""]
    for qid in failed_ids:
        runs = [s for s in scored if s["id"] == qid]
        s = next(r for r in runs if not r["passed"])
        answer = s["answer"].strip().replace("\n", " ")
        if len(answer) > 400:
            answer = answer[:400] + "..."
        times = f" Failed {sum(not r['passed'] for r in runs)} of {len(runs)} runs." if n_runs > 1 else ""
        trap = f" *Trap: {QUESTIONS[qid]['trap']}.*" if "trap" in QUESTIONS[qid] else ""
        lines += [
            f"**{qid}** ({s['category']}): {QUESTIONS[qid]['question']}{trap}",
            f"- Why it failed: {'; '.join(s['reasons'])}.{times}",
            f"- Model said: \"{answer}\"",
            "",
        ]

    calc = sorted({(s["id"], n) for s in scored for n in s["calculated"]})
    if calc:
        lines += [
            "## Numbers accepted as calculations",
            "",
            "Not in the data, but they match a simple sum on numbers the answer quoted. "
            "Worth a quick look: " + ", ".join(f"{qid} ({n})" for qid, n in calc) + ".",
            "",
        ]
    return "\n".join(lines).rstrip()


SHEET_COLUMNS = [
    "id", "run", "category", "question", "model_answer", "tools_called",
    "scorer_verdict", "scorer_reasons", "calculated_numbers", "your_verdict", "your_notes",
]


def write_marking_sheet(run_path: Path, out_path: Path) -> None:
    """A CSV to mark answers by hand (pass/fail in your_verdict), for eval/agreement.py."""
    # utf-8-sig so Excel opens it with the right characters.
    with out_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(SHEET_COLUMNS)
        for s in load_scored(run_path):
            w.writerow([
                s["id"], s["repeat"], s["category"], QUESTIONS[s["id"]]["question"],
                s["answer"].strip(), ", ".join(c["tool"] for c in s.get("tool_calls") or []),
                "pass" if s["passed"] else "fail", "; ".join(s["reasons"]),
                ", ".join(s["calculated"]), "", "",
            ])


def main() -> None:
    run_path = Path(sys.argv[1])
    card = build_scorecard(run_path)
    (run_path.parent / "scorecard.md").write_text(card + "\n", encoding="utf-8")
    write_marking_sheet(run_path, run_path.parent / "marking_sheet.csv")
    print(card)
    print(f"\nSaved scorecard.md and marking_sheet.csv in {run_path.parent}")


if __name__ == "__main__":
    main()
