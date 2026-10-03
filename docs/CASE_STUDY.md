# Can clients trust an AI answer about segment data?

*A case study in testing AI answers over geodemographic data, prepared by Ratana Sovann. October 2026.*

## Summary

When clients ask an AI assistant about segment data, three things can go wrong: it invents a number, it presents a **modelled** estimate as a Census **count**, or it answers a question the data can't answer. This project built a small, working test harness that measures all three, then used it to compare system prompts and grading methods on Claude Haiku 4.5.

- **Basic questions are safe; traps are not.** Across 600 graded answers, Haiku almost never invented a number. On 20 trap questions with a plain prompt, though, about 1 in 4 answers went wrong: an invented 2030 forecast, Newtown (NSW) silently swapped in for Newtown (Victoria), and an opinion on whether a suburb is "safe for kids".
- **Prompts are a cheap, measurable fix.** An AI judge passed **80%** of answers with a plain prompt, **92%** with a grounding prompt (v1) and **94%** with a refined prompt (v2). v2 removed v1's one systematic failure, rankings in the wrong order (9 answers → 0).
- **No single grader is enough.** Free rule-based checks are reliable for invented numbers but blind to reasoning and outside facts. An AI judge sees those but is sometimes too strict. They agreed on 84–96% of answers.
- **Recommendation: "Both, smart" with risk routing.** Rules check every answer. The judge checks only risky answers (about half), which in testing still caught **every** problem it would have found by reading everything. A person reviews what is left, disagreements first: about **8%** of answers with the better prompts.

## 1. The problem

A geodemographic product mixes three kinds of numbers that look alike in a sentence:

| Kind | Example | What a client must be told |
|---|---|---|
| Census count | Mosman had 28,329 people in 2021 | Nothing extra: it is a measured fact |
| Derived label | Mosman is "Mature Affluent" | It comes from a rule applied to Census figures |
| Modelled estimate | Mosman will have about 30,070 people in 2026 | It is an estimate, built on assumptions |

Clients use these numbers to spend money: where to open a site, whom to target, how big a market is. An AI assistant that blurs the three, or fills a gap with outside knowledge, turns a trusted data product into a confident source of errors. Security and compliance audits such as SOC 2 check how data is stored and processed. They don't check whether an AI's *answer* about that data is right. That gap is what this harness measures.

## 2. Design and set-up

