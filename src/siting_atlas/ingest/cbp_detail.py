"""County Business Patterns, ZIP x industry: the warehousing covariate.

Why this source
---------------
The conditional choice model fitted on households, land area and
establishments does not beat a plain population ranking — the difference is
one decision in forty. It cannot, because all three covariates are proxies
for "how much stuff is here". To separate the model from a population map it
needs a variable that is NOT population but does drive siting.

The binding physical constraint on a delivery station is industrially-zoned
land with a suitable building on it. You cannot site one in a residential
ZIP however many households it has. CBP's ZIP-by-industry file measures the
closest free proxy for that: how many warehousing establishments (NAICS 493)
already operate in the ZIP.

    python -m siting_atlas.ingest.cbp_detail

The code format, which is easy to get wrong
-------------------------------------------
CBP pads NAICS to six characters with ``/`` and ``-``, and the file is
HIERARCHICAL — every establishment is counted at each level of its code:

    ------   all industries        \\
    48----   transportation         |  the SAME establishment
    493///   warehousing/storage    |  appears at all five
    4931//   warehousing            |  levels
    49311/   general warehousing    |
    493110   general warehousing   /

So ``493///`` is the warehousing total for the ZIP and the sub-codes must NOT
be summed on top of it. Doing so would multiply the count by roughly four.

The endogeneity trap, and the reason for seven vintages
-------------------------------------------------------
An Amazon delivery station IS a warehousing establishment. If it opened
before the CBP vintage we read, it is counted in its own ZIP's total, and
using that total to predict where Amazon built would be circular — the
covariate would contain the outcome.

The fix is to give every facility a covariate measured BEFORE it opened. We
hold vintages 2016-2022 and select, per facility, the latest vintage strictly
earlier than its opening year. A facility opening in 2021 is scored on CBP
2020; one opening in 2023 or later is scored on 2022, the most recent
available. Facilities opening in 2017 or earlier have no clean vintage and
are reported rather than silently scored.
"""

from __future__ import annotations

import argparse
import csv
import io
import zipfile
from pathlib import Path

import pandas as pd

from ..common import paths
from ..common.context import init_run
from ..common.logging_setup import configure, get_logger
from ..common.trace import artefact, metric, step, traced_layer

_log = get_logger("ingest.cbp_detail")

RAW = paths.RAW / "cbp_zip_detail"
OUT = paths.INTERIM / "cbp_detail.parquet"

#: Three-digit NAICS groups worth carrying, all EXTENSIVE counts so they may
#: enter the choice model's ln(beta'a) term. Keys are the padded CBP code.
#:
#: 492 is included but flagged: couriers and messengers is the industry an
#: Amazon delivery station most plausibly files under, so it carries a
#: sharper version of the same circularity risk as 493 and should be used
#: only with the vintage lag below.
WANTED = {
    "493///": "warehousing_establishments",
    "484///": "trucking_establishments",
    "492///": "courier_establishments",
    "------": "all_establishments",
}

#: Vintages that are comparable to each other. 2016 is on disk and is
#: DELIBERATELY EXCLUDED.
#:
#: Measured when the series was first built: the 2016 file holds 8,418,283
#: rows against 2,870,579 for 2017, and reports warehousing (493///) in 6,165
#: ZIPs at a median of 1 establishment against 1,794 ZIPs at a median of 4
#: from 2017 on. Establishment counts in the real economy do not fall by
#: two-thirds in one year; this is a change in what Census publishes, not in
#: what exists. The cause was not established and is not guessed at here.
#:
#: Splicing the two would put a large artificial step in the covariate
#: exactly where the panel begins, so 2016 is dropped and the six facilities
#: that open in 2017 or earlier are reported as unscoreable rather than
#: scored on an incomparable vintage.
USABLE_VINTAGES = (2017, 2018, 2019, 2020, 2021, 2022)
EARLIEST = min(USABLE_VINTAGES)

__all__ = ["WANTED", "extract", "load", "vintage_for", "main"]


