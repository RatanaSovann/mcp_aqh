# Eval results: Claude Haiku 4.5, 2026-10-03

Run in a Claude Code cloud session with `python eval/run_eval.py --prompt plain` and `--prompt guarded` (CLI backend, `claude -p`, MCP server as the only tool). Each run has its own folder with `run.jsonl` (full answers) and `scorecard.md` (table plus failure examples). [`history.md`](history.md) has one row per run.

| Check | Plain prompt | Guarded prompt |
|---|---|---|
| Answers only from the data (8) | 7 (88%) | 7 (88%) |
| Flags modelled numbers (6) | 4 (67%) | 5 (83%) |
| Refuses out-of-scope questions (6) | 6 (100%) | 6 (100%) |
| **Overall (20)** | **17 (85%)** | **18 (90%)** |

## What the failures have in common

Every failure is the model doing **correct arithmetic** on numbers from the tool. The scorer is strict: any number not in the data counts as made up.

| Question | Prompt | Number flagged | Where it came from |
|---|---|---|---|
| G08 Liverpool vs Kellyville mortgage | both | 73 (%) | (3,000 - 1,733) / 1,733 = 73% |
| M01 Bondi population 2026 | plain | 639 | 11,050 (modelled) - 10,411 (2021) |
| M02 Blacktown population 2026 | plain | 3,130 | 54,090 (modelled) - 50,961 (2021) |
| M02 Blacktown population 2026 | guarded | 3,100 | same, rounded |

So with this data and these questions Haiku 4.5 made up **no** facts, flagged every modelled number it gave, and refused all 6 out-of-scope questions. The plain-prompt M01/M02 answers did say "estimate", so they would pass the modelled check on their own; they fail only on the derived growth figure.

## Caveats

- The CLI backend runs the model through Claude Code, which adds a small built-in system prompt around ours, so "plain" is close to, but not exactly, a bare model.
- One run per prompt. Answers vary a little run to run, so treat 85% vs 90% as the same result.
- O03 (Melbourne suburb) was refused without calling the tool, in both runs. That is correct: the tool only covers Sydney.
