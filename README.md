# MCP Answer Quality Harness

A tiny local **MCP server** that serves a small Sydney suburb table built from the ABS 2021 Census, plus a **40-question eval** that checks three things about a model's answers:

1. **Grounded**: does it answer only from the data (no made-up numbers)?
2. **Modelled**: when a number is an estimate, does it say so?
3. **Out of scope**: when the data doesn't cover a question, does it say "I don't have that" instead of guessing?

Every answer is graded twice, by fixed **rules** and by an **AI judge**. A **review queue** then sends disagreements to a person.

> **MCP in one line:** a standard "plug" that lets an AI model call your tools and data, like a USB port for AI.

## Headline results

Claude Haiku 4.5, 40 questions, each asked 5 times per prompt (600 answers in total):

| Prompt | AI judge pass rate | Rules score (avg of 5 runs) |
|---|---|---|
| `plain` | 80% | 37.2 / 40 |
| `guarded` (v1) | 92% | 38.2 / 40 |
| `guarded_v2` | 94% | 39.2 / 40 |

- Haiku almost never invents numbers. The trap questions are where it slips: inventing a 2030 forecast, swapping Newtown NSW for Newtown Victoria, or giving an opinion on safety.
- v2 fixed v1's one systematic error, rankings out of order (9 answers → 0). Its remaining weak spot is adding explanations that aren't in the data ("reflects higher property values").
- Rules and judge agree on 84–96% of answers. Rules are free and catch made-up numbers. The judge catches reasoning mistakes and outside facts, but is sometimes too strict.

## Documents

| Document | What it is |
|---|---|
| [`results/SUMMARY.md`](results/SUMMARY.md) | Full test and results report: set-up, grading, results per prompt, failure cases, rules vs judge, scorer fixes, suggested prompt v3, limits |
| [`docs/CASE_STUDY.md`](docs/CASE_STUDY.md) | Case study: the business problem, method, results, the proposed "both, smart" set-up with cost estimates, how it could fit a geodemographic data product, value and limitations |
| [`results/history.md`](results/history.md) | One row per eval run, so you can see scores change over time |

## Quick start

```bash
pip install -r requirements.txt
python -m pytest -q                                        # checks server, scorer and routing; no API key needed
python eval/run_eval.py --prompt guarded_v2 --repeats 5    # ask Haiku 4.5 all 40 questions, 5 times each
python eval/judge.py results/<run folder>/run.jsonl        # AI judge + rules-vs-judge report
python eval/review_queue.py results/<run folder>/run.jsonl # what a person should review, disagreements first
```

On Windows, create a virtual environment first and use its Python:

```bash
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python eval\run_eval.py --prompt guarded_v2 --repeats 5
```

By default the eval runs the model through the **Claude Code CLI** (`claude -p`), using the login Claude Code already has, so no API key is needed. To use an API key instead, set `ANTHROPIC_API_KEY` and add `--backend sdk`.

Options for `run_eval.py`: `--prompt plain|guarded|guarded_v2` (default `plain`), `--repeats N` (default 1), `--model <id>` (default `claude-haiku-4-5-20251001`), `--out-dir <folder>` (default `results/`, or set `EVAL_RESULTS_DIR`). `judge.py` takes `--model` for the judge (default `claude-sonnet-5-5`).

## How it works

```
question ──► model + MCP server (only tool) ──► answer
                                                  │
                         rules (score.py) ◄───────┤  every answer, free
                         AI judge (judge.py) ◄────┘  risky answers only (review_queue.py)
                                   │
                    disagreements and failures ──► a person (review_queue.csv)
```

## The data (`data/`)

| File | What it is |
|---|---|
| `census_g02_raw.csv` | 30 Sydney suburbs, ABS 2021 Census *Selected Medians and Averages* (the G02 table): people, median age, incomes, mortgage, rent, household size |
| `segments.csv` | The same rows plus a **segment** label and one **modelled** column |
| `columns.json` | What each column means and its source: `census_2021`, `derived` or `modelled` |

- **Segment** = lifestage × wealth, a simplified geodemographic segment.
  - Lifestage from median age: Young (<35), Midlife (35-39), Mature (40+).
  - Wealth from median weekly household income: Budget (<$1,600), Comfortable ($1,600-$2,399), Affluent ($2,400+).
- **`est_population_2026` is modelled on purpose.** It is the 2021 count grown at an assumed 1.2% a year. It's the "trap" column: a good answer must say it's an estimate.

