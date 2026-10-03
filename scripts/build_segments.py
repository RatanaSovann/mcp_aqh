"""Build data/segments.csv from the raw Census table.

Adds two things on top of the real ABS numbers:
  1. a simple segment label (lifestage x wealth), and
  2. one MODELLED column (est_population_2026), so we can test whether the
     model tells the user when a number is an estimate rather than a count.

Run:  python scripts/build_segments.py
"""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "census_g02_raw.csv"
OUT = ROOT / "data" / "segments.csv"

# Toy growth assumption for the modelled column. Deliberately simple and
# documented: 1.2% a year for 5 years (2021 -> 2026), applied to every suburb.
ANNUAL_GROWTH = 0.012
YEARS = 5


def lifestage(median_age: float) -> str:
    if median_age < 35:
        return "Young"
    if median_age < 40:
        return "Midlife"
    return "Mature"


def wealth(household_income_weekly: float) -> str:
    if household_income_weekly < 1600:
        return "Budget"
    if household_income_weekly < 2400:
        return "Comfortable"
    return "Affluent"


def main() -> None:
    with RAW.open(newline="") as f:
        rows = list(csv.DictReader(f))

    out_rows = []
    for r in rows:
        age = float(r["median_age"])
        hh_income = float(r["median_household_income_weekly"])
        est_2026 = round(int(r["people"]) * (1 + ANNUAL_GROWTH) ** YEARS, -1)
        out_rows.append(
            {
                **r,
                "lifestage": lifestage(age),
                "wealth": wealth(hh_income),
                "segment": f"{lifestage(age)} {wealth(hh_income)}",
                "est_population_2026": int(est_2026),
            }
        )

    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"Wrote {len(out_rows)} rows to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