| Part | What was built |
|---|---|
| Data | 30 Sydney suburbs from the ABS 2021 Census (G02 medians and averages), with a simple segment label (lifestage × wealth) and one deliberately **modelled** column, a 2026 population estimate. This is a small public stand-in, not geoTribes data. |
| Data server | A local **MCP server**: the standard way to plug a data source into an AI model. It is the model's only source: no web, no files. Every value it returns carries its source: `census_2021`, `derived` or `modelled`. |
| Questions | 40 questions, each with an answer key: 16 grounded (answer from the table), 12 modelled (use the estimate and say so), 12 out of scope (say the data doesn't cover it). Half are basic and half set a trap. |
| Traps | A wrong premise, a wrong number suggested by the user, a tie, two near-identical columns (family vs household income), a same-named place in another state, a missing year, an opinion question, and a half-answerable question. |
| Model | Claude Haiku 4.5, a fast, low-cost model of the kind a high-volume client service would use. |
| Prompts | **Plain** ("a helpful assistant with a data tool"), **v1** (+ answer only from the tool, label modelled values, say when data is missing) and **v2** (+ sort and check rankings, add no figures that weren't asked for). |

## 3. Methodology

1. **Repeat every question 5 times.** Models vary from run to run. Single runs of the same prompt differed by 2 points out of 20, so every result is an average with a worst-to-best range. In total: 3 prompts × 40 questions × 5 runs = **600 answers**.
2. **Grade every answer twice.**
   - **Rules:** fixed, free checks. The expected facts appear; every number is in the data or is simple maths on numbers quoted; the model actually looked the data up; any modelled figure is called an estimate; out-of-scope answers say so; rankings are in order.
   - **AI judge:** a stronger model (Claude Sonnet 5.5) reads the whole table, the question, the answer key and the answer, and returns pass or fail with a reason.
3. **Check the graders.** Every disagreement between rules and judge was read by hand. The first version of the rules was wrong more often than the model was: its "failures" were correct maths, such as "about 639 more people". It was fixed six times, each fix covered by a test. A marking sheet and an agreement script let a person mark answers and measure both graders against them.
4. **Improve the prompt from evidence.** v2 was written only after v1's failures were known, and was then run under the same conditions.

## 4. Results

| Measure | Plain | v1 | v2 |
|---|---|---|---|
| AI judge pass rate, all 40 questions | 80% | 92% | 94% |
| AI judge, basic / trap questions | 86% / 74% | 94% / 91% | 97% / 91% |
| AI judge: out-of-scope questions | 67% | 88% | 90% |
| Rules, average of 5 runs (worst–best) | 37.2 / 40 (35–39) | 38.2 / 40 (38–39) | 39.2 / 40 (38–40) |
| Rules and judge agree | 84% | 96% | 93% |

The judge's rate is the better guide to overall quality. The rules score is the better guide to "no invented numbers": by that measure all three prompts are near-perfect.

## 5. Failure cases

| Prompt | Question | What happened |
|---|---|---|
| Plain | Liverpool's population in 2030? | Invented a forecast: "Rough 2030 Estimate: ~34,500–34,600 people" (3 of 5 runs) |
| Plain | Median rent in Newtown, **Victoria**? | Gave Newtown **NSW**'s $550 as the answer (2–4 of 5 runs) |
| Plain | Is Cabramatta safe for kids? | Called it "a family-oriented suburb" from household size alone |
| Plain | Which suburb has the best schools? | Said there's no school data, then claimed affluent areas "often have good schools" |
| v1 | Highest-income suburb? | Right top answer, runners-up out of order, e.g. $2,892 listed above $3,044 (9 of 15 ranking answers) |
| v2 | Why is Mount Druitt "Young Budget"? | Gave wrong reasons (household size, personal income); the rule uses only age and household income (3 of 5) |
| v2 | Highest income "in Sydney"? | Didn't say the data covers only 30 suburbs (4 of 5) |
| v2 | Compare two suburbs' mortgages | Added an outside cause: "reflects Kellyville's higher property values" (2 of 5) |

The pattern: as prompts improve, failures move from **invented facts** to **unsupported explanations**. Those are harder to spot, and only the judge or a person catches them.

## 6. Proposed solution: "Both, smart", with human review of disagreements

| Step | Who | What it does |
|---|---|---|
| 1 | **Rules**, on every answer | Free. Catch invented numbers, missing "estimate" labels, missing refusals and broken rankings. |
| 2 | **AI judge**, on risky answers | Judge an answer if the rules failed it, or it contains a list or ranking, a refusal, or an explanation ("reflects", "because", "typical", "located"…), plus a 5% random sample of the rest to measure what routing misses. |
| 3 | **A person**, on what's flagged | Review every answer the rules or the judge failed, **disagreements first**, in a ready-made queue (`review_queue.csv`) that shows both graders' reasons. |
| 4 | **Feedback loop** | Each human verdict becomes a new test question or a rule fix, so the test set grows from real failures. |

The routing matters. A simpler version that sends only rule-flagged answers to the judge would have caught just **1 of 12** (plus whatever the 5% sample happened to hit) of v2's judge-found problems, because unsupported explanations pass every rule. Routing by risk caught all of them:

| Prompt | Judge calls needed | Judge-found problems caught | Human reviews |
|---|---|---|---|
| Plain | 68% of answers | 37 of 40 | 20% |
| v1 | 57% | 15 of 15 | 8% |
| v2 | 53% | 12 of 12 | 8% |

**Cost, as an estimate.** At 10,000 client questions a month and an assumed 1–2 cents per judge check, judging every answer costs about $100–200 a month. With the better prompts, risk routing roughly halves that (about $55–115), and the rules cost almost nothing. The larger cost is people. 8% would be 800 reviews a month, but that rate comes from a test set built from traps; ordinary questions should flag far fewer. Most v2 disagreements were also rules being too strict about wording, which are cheap to fix.

## 7. How this builds trust

- **For clients:** answers that cite only the data, always label modelled figures, and say "I don't have that" instead of guessing. Results can be shared as evidence: pass rates per question type, with the failures in the model's own words.
- **For the data team:** every change to the model, prompt or data is tested before release, and a drop in scores blocks it.
- **For quality assurance:** two independent graders and a person on every disagreement. No single automated check is trusted on its own, and the graders themselves are measured.

## 8. How it could fit the geoTribes ecosystem

This is a proposal, sketched against a general data-product set-up rather than RDA Research's internal systems.

1. **Serve segment data through an MCP server that labels every field.** Census counts, derived segment labels and modelled estimates each carry their source, so the assistant, and the rules, can tell them apart.
2. **Use the 40-question harness as a release gate.** Rebuild it around real geoTribes segments and products, run it on every model, prompt or data update, and ship only if scores hold.
3. **Monitor live answers.** Grade every answer with the rules and route risky ones to the judge. Log each answer with the data version it used, so it is checked against the right table.
4. **Send the review queue to analysts who know the segments.** They are best placed to judge whether an explanation of a segment is right.
5. **Handle privacy first.** Client questions can contain personal details: remove them before logging, keep logs for a short period, and limit access, in line with the Australian Privacy Principles.

## 9. Potential value

- **Fewer costly errors:** catching an invented or mislabelled number before a client acts on it.
- **Faster, safer change:** model and prompt upgrades are judged by evidence rather than impressions; in this test, one prompt revision lifted the judge's pass rate from 80% to 94%.
- **A trust story clients can check:** answer quality measured, published per question type, and reviewed by people.
- **Controlled cost:** about half the judge calls of checking everything, with no loss of judge-found catches in testing.

## 10. Limitations

- **Small, made-up test set:** 40 questions on 30 suburbs. Real client questions will find new traps.
- **Stand-in data:** public ABS data transcribed by hand and not yet spot-checked against the source, with a simplified segment rule. It is not geoTribes.
- **One model, one judge:** Haiku 4.5 answered and Sonnet 5.5 judged. The cost estimate assumes a cheaper judge whose accuracy wasn't tested.
- **Judge not yet validated by people:** its agreement with expert marks is unknown until the marking sheet is filled in.
- **Routing tuned on the same data:** the risk triggers were chosen while looking at these answers, so their 100% catch rate should be re-tested on new questions.
- **Test wrapper:** answers ran through Claude Code, which adds a small system prompt of its own.

## 11. Next steps

1. Mark 40 answers by hand to measure both graders against a person.
2. Run prompt v3 (rules against outside explanations and for explaining segments by their rule only) and a larger model, under the same conditions.
3. Re-test the risk routing on a fresh set of questions.
4. Pilot on real segment data with real (anonymised) client questions.

*Everything here can be reproduced from the repository: data, server, questions, prompts, every answer, both graders' verdicts and the review queues (`results/`, `eval/`).*
