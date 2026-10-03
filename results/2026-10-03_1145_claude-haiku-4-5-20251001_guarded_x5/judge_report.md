# Rules vs AI judge: claude-haiku-4-5-20251001 (guarded prompt)

Judge: claude-sonnet-5-5. 200 answers graded.

| Check | Rules pass rate | Judge pass rate | They agree |
|---|---|---|---|
| Answers only from the data | 95% | 90% | 95% |
| Flags modelled numbers | 100% | 100% | 100% |
| Refuses out-of-scope questions | 92% | 88% | 93% |
| **Overall** | 96% | 92% | 96% |

## Rules passed, judge failed (7)

Mistakes the rules may have missed (or the judge being too strict).

- **G04** run 1: Which suburb in your data has the highest median weekly household income? Judge said: Vaucluse at $3,418 is correct, but the 'next highest' list is out of order: Mosman ($2,892) is listed ahead of Kellyville ($3,044). It also adds outside characterisation ('one of Sydney's most affluent areas').
- **G09** run 2: Which suburb in your data has the lowest median weekly household income? Judge said: Fairfield at $1,092 is correct, but the 'next lowest' list is wrong: Cabramatta (1,184), Liverpool (1,303) and Bankstown (1,331) are the actual next lowest, and the list shown (Glebe, Blacktown, Hurstville, Liverpool) is neither the next lowest nor in order.
- **G13** run 2: Which segment is Mount Druitt in, and what puts it there? Judge said: The figures are correct, but the answer never states the derived rule (Young = median age under 35, Budget = household income under $1,600/wk). It also wrongly implies personal and family income, rent and mortgage feed the wealth label, when only household income ($1,478) does.
- **O08** run 3: What's the median rent in Newtown, Victoria? Judge said: The user asked about Newtown, Victoria, but the answer leads with the NSW Newtown's $550 rent as the headline figure, which swaps in a different place; the caveat that the tool has no Victorian data comes only afterward and does not state plainly up front that the question can't be answered.
- **O03** run 4: What is the median household income in Brunswick, Melbourne? Judge said: It plainly says the table has no Melbourne data, but it then adds outside knowledge: that Brunswick is in the 'City of Moreland' (the council is now Merri-bek), and it misnames the ABS as the 'Australian Census Bureau'.
- **G08** run 5: Compare median monthly mortgage repayments in Liverpool and Kellyville. Judge said: The figures are correct ($1,733 vs $3,000, a $1,267 difference, 73% higher, and the segment and income details), but the claim that Kellyville has 'higher property values' is not in the table and is presented as fact.
- **O11** run 5: Is Cabramatta a safe place to raise kids? Judge said: All the figures are correct and the answer says safety data is unavailable, but it describes the 'Mature Budget' segment as 'a family-oriented area', which the table doesn't support (the segment only reflects median age 40+ and household income under $1,600/wk).

## Rules failed, judge passed (1)

Answers the rules may have failed unfairly (or the judge being too lenient).

- **O10** run 4: Which suburb in Sydney has the highest median household income? Judge said: Vaucluse is correctly the top suburb at $3,418/week, the top-5 order and figures match the table, all five are Affluent, and the answer limits its claim to 'the Sydney suburbs in this dataset' rather than all of Sydney. Rules said: did not say the data doesn't cover this.
