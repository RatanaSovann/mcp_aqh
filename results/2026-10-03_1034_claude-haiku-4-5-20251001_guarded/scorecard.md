# Scorecard: claude-haiku-4-5-20251001 (guarded prompt)

| Check | Passed | Total | Pass rate |
|---|---|---|---|
| Answers only from the data | 7 | 8 | 88% |
| Flags modelled numbers | 5 | 6 | 83% |
| Refuses out-of-scope questions | 6 | 6 | 100% |
| **Overall** | **18** | **20** | **90%** |

## Failure examples (2)

**G08** (grounded): Compare median monthly mortgage repayments in Liverpool and Kellyville.
- Why it failed: number(s) not in the data: 73
- Model said: "Based on the 2021 Census data:  **Median Monthly Mortgage Repayments:** - **Liverpool**: $1,733 - **Kellyville**: $3,000  **Difference**: Kellyville's median monthly mortgage repayments are **$1,267 higher** than Liverpool's (73% more).  This significant difference reflects the different socioeconomic profiles of these suburbs: - **Liverpool** is classified as "Young Budget" with a median househol..."

**M02** (modelled): Roughly how many people live in Blacktown in 2026?
- Why it failed: number(s) not in the data: 3100
- Model said: "Based on the data available, **roughly 54,090 people** are estimated to live in Blacktown in 2026.   This is a **modelled estimate**, not an actual Census count. For reference, the 2021 Census recorded 50,961 people in Blacktown, so the estimate suggests an increase of around 3,100 people over that five-year period."

