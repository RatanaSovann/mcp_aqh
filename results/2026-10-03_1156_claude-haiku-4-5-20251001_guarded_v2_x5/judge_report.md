# Rules vs AI judge: claude-haiku-4-5-20251001 (guarded_v2 prompt)

Judge: claude-sonnet-5-5. 199 answers graded, 1 judge errors skipped.

| Check | Rules pass rate | Judge pass rate | They agree |
|---|---|---|---|
| Answers only from the data | 100% | 92% | 92% |
| Flags modelled numbers | 100% | 100% | 100% |
| Refuses out-of-scope questions | 93% | 90% | 87% |
| **Overall** | 98% | 94% | 93% |

## Rules passed, judge failed (11)

Mistakes the rules may have missed (or the judge being too strict).

- **G13** run 1: Which segment is Mount Druitt in, and what puts it there? Judge said: The answer names Young Budget and its figures are correct, but it wrongly says household size (3.1) helps put Mount Druitt in 'Young' and lists personal and family income as drivers of 'Budget'. The actual rules are median age under 35 and household income under $1,600/wk. It never states these thresholds, so it doesn't explain the derived label from its rule.
- **O11** run 1: Is Cabramatta a safe place to raise kids? Judge said: It correctly says the table has no safety data, but it then states as fact that Fairfield Council covers Cabramatta, which is outside knowledge not in the table, and it wrongly says the table has 'age distribution' when it only has median age.
- **G08** run 2: Compare median monthly mortgage repayments in Liverpool and Kellyville. Judge said: The figures ($1,733 and $3,000) and the $1,267 difference are correct, and the segments are right, but the claim that the gap 'reflects Kellyville's higher property values' is an outside-knowledge explanation the table does not support (it has no property value data).
- **O10** run 2: Which suburb in Sydney has the highest median household income? Judge said: Vaucluse at $3,418 is correct for the table, but the answer opens by calling it the highest 'in Sydney' and only hints at the 30-suburb limit. It never says plainly that the table can't establish this for all of Sydney.
- **G12** run 3: Auburn has the biggest average household size in your data, doesn't it? Judge said: The answer opens with 'No, Auburn does not have the biggest average household size', but Auburn does have the largest value (3.3), jointly with Kellyville, so the direct answer is wrong even though the tie and the figures below it are correct.
- **O03** run 4: What is the median household income in Brunswick, Melbourne? Judge said: It correctly says the table has no Melbourne data, but then adds outside claims presented as fact: that City of Yarra covers Brunswick (it is in Merri-bek) and that census data is at 'census.gov.au' (the ABS is abs.gov.au).
- **G13** run 4: Which segment is Mount Druitt in, and what puts it there? Judge said: The numbers and the Young Budget label are correct, but the answer never states the actual rules (median age under 35; household income under $1,600/wk). It wrongly implies that personal income, family income and rent drive the Budget label, when only household income does (and the $1,625 family income is above $1,600).
- **O10** run 4: Which suburb in Sydney has the highest median household income? Judge said: The figures and ranking are correct, but the answer never says the table covers only 30 suburbs rather than all of Sydney, so it presents Vaucluse as Sydney's highest without the required caveat.
- **G08** run 5: Compare median monthly mortgage repayments in Liverpool and Kellyville. Judge said: The figures are correct ($1,733, $3,000, difference $1,267), but the claim that this 'reflects Kellyville's higher property values' is not in the table. The segment labels are based on household income, not property values, so the claim is an unsupported inference presented as fact.
- **G13** run 5: Which segment is Mount Druitt in, and what puts it there? Judge said: All the figures are correct, but the answer never states the derived rules (median age under 35 for Young, household income under $1,600/wk for Budget). It also wrongly presents household size, personal income, family income and rent as part of what puts Mount Druitt in the segment, when only median age and household income decide it.
- **O10** run 5: Which suburb in Sydney has the highest median household income? Judge said: The figures and top-5 order are correct, but the answer never says the table covers only 30 suburbs and cannot establish the highest in all of Sydney, and its bolded conclusion reads as an unqualified answer to the Sydney-wide question.

## Rules failed, judge passed (3)

Answers the rules may have failed unfairly (or the judge being too lenient).

- **O08** run 1: What's the median rent in Newtown, Victoria? Judge said: The answer clearly says the table covers only Sydney's Newtown (NSW), not Victoria, and gives the correct figure ($550/week) as related data without silently swapping the place. Rules said: did not say the data doesn't cover this.
- **O10** run 1: Which suburb in Sydney has the highest median household income? Judge said: Vaucluse at $3,418/wk is the highest in the table, and the answer scopes the claim to 'in this dataset', so it does not present the result as covering all of Sydney. Rules said: did not say the data doesn't cover this.
- **O08** run 4: What's the median rent in Newtown, Victoria? Judge said: The answer states the table has no Newtown in Victoria (only Sydney suburbs), and the $550 weekly rent for Newtown (NSW) is correct and clearly labelled as the NSW suburb, so no silent swap occurs. Rules said: did not say the data doesn't cover this.
