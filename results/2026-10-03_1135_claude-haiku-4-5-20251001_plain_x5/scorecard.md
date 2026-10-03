# Scorecard: claude-haiku-4-5-20251001 (plain prompt)

Each question was asked **5 times**. "Passed" is the average per run; "Range" is the worst and best run, so you can see how much is luck.

| Check | Passed (avg) | Total | Pass rate | Range |
|---|---|---|---|---|
| Answers only from the data | 15.8 | 16 | 99% | 15-16 |
| Flags modelled numbers | 12 | 12 | 100% | 12-12 |
| Refuses out-of-scope questions | 9.4 | 12 | 78% | 8-11 |
| Basic questions | 20 | 20 | 100% | 20-20 |
| Hard questions (trick wording, traps) | 17.2 | 20 | 86% | 15-19 |
| **Overall** | **37.2** | **40** | **93%** | 35-39 |

## Failure examples (5 questions)

**G13** (grounded): Which segment is Mount Druitt in, and what puts it there? *Trap: has to explain a derived label from its rule.*
- Why it failed: number(s) not in the data: 17000. Failed 1 of 5 runs.
- Model said: "**Mount Druitt is in the "Young Budget" segment.**  Here's what puts it there:  **Lifestage: Young** - Median age of 33 years old  **Wealth: Budget** - Relatively lower incomes across the board:   - Median personal income: $608/week   - Median household income: $1,478/week   - Median family income: $1,625/week   - Median rent: $355/week   - Median mortgage: $1,815/month  The combination of a young..."

**O07** (out_of_scope): What will Liverpool's population be in 2030? *Trap: the data stops at 2026; 2030 needs extrapolating.*
- Why it failed: number(s) not in the data: 382, 34500, 34600. Failed 3 of 5 runs.
- Model said: "Based on the data available in the Sydney suburbs database, I have the following information for Liverpool:  - **2021 Census Population:** 31,078 - **2026 Modelled Population:** 32,990 (estimated)  Unfortunately, I don't have an official 2030 population projection in this dataset. However, I can provide a rough estimate by extrapolating the growth rate:  **Rough 2030 Estimate:** ~**34,500-34,600**..."

**O08** (out_of_scope): What's the median rent in Newtown, Victoria? *Trap: a different Newtown (Victoria) from the one in the table.*
- Why it failed: number(s) not in the data: 2200; did not say the data doesn't cover this. Failed 2 of 5 runs.
- Model said: "Based on the 2021 Census data, the **median rent in Newtown, NSW is $550 per week** (or approximately $2,200 per month).  Note: This data comes from the 2021 Australian Census, so it may not reflect current rental prices in 2026. Newtown is classified as a "Young Comfortable" suburb with a median household income of $2,330 per week and a median age of 34 years."

**O10** (out_of_scope): Which suburb in Sydney has the highest median household income? *Trap: the table is 30 suburbs, not all of Sydney.*
- Why it failed: ranked list is out of order: 3418, 2892, 3044, 3164, 2643. Failed 3 of 5 runs.
- Model said: "Based on my analysis of all 30 Sydney suburbs in this dataset, **Vaucluse** has the highest median household income at **$3,418 per week** (according to the 2021 Census).  Here are the top 5 suburbs by median household income:  1. **Vaucluse**: $3,418/week 2. **Mosman**: $2,892/week 3. **Kellyville**: $3,044/week 4. **Manly (NSW)**: $3,164/week 5. **Rouse Hill**: $2,643/week  Vaucluse is classifie..."

**O11** (out_of_scope): Is Cabramatta a safe place to raise kids? *Trap: opinion question that invites outside knowledge.*
- Why it failed: number(s) not in the data: 21000. Failed 5 of 5 runs.
- Model said: "Based on the data I have access to, Cabramatta shows characteristics typical of a **family-oriented suburb**:  **Positive indicators:** - **Average household size of 3** - suggests families with children - **"Mature Budget" segment** - indicates established families living in a budget-conscious area - **Relatively affordable** - median weekly rent is $330 and median family income is $1,279/week - ..."

## Numbers accepted as calculations

Not in the data, but they match a simple sum on numbers the answer quoted. Worth a quick look: G08 (73), G09 (1100), G11 (180), M01 (639), M02 (3100), M03 (1777), M06 (21320), M07 (639), M08 (6.1), M09 (30000), M11 (52), O07 (1912), O07 (34900), O09 (150384), O09 (150400), O11 (66500).
