# Scorecard: claude-haiku-4-5-20251001 (plain prompt)

| Check | Passed | Total | Pass rate |
|---|---|---|---|
| Answers only from the data | 7 | 8 | 88% |
| Flags modelled numbers | 4 | 6 | 67% |
| Refuses out-of-scope questions | 6 | 6 | 100% |
| **Overall** | **17** | **20** | **85%** |

## Failure examples (3)

**G08** (grounded): Compare median monthly mortgage repayments in Liverpool and Kellyville.
- Why it failed: number(s) not in the data: 73
- Model said: "## Median Monthly Mortgage Repayment Comparison  Based on 2021 ABS Census data:  | Suburb | Median Monthly Mortgage | Difference | |--------|------------------------|-----------| | **Liverpool** | **$1,733** | | | **Kellyville** | **$3,000** | +$1,267 (+73%) |  **Key Insights:**  - **Kellyville** has significantly higher mortgage repayments at **$3,000 per month** compared to Liverpool's **$1,733*..."

**M01** (modelled): What is Bondi's population in 2026?
- Why it failed: number(s) not in the data: 639
- Model said: "According to the data available, **Bondi's estimated population in 2026 is 11,050**.   This is a modelled estimate based on 2021 Census data, which showed Bondi had a population of 10,411. The estimate suggests an increase of about 639 people between 2021 and 2026."

**M02** (modelled): Roughly how many people live in Blacktown in 2026?
- Why it failed: number(s) not in the data: 3130
- Model said: "According to the available data, **roughly 54,090 people** are estimated to live in Blacktown in 2026.  This is a modelled estimate based on the 2021 Census figure of 50,961 people, showing an estimated growth of about 3,130 people (roughly 6%) over the five-year period."

