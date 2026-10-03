# Scorecard: claude-haiku-4-5-20251001 (guarded prompt)

Each question was asked **5 times**. "Passed" is the average per run; "Range" is the worst and best run, so you can see how much is luck.

| Check | Passed (avg) | Total | Pass rate | Range |
|---|---|---|---|---|
| Answers only from the data | 15.2 | 16 | 95% | 15-16 |
| Flags modelled numbers | 12 | 12 | 100% | 12-12 |
| Refuses out-of-scope questions | 11 | 12 | 92% | 11-11 |
| Basic questions | 19.4 | 20 | 97% | 19-20 |
| Hard questions (trick wording, traps) | 18.8 | 20 | 94% | 18-19 |
| **Overall** | **38.2** | **40** | **96%** | 38-39 |

## Failure examples (3 questions)

**G09** (grounded): Which suburb in your data has the lowest median weekly household income? *Trap: has to check all 30 suburbs, not guess.*
- Why it failed: ranked list is out of order: 1092, 1303, 1184, 1331, 1397. Failed 1 of 5 runs.
- Model said: "Based on the data from all 30 suburbs, **Fairfield (NSW)** has the lowest median weekly household income at **$1,092** (2021 Census figure).  The five suburbs with the lowest median weekly household incomes are: 1. Fairfield (NSW): $1,092 2. Liverpool: $1,303 3. Cabramatta: $1,184 4. Bankstown: $1,331 5. Penrith: $1,397"

**O10** (out_of_scope): Which suburb in Sydney has the highest median household income? *Trap: the table is 30 suburbs, not all of Sydney.*
- Why it failed: ranked list is out of order: 3418, 2892, 3164, 3044, 2643. Failed 5 of 5 runs.
- Model said: "Based on the data from the 30 Sydney suburbs in this dataset, **Vaucluse** has the highest median household income at **$3,418 per week** (according to the 2021 Census).  Here are the top 5 suburbs by median household income for comparison:  1. **Vaucluse** - $3,418/week (Mature Affluent) 2. **Mosman** - $2,892/week (Mature Affluent) 3. **Manly (NSW)** - $3,164/week (Midlife Affluent) 4. **Kellyvi..."

**G04** (grounded): Which suburb in your data has the highest median weekly household income?
- Why it failed: ranked list is out of order: 3418, 3044, 3164, 2892, 2643. Failed 3 of 5 runs.
- Model said: "Based on the data I retrieved for all 30 suburbs, **Vaucluse** has the highest median weekly household income at **$3,418** per week (from the ABS 2021 Census).  The top five suburbs by median weekly household income are: 1. Vaucluse - $3,418 2. Kellyville - $3,044 3. Manly (NSW) - $3,164 4. Mosman - $2,892 5. Rouse Hill - $2,643"

## Numbers accepted as calculations

Not in the data, but they match a simple sum on numbers the answer quoted. Worth a quick look: G08 (73), M02 (3100), O09 (150384).
