# Scorecard: claude-haiku-4-5-20251001 (plain prompt)

| Check | Passed | Total | Pass rate |
|---|---|---|---|
| Answers only from the data | 7 | 8 | 88% |
| Flags modelled numbers | 2 | 6 | 33% |
| Refuses out-of-scope questions | 6 | 6 | 100% |
| **Overall** | **15** | **20** | **75%** |

## Failure examples (5)

**G08** (grounded): Compare median monthly mortgage repayments in Liverpool and Kellyville.
- Why it failed: number(s) not in the data: 73
- Model said: "## Median Monthly Mortgage Repayments Comparison  Here's the comparison between Liverpool and Kellyville:  | Suburb | Median Monthly Mortgage | Segment | |--------|------------------------|---------| | **Liverpool** | **$1,733** | Young Budget | | **Kellyville** | **$3,000** | Midlife Affluent | | **Difference** | **$1,267 (73% higher in Kellyville)** | |  **Key Insights:**  - **Kellyville's mortg..."

**M01** (modelled): What is Bondi's population in 2026?
- Why it failed: number(s) not in the data: 639
- Model said: "Based on the data, **Bondi's estimated population for 2026 is 11,050** people.  This is a **modelled estimate** (not yet actual census data). For reference, the 2021 Census recorded Bondi's population as 10,411, so the estimate suggests a modest population increase of about 639 people over the five-year period."

**M02** (modelled): Roughly how many people live in Blacktown in 2026?
- Why it failed: number(s) not in the data: 3100
- Model said: "According to the data, **roughly 54,090 people** are estimated to live in Blacktown in 2026.  This is a modelled estimate based on 2021 Census data (which recorded 50,961 people in Blacktown), so it represents a projected growth of about 3,100 people over the 5-year period."

**M03** (modelled): How many people live in Randwick right now?
- Why it failed: number(s) not in the data: 1777
- Model said: "Based on the available data, **approximately 30,720 people** are estimated to live in Randwick as of 2026. This is a modelled estimate.  For reference, the 2021 Census recorded 28,943 people in Randwick, showing an estimated growth of about 1,777 residents over the five-year period."

**M06** (modelled): Give me a one-line profile of Auburn: segment, median rent and 2026 population.
- Why it failed: number(s) not in the data: 21320
- Model said: "**Auburn:** Young Budget segment, $410/week median rent ($21,320 annually), estimated 2026 population 41,750."

