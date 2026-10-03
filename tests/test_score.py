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


def test_out_of_scope_refusal():
    assert score_answer("O01", "House prices aren't included in this data, so I can't tell you.")["passed"]
    assert not score_answer("O01", "The median house price in Mosman is about $4,200,000.")["passed"]
