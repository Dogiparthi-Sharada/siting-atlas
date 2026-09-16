"""What Amazon's disclosed subsidies can and cannot tell this project.

    python -m siting_atlas.ingest.subsidies

Reads the Good Jobs First Subsidy Tracker export and writes
`outputs/metrics/subsidies.json`.

WHY THIS IS AN EMITTER AND NOT A SHELL COMMAND
----------------------------------------------
Three figures were quoted to the inspirator today from throwaway shell
commands and all three turned out to be wrong or uncheckable. The project's
rule is "cite the artefact, not the figure", and a number nobody can
reproduce is not a number. Everything stated about this file is computed here.

WHAT THE SOURCE IS
------------------
Good Jobs First aggregate subsidy awards that state and local governments are
LEGALLY REQUIRED to disclose. That provenance is the interesting part: this is
the best case for public transparency -- a nonprofit consolidating mandated
reporting -- rather than a leak or a scrape.

Downloaded 2026-09-14 for USD 25. This host receives HTTP 403 from the
endpoint, so the file cannot be re-fetched here and is tracked as evidence.

THE FINDING THIS MODULE EXISTS TO MEASURE
-----------------------------------------
The obvious use -- "tell a county what comparable counties paid for a facility
like theirs" -- is NOT SUPPORTED, and the reason is worth more than the use
would have been.

Even in the best case for disclosure, the records are too coarse to attribute
a subsidy to a building. Most rows name a county and no postcode. A county
negotiating a specific site cannot look up what a specific comparable site
received, because the mandated disclosure was never that granular.

Set beside `docs/data/MWPVL_2025.md`, that makes a pair:

  - commercial network data:   withheld, because it is worth money
  - mandated subsidy data:     published, and still too coarse to act on

Two different mechanisms, the same outcome for the county. The second is the
more damning, because it is what the transparency regime already delivers.

WHAT IS DELIBERATELY NOT DONE
-----------------------------
No subsidy is attributed to a facility. No value is imputed. Megadeals are
reported separately rather than winsorised, because a $8.3bn data-centre award
is not an outlier in a delivery-station distribution -- it is a different
population, and averaging it in would be the error, not excluding it.
"""

from __future__ import annotations

import re

import pandas as pd

from ..common import paths
from ..common.log_json import write_json

SOURCE = (paths.EXTERNAL / "subsidies"
          / "subsidy_tracker_amazon_2026-09-14.csv")
FACILITIES = (paths.EXTERNAL / "facility_panel"
              / "national_facilities_expanded.csv")
OUT = paths.METRICS / "subsidies.json"

#: Project descriptions are free text, so facility class is inferred from
#: words rather than from the NAICS column -- only 23 of 576 rows carry a
#: NAICS code at all. Reported with its own counts so a reader can judge the
#: classifier rather than trust it.
CLASSES = (
    ("warehouse_distribution",
     r"warehous|distribut|fulfil|delivery station|sortation|logistic"),
    ("data_centre", r"data cent|data-cent"),
    ("headquarters_office", r"headquarter|hq2|office tower|corporate office"),
)


def _money(series: pd.Series) -> pd.Series:
    """Dollar strings to floats. Blank and unparseable become NaN, not zero."""
    return pd.to_numeric(
        series.astype(str).str.replace(r"[^0-9.-]", "", regex=True),
        errors="coerce")


def _city_key(value) -> str:
    return re.sub(r"[^A-Z]", "", str(value).upper())