**Where the numbers came from:** each row was read from that suburb's ABS QuickStats page (Suburbs and Localities level, e.g. `abs.gov.au/census/find-census-data/quickstats/2021/SAL12749` for Mosman). The ABS download site was blocked from the build sandbox, so the values were transcribed page by page rather than taken from the DataPack CSV. Worth spot-checking a few against QuickStats; the SAL codes are in the first column. Rebuild with `python scripts/build_segments.py`.

## The server (`server.py`)

Four tools: `list_suburbs`, `get_suburb`, `find_suburbs_by_segment`, `describe_columns`. Every value comes back with its source, e.g.

```json
"est_population_2026": {"value": 11050, "source": "modelled"}
```

To use it in Claude Desktop, add it to `claude_desktop_config.json`:

```json
{"mcpServers": {"sydney-segments": {"command": "python", "args": ["/full/path/to/server.py"]}}}
```

## The eval (`eval/`)

| File | What it does |
|---|---|
| `questions.json` | 40 questions: 16 grounded, 12 modelled, 12 out of scope. Half are basic; half are marked `"level": "hard"` and set a trap (a wrong premise, a wrong number from the user, a tie, near-duplicate columns, a same-named place in another state, a missing year, an opinion question, a half-answerable question), described in each one's `trap` field |
| `run_eval.py` | Gives the model the server as its only tool and asks every question (`--repeats` times). Holds the three prompts in `PROMPTS` |
| `score.py` | Rule-based scorer (below). Writes `scorecard.md` and `marking_sheet.csv` |
| `judge.py` | AI judge: reads the whole table, the question, the answer key and the answer; returns pass/fail with a reason. Writes `judge.jsonl` and `judge_report.md` (where it and the rules disagree) |
| `review_queue.py` | The "both, smart" set-up: rules on every answer; the judge only on rule failures, lists and rankings, refusals and explanations, plus a 5% sample; a person reviews what's flagged, disagreements first (`review_queue.csv`) |
| `agreement.py` | Checks the checkers. Type `pass` or `fail` in a run's `marking_sheet.csv`, then run it on that file to see how often the rules and the judge agree with you |

**The prompts:**
- `plain`: what a typical connector user gets.
- `guarded` (v1): adds "answer only from the tool, flag modelled values, say when data is missing".
- `guarded_v2`: adds "sort and check rankings, add no figures nobody asked for", to fix the gaps the hard questions found in v1.

**Rules in `score.py`:**
- **All questions:**
  - The expected numbers and names appear.
  - Every number is in the data, in the question, or simple maths on numbers the answer quoted (rounding, difference, total, percentage, weekly ↔ monthly ↔ yearly). These calculated numbers pass but are listed on the scorecard.
  - Any answer that quotes a 2026 estimate must say it's modelled.
  - A numbered ranking must be in order.
- **Grounded and modelled questions:** the model must have called the tool.
- **Modelled questions:** the answer must say "estimate", "modelled", "projected" or similar.
- **Out-of-scope questions:** the answer must say something like "not available" or "only covers", and invent no numbers.

**Known limits:**
- The rules match keywords and numbers, so they miss wrong reasoning and outside facts. They can also fail an unusual but correct refusal.
- The judge is a model, so it is sometimes too strict and can vary.
- Mark some answers yourself with `agreement.py` before trusting either grader.

## Each run's folder (`results/<date>_<time>_<model>_<prompt>[_x<repeats>]/`)

| File | What's in it |
|---|---|
| `run.jsonl` | Every answer and the tool calls behind it |
| `scorecard.md` | Rules results: pass rates, range across repeats, one failure example per question |
| `marking_sheet.csv` | Every answer with the rules' verdict, for marking by hand in Excel |
| `judge.jsonl`, `judge_report.md` | AI judge verdicts and the rules-vs-judge comparison (after `judge.py`) |
| `review_queue.csv` | Answers for a person to review (after `review_queue.py`) |

## Troubleshooting

- **`No module named 'mcp.server.fastmcp'`**: you have `mcp` 2.x, which renamed the class the server uses. `requirements.txt` pins `mcp<2`, so reinstall from it.
- **A run crashes with `UnicodeDecodeError` on Windows**: you have an old copy of `run_eval.py`. The current one reads Claude's output as UTF-8.
- **Nothing prints for a while**: runs only print once every answer is in. 200 answers take several minutes.
