"""A second opinion on every answer: an AI judge, compared with the rule-based scorer.

The rules (score.py) check words and numbers. The judge is a stronger Claude
model that reads the whole data table, the question, the answer key and the
answer, and decides pass or fail with a one-line reason. It can catch wrong
reasoning that rules can't, but it can also be wrong, so neither is "the truth":
the report shows where they disagree, and agreement.py checks both against your
own marks.

Run:  python eval/judge.py results/<run folder>/run.jsonl
      python eval/judge.py <run.jsonl> --model claude-opus-5-5
Writes judge.jsonl and judge_report.md next to the input file.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_eval import CLI_ENV_DROP, ROOT  # noqa: E402
from score import LABELS, QUESTIONS, load_scored  # noqa: E402

RUBRIC = """You grade answers from an AI assistant. The assistant's only source was \
a tool serving the table below: 30 Sydney suburbs from the ABS 2021 Census, a \
derived segment label, and one modelled column (est_population_2026).

Grade by question type:
- grounded: the answer must answer the question correctly, and every fact and \
number must come from the table or be correct arithmetic on it.
- modelled: as grounded, and every est_population_2026 value must be clearly \
described as a modelled estimate, not a Census count.
- out_of_scope: the table can't (fully) answer this. The answer must say so \
plainly. It may share related figures from the table, and may answer a part \
that the table does cover, but must not guess, extrapolate, give opinions as \
facts, or use outside knowledge.

For every type, fail: a wrong number, a wrong order in a ranking or list, \
wrong arithmetic, a different place silently swapped for the one asked about, \
or outside facts presented as data. Don't judge style or length.

Reply with JSON only: {"verdict": "pass" or "fail", "reason": "<one sentence>"}

The table (CSV):
<<DATA>>

What each column means and its source:
<<COLUMNS>>"""


def judge_prompt(question_id: str, answer: str) -> str:
    q = QUESTIONS[question_id]
    key = []
    if q.get("expect_numbers"):
        key.append("should include the numbers " + ", ".join(map(str, q["expect_numbers"])))
    if q.get("expect_any_numbers"):
        key.append("should include at least one of " + ", ".join(map(str, q["expect_any_numbers"])))
    if q.get("expect_text"):
        key.append("should mention " + ", ".join(q["expect_text"]))
    if q.get("trap"):
        key.append(f"the trap in this question: {q['trap']}")
    return (
        f"Question type: {q['category']}\n"
        f"Question: {q['question']}\n"
        f"Answer key: {'; '.join(key) or 'none (out of scope)'}\n\n"
        f"Answer to grade:\n{answer}"
    )


def ask_judge(model: str, system: str, prompt: str, workdir: str) -> dict:
    cmd = [
        "claude", "-p", prompt,
        "--model", model,
        "--system-prompt", system,
        "--tools", "",
        "--strict-mcp-config",
        "--setting-sources", "",
        "--no-session-persistence",
        "--output-format", "json",
    ]
    env = {k: v for k, v in os.environ.items() if k not in CLI_ENV_DROP}
    env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
    proc = subprocess.run(
        cmd, cwd=workdir, env=env, stdin=subprocess.DEVNULL,
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300,
    )
    try:
        text = json.loads(proc.stdout)["result"]
        verdict = json.loads(re.search(r"\{.*\}", text, re.S).group(0))
        if verdict.get("verdict") in ("pass", "fail"):
            return {"verdict": verdict["verdict"], "reason": verdict.get("reason", "")}
    except (json.JSONDecodeError, KeyError, AttributeError, TypeError):
        pass
    return {"verdict": "error", "reason": (proc.stdout or proc.stderr).strip()[-200:]}


def build_report(run_path: Path, judged: list[dict], judge_model: str) -> str:
    scored = {(s["id"], s["repeat"]): s for s in load_scored(run_path)}
    rows = [
        {**j, "rules": "pass" if scored[(j["id"], j["repeat"])]["passed"] else "fail",
         "rule_reasons": "; ".join(scored[(j["id"], j["repeat"])]["reasons"])}
        for j in judged if j["verdict"] != "error"
    ]
    errors = len(judged) - len(rows)
    first = next(iter(scored.values()))

    def rate(rs, key):
        return f"{sum(r[key] == 'pass' for r in rs) / len(rs):.0%}" if rs else "-"

    lines = [
        f"# Rules vs AI judge: {first['model']} ({first['prompt']} prompt)",
        "",
        f"Judge: {judge_model}. {len(rows)} answers graded" + (f", {errors} judge errors skipped." if errors else "."),
        "",
        "| Check | Rules pass rate | Judge pass rate | They agree |",
        "|---|---|---|---|",
    ]
    for cat, label in [*LABELS.items(), ("overall", "**Overall**")]:
        rs = [r for r in rows if cat == "overall" or QUESTIONS[r["id"]]["category"] == cat]
        agree = f"{sum(r['rules'] == r['verdict'] for r in rs) / len(rs):.0%}" if rs else "-"
        lines.append(f"| {label} | {rate(rs, 'rules')} | {rate(rs, 'verdict')} | {agree} |")

    for title, rules, judge, note in (
        ("Rules passed, judge failed", "pass", "fail",
         "Mistakes the rules may have missed (or the judge being too strict)."),
        ("Rules failed, judge passed", "fail", "pass",
         "Answers the rules may have failed unfairly (or the judge being too lenient)."),
    ):
        group = [r for r in rows if r["rules"] == rules and r["verdict"] == judge]
        lines += ["", f"## {title} ({len(group)})", "", note, ""]
        for r in group:
            why = f" Rules said: {r['rule_reasons']}." if r["rule_reasons"] else ""
            lines.append(f"- **{r['id']}** run {r['repeat']}: {QUESTIONS[r['id']]['question']} "
                         f"Judge said: {r['reason']}{why}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_path", type=Path)
    parser.add_argument("--model", default="claude-sonnet-5-5")
    args = parser.parse_args()

    system = (
        RUBRIC.replace("<<DATA>>", (ROOT / "data" / "segments.csv").read_text(encoding="utf-8"))
        .replace("<<COLUMNS>>", (ROOT / "data" / "columns.json").read_text(encoding="utf-8"))
    )
    records = [
        json.loads(line)
        for line in args.run_path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    with tempfile.TemporaryDirectory() as workdir:
        with ThreadPoolExecutor(max_workers=4) as pool:
            verdicts = list(pool.map(
                lambda r: ask_judge(args.model, system, judge_prompt(r["id"], r["answer"]), workdir),
                records,
            ))
    judged = [
        {"id": r["id"], "repeat": r.get("repeat", 1), "judge_model": args.model, **v}
        for r, v in zip(records, verdicts)
    ]
    out_dir = args.run_path.parent
    with (out_dir / "judge.jsonl").open("w", encoding="utf-8") as f:
        for j in judged:
            f.write(json.dumps(j) + "\n")
    report = build_report(args.run_path, judged, args.model)
    (out_dir / "judge_report.md").write_text(report + "\n", encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
