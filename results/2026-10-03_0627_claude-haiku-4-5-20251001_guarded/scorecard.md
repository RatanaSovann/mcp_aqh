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
- Model said: "Based on the 2021 Census data:  | Suburb | Median Monthly Mortgage | Difference | |--------|------------------------|------------| | **Liverpool** | $1,733 | Baseline | | **Kellyville** | $3,000 | +$1,267 (73% higher) |  **Key difference:** Kellyville's median monthly mortgage repayment is significantly higher at $3,000 compared to Liverpool's $1,733—a difference of $1,267 per month.  This reflect..."

**M02** (modelled): Roughly how many people live in Blacktown in 2026?
- Why it failed: number(s) not in the data: 3100
- Model said: "Based on the data available, the **modelled estimate for Blacktown's population in 2026 is approximately 54,090 people**.   This is a modelled estimate, not an actual Census count. For reference, the 2021 Census recorded 50,961 people in Blacktown, so the projection suggests growth of roughly 3,100 people over the five-year period."