def vintage_for(open_year: int, available: list[int]) -> int | None:
    """The latest vintage strictly BEFORE `open_year`, or None.

    Strictly before, not "at or before": CBP's reference period is the week
    of 12 March, so a facility opening in January 2022 would already appear
    in the 2022 file. Requiring a strictly earlier vintage costs one year of
    covariate freshness and removes the ambiguity entirely.
    """
    earlier = [y for y in available if y < open_year]
    return max(earlier) if earlier else None


def extract(path: Path) -> pd.DataFrame:
    """One row per (zip, vintage) with the wanted industry counts as columns.

    Streams the member rather than loading it: the 2016 file is 2.9 million
    rows and we keep four of them per ZIP.
    """
    year = 2000 + int(path.stem[3:5])
    rows: dict[str, dict] = {}
    with zipfile.ZipFile(path) as z:
        member = z.namelist()[0]
        with z.open(member) as fh:
            stream = io.TextIOWrapper(fh, "utf-8", errors="replace")
            reader = csv.reader(stream)
            header = next(reader)
            i_zip = header.index("zip")
            i_naics = header.index("naics")
            i_est = header.index("est")
            for row in reader:
                code = row[i_naics].strip()
                column = WANTED.get(code)
                if column is None:
                    continue
                zcta = row[i_zip].strip().zfill(5)
                rec = rows.setdefault(zcta, {"zcta": zcta, "cbp_year": year})
                try:
                    rec[column] = int(row[i_est])
                except ValueError:
                    rec[column] = 0

    frame = pd.DataFrame(list(rows.values()))
    for column in WANTED.values():
        if column not in frame.columns:
            frame[column] = 0
        # A ZIP with no row for an industry has zero establishments in it.
        # That is a real zero, not a missing value, and treating it as NULL
        # would drop exactly the residential ZIPs the covariate exists to
        # distinguish from industrial ones.
        frame[column] = frame[column].fillna(0).astype(int)
    with_493 = int((frame["warehousing_establishments"] > 0).sum())
    _log.info("%d: %d ZIPs, %d with any warehousing establishment",
              year, len(frame), with_493)
    return frame


def load() -> pd.DataFrame:
    """Every vintage on disk, stacked, one row per (zcta, cbp_year)."""
    files = [f for f in sorted(RAW.glob("zbp??detail.zip"))
             if 2000 + int(f.stem[3:5]) in USABLE_VINTAGES]
    skipped = [f.name for f in sorted(RAW.glob("zbp??detail.zip"))
               if 2000 + int(f.stem[3:5]) not in USABLE_VINTAGES]
    if skipped:
        _log.warning("skipping %s: not comparable with the 2017+ series, "
                     "see USABLE_VINTAGES", ", ".join(skipped))
    if not files:
        raise SystemExit(
            f"no usable CBP detail files in {paths.rel(RAW)}/ — see the "
            "module docstring for the URL pattern")
    return pd.concat([extract(f) for f in files], ignore_index=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    paths.ensure_dirs()
    init_run()
    configure()

    with (traced_layer("L1", "CBP ZIP x industry detail"),
          step("cbp_detail:extract")):
        frame = load()
        metric("cbp_detail_rows", len(frame))
        metric("cbp_detail_vintages", int(frame["cbp_year"].nunique()))

    out = Path(args.out) if args.out else OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(out, index=False)
    artefact(out, rows=len(frame))

    print(f"\n  {len(frame):,} (zcta, year) rows across "
          f"{frame['cbp_year'].nunique()} vintages -> {paths.rel(out)}\n")
    print(f"  {'year':>6}{'ZIPs':>10}{'with 493':>10}{'median 493>0':>14}")
    for year, g in frame.groupby("cbp_year"):
        nz = g[g["warehousing_establishments"] > 0]
        print(f"  {year:>6}{len(g):>10,}{len(nz):>10,}"
              f"{nz['warehousing_establishments'].median():>14.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
