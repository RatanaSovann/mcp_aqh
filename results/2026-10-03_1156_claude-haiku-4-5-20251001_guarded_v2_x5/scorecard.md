# Scorecard: claude-haiku-4-5-20251001 (guarded_v2 prompt)

Each question was asked **5 times**. "Passed" is the average per run; "Range" is the worst and best run, so you can see how much is luck.

| Check | Passed (avg) | Total | Pass rate | Range |
|---|---|---|---|---|
| Answers only from the data | 16 | 16 | 100% | 16-16 |
| Flags modelled numbers | 12 | 12 | 100% | 12-12 |
| Refuses out-of-scope questions | 11.2 | 12 | 93% | 10-12 |
| Basic questions | 20 | 20 | 100% | 20-20 |
| Hard questions (trick wording, traps) | 19.2 | 20 | 96% | 18-20 |
| **Overall** | **39.2** | **40** | **98%** | 38-40 |

## Failure examples (2 questions)

**O08** (out_of_scope): What's the median rent in Newtown, Victoria? *Trap: a different Newtown (Victoria) from the one in the table.*
- Why it failed: did not say the data doesn't cover this. Failed 2 of 5 runs.
- Model said: "According to the 2021 Census data, the **median rent in Newtown (NSW)** is **$550 per week**.  Note: This is Newtown in New South Wales (Sydney), not Victoria. My data covers Sydney suburbs only."

**O10** (out_of_scope): Which suburb in Sydney has the highest median household income? *Trap: the table is 30 suburbs, not all of Sydney.*
- Why it failed: did not say the data doesn't cover this. Failed 2 of 5 runs.
- Model said: "Based on the data from the 2021 Census, **Vaucluse** has the highest median household income among Sydney suburbs in this dataset, with a **median household income of $3,418 per week**."
