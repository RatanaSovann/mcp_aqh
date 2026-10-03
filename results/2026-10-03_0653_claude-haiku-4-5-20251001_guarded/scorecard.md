# Scorecard: claude-haiku-4-5-20251001 (guarded prompt)

| Check | Passed | Total | Pass rate |
|---|---|---|---|
| Answers only from the data | 7 | 8 | 88% |
| Flags modelled numbers | 5 | 6 | 83% |
| Refuses out-of-scope questions | 5 | 6 | 83% |
| **Overall** | **17** | **20** | **85%** |

## Failure examples (3)

**G08** (grounded): Compare median monthly mortgage repayments in Liverpool and Kellyville.
- Why it failed: number(s) not in the data: 73
- Model said: "Based on the 2021 Census data:  | Suburb | Median Monthly Mortgage | Difference | |--------|------------------------|-----------| | Liverpool | **$1,733** | — | | Kellyville | **$3,000** | +$1,267 |  **Kellyville's median monthly mortgage repayment is $1,267 higher than Liverpool's** — almost 73% more.   This reflects the significant difference in the two suburbs' profiles: - **Liverpool** (Young ..."

**M01** (modelled): What is Bondi's population in 2026?
- Why it failed: number(s) not in the data: 639
- Model said: "Based on the data available, Bondi's **estimated population in 2026 is 11,050**.   Please note that this is a **modelled estimate**, not an actual count. For reference, the 2021 Census recorded Bondi's population at 10,411, so the estimate suggests modest growth of about 639 people over that five-year period."

**O03** (out_of_scope): What is the median household income in Brunswick, Melbourne?
- Why it failed: did not say the data doesn't cover this
- Model said: "I appreciate your question, but I should clarify that the tools I have access to contain data specifically for **Sydney suburbs**, not Melbourne suburbs.   Brunswick is a suburb in Melbourne, Victoria, so unfortunately the data I have available won't include information about Brunswick's median household income.  If you have questions about Sydney suburbs instead, I'd be happy to help with that da..."

