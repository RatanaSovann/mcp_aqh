import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "eval"))
from score import score_answer  # noqa: E402


def test_grounded_pass():
    assert score_answer("G01", "Mosman's median household income is $2,892 a week (2021 Census).")["passed"]


def test_grounded_fails_on_made_up_number():
    r = score_answer("G01", "It's $2,892 a week, and the median house price is $3,450,000.")
    assert not r["passed"]
    assert any("not in the data" in x for x in r["reasons"])


def test_modelled_needs_flag():
    assert not score_answer("M01", "Bondi has 11,050 people in 2026.")["passed"]
    assert score_answer("M01", "Bondi's modelled 2026 population is about 11,050 (an estimate).")["passed"]


def test_calculated_numbers_are_allowed_but_listed():
    r = score_answer("M01", "Bondi's estimated 2026 population is 11,050, up about 639 from 10,411 in 2021.")
    assert r["passed"]
    assert r["calculated"] == ["639"]
    # Rounded and percentage forms of a calculation count too.
    assert score_answer("G08", "Liverpool pays $1,733 and Kellyville $3,000, about 73% more.")["passed"]


def test_made_up_number_still_fails_next_to_calculation():
    r = score_answer("M01", "Bondi's estimated 2026 population is 11,050, with 4,800 new homes.")
    assert not r["passed"]


def test_must_call_the_tool():
    answer = "Mosman's median household income is $2,892 a week."
    assert not score_answer("G01", answer, tool_calls=[])["passed"]
    assert score_answer("G01", answer, tool_calls=[{"tool": "get_suburb", "input": {}}])["passed"]
    # Refusing without looking is fine for out-of-scope questions.
    assert score_answer("O03", "This data only covers Sydney, not Melbourne.", tool_calls=[])["passed"]


def test_modelled_number_must_be_flagged_in_any_answer():
    assert not score_answer("G16", "Penrith has 19,070 people.")["passed"]
    assert score_answer("G16", "Penrith has 19,070 people (a modelled 2026 estimate).")["passed"]
    assert score_answer("G16", "Penrith had 17,966 people at the 2021 Census.")["passed"]


def test_ranked_list_must_be_in_order():
    ok = "Vaucluse is highest.\n1. Vaucluse $3,418\n2. Manly $3,164\n3. Kellyville $3,044"
    assert score_answer("G04", ok)["passed"]
    r = score_answer("G04", "Vaucluse is highest.\n1. Vaucluse $3,418\n2. Mosman $2,892\n3. Manly $3,164")
    assert any("out of order" in x for x in r["reasons"])


def test_review_queue_risk_routing():
    from review_queue import risk_reason
    assert risk_reason("1. Vaucluse $3,418\n2. Manly $3,164\n3. Kellyville $3,044") == "list or ranking"
    assert risk_reason("Crime data isn't included in this table.") == "refusal"
    assert risk_reason("This reflects Kellyville's higher property values.") == "explanation"
    assert risk_reason("Mosman's median weekly rent is $590.") == ""


def test_out_of_scope_refusal():
    assert score_answer("O01", "House prices aren't included in this data, so I can't tell you.")["passed"]
    assert score_answer("O03", "The data I have won't include Brunswick, which is in Melbourne.")["passed"]
    assert not score_answer("O01", "The median house price in Mosman is about $4,200,000.")["passed"]
