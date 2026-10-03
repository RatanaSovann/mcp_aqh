"""A tiny local MCP server that serves the Sydney suburb segment table.

Every number it returns is labelled with where it came from:
  census_2021 = a real ABS 2021 Census figure
  derived     = a label we computed from Census figures (the segment)
  modelled    = an estimate, NOT a count (est_population_2026)

Run on its own (stdio):  python server.py
"""

import csv
import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

DATA_DIR = Path(__file__).resolve().parent / "data"
COLUMNS = json.loads((DATA_DIR / "columns.json").read_text())
NUMERIC = {
    "people", "median_age", "median_personal_income_weekly",
    "median_family_income_weekly", "median_household_income_weekly",
    "median_mortgage_monthly", "median_rent_weekly", "avg_household_size",
    "est_population_2026",
}

DATA_NOTE = (
    "Coverage: 30 Sydney suburbs, ABS 2021 Census (G02 Selected Medians and "
    "Averages), plus a derived segment label and one modelled column. "
    "Fields with source='modelled' are estimates and must be described as "
    "such. Anything not in this table is not available from this tool."
)


def _load_rows() -> list[dict]:
    with (DATA_DIR / "segments.csv").open(newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in NUMERIC:
            r[k] = float(r[k]) if "." in r[k] else int(r[k])
    return rows


ROWS = _load_rows()


def _clean(name: str) -> str:
    return name.lower().replace("(nsw)", "").strip()


def _find(name: str) -> dict | None:
    for r in ROWS:
        if _clean(r["area_name"]) == _clean(name):
            return r
    return None


def _labelled(row: dict) -> dict:
    return {
        k: {"value": v, "source": COLUMNS[k]["source"]}
        for k, v in row.items()
    }


mcp = FastMCP("sydney-segments")


@mcp.tool()
def list_suburbs() -> dict:
    """List every suburb in the table with its segment label."""
    return {
        "suburbs": [{"area_name": r["area_name"], "segment": r["segment"]} for r in ROWS],
        "note": DATA_NOTE,
    }


@mcp.tool()
def get_suburb(name: str) -> dict:
    """Get all fields for one suburb. Each value carries its source
    (census_2021, derived or modelled)."""
    row = _find(name)
    if row is None:
        return {
            "error": f"'{name}' is not in this table.",
            "available": [r["area_name"] for r in ROWS],
            "note": DATA_NOTE,
        }
    return {"suburb": _labelled(row), "note": DATA_NOTE}


@mcp.tool()
def find_suburbs_by_segment(segment: str) -> dict:
    """List suburbs in a segment, e.g. 'Young Affluent'. Lifestage is
    Young/Midlife/Mature, wealth is Budget/Comfortable/Affluent."""
    matches = [r["area_name"] for r in ROWS if r["segment"].lower() == segment.lower().strip()]
    return {
        "segment": segment,
        "suburbs": matches,
        "all_segments": sorted({r["segment"] for r in ROWS}),
        "note": DATA_NOTE,
    }


@mcp.tool()
def describe_columns() -> dict:
    """Explain every column: what it means and whether it is a Census
    figure, a derived label, or a modelled estimate."""
    return {"columns": COLUMNS, "note": DATA_NOTE}


if __name__ == "__main__":
    mcp.run()
