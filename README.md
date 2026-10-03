# MCP Answer Quality Harness

A tiny local **MCP server** that serves a small Sydney suburb table built from the ABS 2021 Census, plus a **40-question eval** that checks three things about a model's answers:

1. **Grounded**: does it answer only from the data (no made-up numbers)?
2. **Modelled**: when a number is an estimate, does it say so?
3. **Out of scope**: when the data doesn't cover a question, does it say "I don't have that" instead of guessing?

> **MCP in one line:** a standard "plug" that lets an AI model call your tools and data, like a USB port for AI.

## Quick start

```bash
pip install -r requirements.txt
python -m pytest -q                     # checks the server and scorer, no API key needed
python eval/run_eval.py                 # Claude Haiku 4.5, plain prompt
python eval/run_eval.py --prompt guarded
python eval/run_eval.py --repeats 5     # each question 5 times: average and range
```

By default the eval runs the model through the **Claude Code CLI** (`claude -p`), using the login Claude Code already has. That means it works in a Claude Code cloud session or on a laptop with Claude Code installed, with no API key. To use an API key instead: `export ANTHROPIC_API_KEY=sk-ant-...` and add `--backend sdk`.

Latest results: [`results/SUMMARY.md`](results/SUMMARY.md). Case study (problem, method, results, proposed set-up): [`docs/CASE_STUDY.md`](docs/CASE_STUDY.md).

Each run gets its own folder, `results/<date>_<time>_<model>_<prompt>/`, holding `run.jsonl` (raw answers), `scorecard.md` (the results table with failure examples) and `marking_sheet.csv` (every answer, for marking by hand). Every run also adds one row to `results/history.md`, so you can watch the scores change as the project grows. To save somewhere else, pass `--out-dir <folder>` or set `EVAL_RESULTS_DIR`.

## The data (`data/`)

| File | What it is |
|---|---|
| `census_g02_raw.csv` | 30 Sydney suburbs, ABS 2021 Census *Selected Medians and Averages* (the G02 table): people, median age, incomes, mortgage, rent, household size |
| `segments.csv` | The same rows plus a **segment** label and one **modelled** column |
| `columns.json` | What each column means and its source: `census_2021`, `derived` or `modelled` |

- **Segment** = lifestage x wealth, a mini version of geoTribes-style segments.
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

- `questions.json`: 40 questions: 16 grounded, 12 modelled, 12 out of scope. Half are basic. The other half are marked `"level": "hard"` and each sets a trap (a wrong premise, a near-duplicate column, a tie, a half-answerable question), described in its `trap` field.
- Any answer that quotes a 2026 estimate must say it's modelled, whatever the question.
- `run_eval.py`: gives the model the server as its only tool and runs each question (`--backend cli` or `sdk`).
- `score.py`: rule-based scorer.
  - Grounded: expected numbers/names appear, the model **called the tool**, and **every number in the answer exists in the data** (or in the question), or is a simple sum on numbers the answer quoted (a difference, total, percentage, or weekly to yearly). Those calculated numbers pass but are listed in the scorecard so you can check them.
  - Modelled: same, plus words like "modelled", "estimate" or "projected".
  - Out of scope: a "the data doesn't cover this" phrase, and no invented numbers.
- `agreement.py`: checks the checker. Mark answers yourself in a run's `marking_sheet.csv` (type `pass` or `fail` in `your_verdict`), then run `python eval/agreement.py <that file>` to see how often the scorer agrees with you, and where.
- `judge.py`: a second opinion. An AI judge (Claude Sonnet 5.5 by default) grades every answer of a run with a one-line reason, and `judge_report.md` shows where it and the rules disagree.
- `review_queue.py`: the "both, smart" set-up replayed on a judged run. Rules check every answer, the judge checks only risky ones (rule failures, lists and rankings, refusals, explanations, plus a 5% sample), and `review_queue.csv` lists what a person should review, disagreements first.
- Three prompts: `plain` (what a typical connector user gets), `guarded` (explicit grounding rules) and `guarded_v2` (guarded plus fixes for the gaps the hard questions found), so you can see how much the prompt matters.

**Known scorer limits:** it's keyword and number matching, not a judge model. A made-up number that happens to equal another value in the table (or a sum of quoted ones) slips through, and an unusual refusal phrasing can be marked as a fail. Read the failure examples, and mark some answers yourself with `agreement.py`, before trusting the score.