def collect() -> dict:
    d = pd.read_csv(SOURCE, dtype=str)
    d["value"] = _money(d["Subsidy Value"])
    d["jobs"] = _money(d["Number of Jobs or Training Slots"])
    d["year"] = pd.to_numeric(d["Year"], errors="coerce")
    text = (d["Project Description"].fillna("") + " "
            + d["Notes"].fillna("") + " "
            + d["Specialized Industry"].fillna("")).str.lower()

    by_class = {}
    for name, pattern in CLASSES:
        hit = text.str.contains(pattern, regex=True)
        by_class[name] = {
            "records": int(hit.sum()),
            "total_usd": float(d.loc[hit, "value"].sum()),
            "median_usd": float(d.loc[hit, "value"].median()),
        }
    classified = text.str.contains(
        "|".join(p for _, p in CLASSES), regex=True)
    by_class["unclassified"] = {
        "records": int((~classified).sum()),
        "total_usd": float(d.loc[~classified, "value"].sum()),
        "median_usd": float(d.loc[~classified, "value"].median()),
    }

    # The granularity finding. This is the point of the module.
    granularity = {
        "records": int(len(d)),
        "with_a_postcode": int(d["Zip"].notna().sum()),
        "with_a_street_address": int(d["Address"].notna().sum()),
        "with_a_county": int(d["County"].notna().sum()),
        "with_a_city": int(d["City"].notna().sum()),
        "with_a_subsidy_value": int(d["value"].notna().sum()),
        "with_a_job_count": int(d["jobs"].notna().sum()),
    }

    facilities = pd.read_csv(FACILITIES, dtype=str)
    fac_cities = {(_city_key(r.city), str(r.state).upper()[:2])
                  for r in facilities.itertuples()
                  if pd.notna(r.city)}
    sub_cities = {(_city_key(r.City), str(r.Location).upper()[:2])
                  for r in d.itertuples() if pd.notna(r.City)}
    overlap = fac_cities & sub_cities

    # Deals small enough to be a plausible single logistics building. Stated as
    # a threshold rather than a percentile so the reader can move it.
    small = d[d["value"] < 50e6]

    return {
        "source": "Good Jobs First Subsidy Tracker, Amazon parent",
        "downloaded": "2026-09-14",
        "cost_usd": 25,
        "year_range": [int(d["year"].min()), int(d["year"].max())],
        "total_disclosed_usd": float(d["value"].sum()),
        "by_facility_class": by_class,
        "granularity": granularity,
        "join_to_facility_panel": {
            "facility_cities": len(fac_cities),
            "subsidy_cities": len(sub_cities),
            "overlapping_cities": len(overlap),
            "share_of_facility_cities": len(overlap) / len(fac_cities),
        },
        "deals_under_50m": {
            "records": int(len(small)),
            "total_usd": float(small["value"].sum()),
            "median_usd": float(small["value"].median()),
        },
        "what_this_cannot_support": (
            f"Facility-level attribution. "
            f"{granularity['with_a_postcode']} of {granularity['records']} "
            f"records carry a postcode and "
            f"{granularity['with_a_street_address']} a street address, so a "
            "subsidy cannot be tied to a building. Any statement of the form "
            "'facilities like yours received X' is unsupported by this file."),
        "why_megadeals_are_not_winsorised": (
            "A data-centre award is not an outlier in a delivery-station "
            "distribution; it is a different population. Excluding it by "
            "class is correct and trimming it by value would not be."),
    }


def main() -> int:
    if not SOURCE.exists():
        raise SystemExit(f"\n  {paths.rel(SOURCE)} not found\n")
    r = collect()

    print("\n  === Amazon disclosed subsidies, Good Jobs First ===\n")
    print(f"  {r['granularity']['records']} records, "
          f"{r['year_range'][0]}-{r['year_range'][1]}, "
          f"${r['total_disclosed_usd'] / 1e6:,.0f}M disclosed\n")
    print(f"  {'class':24} {'records':>8} {'total':>11} {'median':>11}")
    for name, v in r["by_facility_class"].items():
        print(f"  {name:24} {v['records']:>8} "
              f"${v['total_usd'] / 1e6:>9,.0f}M "
              f"${v['median_usd'] / 1e6:>9,.1f}M")

    g = r["granularity"]
    print("\n  GRANULARITY -- the finding:")
    print(f"      with a county          {g['with_a_county']:>4} "
          f"of {g['records']}")
    print(f"      with a city            {g['with_a_city']:>4}")
    print(f"      with a street address  {g['with_a_street_address']:>4}")
    print(f"      with a POSTCODE        {g['with_a_postcode']:>4}"
          "   <- facility attribution is impossible")

    j = r["join_to_facility_panel"]
    print(f"\n  cities in both the subsidy file and the facility panel: "
          f"{j['overlapping_cities']} of {j['facility_cities']} "
          f"({j['share_of_facility_cities']:.1%})")

    s = r["deals_under_50m"]
    print(f"\n  deals under $50M: {s['records']} records, median "
          f"${s['median_usd'] / 1e3:,.0f}k -- the order-of-magnitude")
    print("  answer to 'is what we are being offered normal?'\n")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    write_json(OUT, r)
    print(f"  -> {paths.rel(OUT)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
