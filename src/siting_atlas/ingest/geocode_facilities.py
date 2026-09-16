"""Coordinates for the facility panel, via the free Census batch geocoder.

`AUDIT_2026_09_14.md` §1.9: zero of 700 facilities in a siting atlas carry a
coordinate. Rationale, results and caveats: `docs/data/GEOCODING.md`. The
`geographies` endpoint is used rather than `locations` because for the same
one request it also returns the state FIPS of the block the RETURNED POINT
falls in, which makes the wrong-state check free.

IT NEVER INVENTS A COORDINATE. `Tie` and `No_Match` get none, and a row
whose address was blank before we started says so rather than blaming the
geocoder. The ZCTA centroid appears only in `fallback_*` columns behind an
explicit `fallback_method` flag, never in `latitude`/`longitude`. WRITES A
NEW FILE; `national_facilities_expanded.csv` is never touched.
"""

from __future__ import annotations

import argparse
import csv
import io
import time
from pathlib import Path

import pandas as pd
import requests

from ..common import paths
from ..common.logging_setup import get_logger
from ..warehouse.geo_keys import FIPS_STATE

_log = get_logger("ingest.geocode_facilities")

ENDPOINT = "https://geocoding.geo.census.gov/geocoder/geographies/addressbatch"
BENCHMARK = "Public_AR_Current"
VINTAGE = "Current_Current"

PANEL = paths.EXTERNAL / "facility_panel" / "national_facilities_expanded.csv"
OUT = paths.EXTERNAL / "facility_panel" / "geocoded_expanded.csv"

#: Rows per POST. 10,000 allowed, but a chunk is the unit of retry.
CHUNK = 200

#: No_Match/Tie rows stop after `match_status`, so the reader pads.
RESPONSE_COLUMNS = ("row_id", "input_address", "match_status", "match_quality",
                    "matched_address", "coordinates", "tiger_line_id", "side",
                    "returned_state_fips", "county_fips", "tract", "block")

#: `latitude`/`longitude` are the geocode; `fallback_*` never merges in.
OUTPUT_COLUMNS = (
    "facility_id", "input_address", "match_status", "match_quality",
    "matched_address", "latitude", "longitude", "geocode_method",
    "tiger_line_id", "side", "returned_state_fips", "returned_state",
    "county_fips", "tract", "block", "claimed_state", "state_agrees",
    "claimed_zip", "returned_zip", "zip_agrees", "zcta_of_point",
    "zcta_agrees", "fallback_latitude", "fallback_longitude",
    "fallback_method", "failure_reason")


def _clean(value: object) -> str:
    """One CSV field the Census parser will accept.

    Commas/quotes are stripped, not escaped: a quoted comma shifts every
    later column by one, silently turning a state into a ZIP.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).replace(",", " ").replace('"', " ").strip()


def build_batch_input(panel: pd.DataFrame) -> pd.DataFrame:
    """The five-column, header-less frame the batch geocoder expects."""
    return pd.DataFrame({
        "row_id": panel["facility_id"].map(_clean),
        "street": panel["site_address"].map(_clean),
        "city": panel["city"].map(_clean),
        "state": panel["state"].map(_clean),
        "zip": panel["zip"].map(_clean),
    })


def _to_csv_bytes(frame: pd.DataFrame) -> bytes:
    buf = io.StringIO()
    frame.to_csv(buf, header=False, index=False, quoting=csv.QUOTE_NONE)
    return buf.getvalue().encode("utf-8")


def post_chunk(chunk: pd.DataFrame, attempts: int = 3,
               timeout: int = 180) -> list[list[str]]:
    """POST one chunk, or raise after `attempts`.

    Under load the service returns an HTML page, not a 5xx, so a bad
    response is caught by the row count rather than the status code.
    """
    files = {"addressFile": ("a.csv", _to_csv_bytes(chunk), "text/csv")}
    data = {"benchmark": BENCHMARK, "vintage": VINTAGE}
    last: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            resp = requests.post(ENDPOINT, files=files, data=data,
                                 timeout=timeout)
            resp.raise_for_status()
            rows = list(csv.reader(io.StringIO(resp.text)))
            rows = [r for r in rows if r]
            if len(rows) != len(chunk):
                raise ValueError(
                    f"asked for {len(chunk)} rows, got {len(rows)}")
            return rows
        except Exception as exc:                          # noqa: BLE001
            last = exc
            _log.warning("chunk attempt %d/%d failed: %s",
                         attempt, attempts, exc)
            time.sleep(2 * attempt)
    raise RuntimeError(f"chunk failed after {attempts} attempts: {last}")


def geocode(batch: pd.DataFrame, chunk_size: int = CHUNK) -> pd.DataFrame:
    """Every row through the service, keyed on `row_id`.

    Input order is NOT preserved, so results are joined on the id, never
    concatenated positionally — that error would give Anchorage's coordinate
    to a facility in Napa and nothing downstream would notice.
    """
    parsed: list[list[str]] = []
    for start in range(0, len(batch), chunk_size):
        chunk = batch.iloc[start:start + chunk_size]
        parsed.extend(post_chunk(chunk))
        _log.info("geocoded %d/%d", min(start + chunk_size, len(batch)),
                  len(batch))
    width = len(RESPONSE_COLUMNS)
    padded = [(r + [""] * width)[:width] for r in parsed]
    return pd.DataFrame(padded, columns=list(RESPONSE_COLUMNS))


def _split_coordinates(frame: pd.DataFrame) -> pd.DataFrame:
    """`"-149.868,61.167"` -> numeric lat/lon. LONGITUDE COMES FIRST;
    reversing it puts every US facility in the Indian Ocean.
    """
    parts = frame["coordinates"].str.split(",", n=1, expand=True)
    if parts.shape[1] < 2:
        parts = parts.reindex(columns=[0, 1])
    frame["longitude"] = pd.to_numeric(parts[0], errors="coerce")
    frame["latitude"] = pd.to_numeric(parts[1], errors="coerce")
    return frame


def zcta_of_points(frame: pd.DataFrame) -> pd.Series:
    """Which ZCTA polygon contains each point. TIGER 2020, not the
    geocoder, so it is an independent opinion; covers 25,022 ZCTAs, and a
    blank means "outside the shapefile", not "wrong".
    """
    import geopandas as gpd

    geom_path = paths.INTERIM / "zcta_geom.parquet"
    out = pd.Series("", index=frame.index, dtype=object)
    ok = frame["latitude"].notna() & frame["longitude"].notna()
    if not ok.any() or not geom_path.exists():
        return out
    polys = gpd.read_parquet(geom_path)
    geom = gpd.points_from_xy(frame.loc[ok, "longitude"],
                              frame.loc[ok, "latitude"])
    pts = gpd.GeoDataFrame(frame.loc[ok, []], geometry=geom, crs=polys.crs)
    joined = gpd.sjoin(pts, polys, how="left", predicate="within")
    joined = joined[~joined.index.duplicated(keep="first")]
    out.loc[ok] = joined["ZCTA5CE20"].fillna("").astype(str)
    return out


def zcta_centroids(zips: pd.Series) -> pd.DataFrame:
    """Gazetteer ZCTA centroids, for the explicitly-flagged fallback only."""
    cols = ["fallback_latitude", "fallback_longitude"]
    gaz_path = paths.INTERIM / "gazetteer.parquet"
    if not gaz_path.exists():
        return pd.DataFrame(index=zips.index, columns=cols)
    gaz = pd.read_parquet(gaz_path).set_index("zcta")
    return pd.DataFrame(
        dict(zip(cols, (zips.map(gaz["latitude"]),
                        zips.map(gaz["longitude"])), strict=True)),
        index=zips.index)


def _agree(out: pd.DataFrame, got: str, claimed: str,
           mask: pd.Series) -> pd.Series:
    """Does the geocoder's answer match the panel's claim? A blank cannot
    disagree with anything, so it is NA, not False — counting "we never
    knew" as a failure would inflate every rate in the report.
    """
    res = pd.Series(pd.NA, index=out.index, dtype=object)
    ok = mask & (out[got] != "") & (out[claimed] != "")
    res[ok] = out.loc[ok, got] == out.loc[ok, claimed]
    return res


def _failure_reason(row: pd.Series) -> str:
    """Why a row has no coordinate. "Could not find it" and "we never had
    an address" are different defects needing different fixes.
    """
    if row["match_status"] == "Match":
        return ""
    if not row["sent_street"]:
        return "no_street_address_in_panel"
    if row["match_status"] == "Tie":
        return "ambiguous_tie_no_coordinate_returned"
    if not row["sent_city"] and not row["sent_state"]:
        return "no_match_and_city_state_also_blank"
    return "no_match_street_not_in_tiger"


def assemble(panel: pd.DataFrame, raw: pd.DataFrame,
             batch: pd.DataFrame) -> pd.DataFrame:
    """Join the response back onto the panel and run every sanity check."""
    sent = batch.rename(columns={c: f"sent_{c}" for c in
                                 ("street", "city", "state", "zip")})
    out = raw.merge(sent, on="row_id", how="right")
    out = _split_coordinates(out).rename(columns={"row_id": "facility_id"})
    claimed = panel.set_index("facility_id")
    out["claimed_state"] = out["facility_id"].map(claimed["state"]).fillna("")
    out["claimed_zip"] = out["facility_id"].map(claimed["zip"]).fillna("")

    out["returned_state"] = (out["returned_state_fips"].str.zfill(2)
                             .map(FIPS_STATE).fillna(""))
    # The geocoder's own normalised ZIP. Kept because comparing it with the
    # panel's ZIP is what exposed 28 wrong postcodes — see
    # docs/data/GEOCODING.md. It is evidence, not a correction.
    out["returned_zip"] = (out["matched_address"].fillna("")
                           .str.extract(r"(\d{5})\s*$")[0].fillna(""))
    out["zcta_of_point"] = zcta_of_points(out)

    matched = out["match_status"] == "Match"
    out["state_agrees"] = _agree(out, "returned_state", "claimed_state",
                                 matched)
    out["zip_agrees"] = _agree(out, "returned_zip", "claimed_zip", matched)
    out["zcta_agrees"] = _agree(out, "zcta_of_point", "claimed_zip", matched)

    out["geocode_method"] = ""
    out.loc[matched, "geocode_method"] = "census_batch_geographies"
    out["failure_reason"] = out.apply(_failure_reason, axis=1)

    # Cleared for anything not a clean Match, so no consumer can pick up a
    # Tie's leftovers.
    out.loc[~matched, ["latitude", "longitude"]] = pd.NA

    cent = zcta_centroids(out["claimed_zip"])
    out = pd.concat([out, cent], axis=1)
    out["fallback_method"] = ""
    need = ~matched & out["fallback_latitude"].notna()
    out.loc[need, "fallback_method"] = "zcta_centroid_gazetteer"
    out.loc[matched, ["fallback_latitude", "fallback_longitude"]] = pd.NA

    return out[list(OUTPUT_COLUMNS)]


def summarise(out: pd.DataFrame) -> str:
    """The numbers that decide whether this file may be used."""
    n, c = len(out), out["match_status"].value_counts()
    m = int(c.get("Match", 0))
    exact = int((out["match_quality"] == "Exact").sum())

    def no(col: str) -> int:
        return int((out[col] == False).sum())                  # noqa: E712

    lines = [f"rows {n} | Match {m} ({m / n:.1%}) | Exact {exact} | "
             f"Non_Exact {m - exact} | No_Match {int(c.get('No_Match', 0))} "
             f"| Tie {int(c.get('Tie', 0))}",
             f"coordinate outside claimed state {no('state_agrees')}",
             f"coordinate outside claimed ZCTA  {no('zcta_agrees')}",
             f"panel ZIP != geocoder ZIP        {no('zip_agrees')} "
             f"(a panel defect, not a geocode defect)",
             "failure reasons:"]
    lines += [f"  {r:38s} {k}"
              for r, k in out["failure_reason"].value_counts().items() if r]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--panel", type=Path, default=PANEL)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--chunk", type=int, default=CHUNK)
    ap.add_argument("--write-input", type=Path, default=None,
                    help="write the header-less batch input file and stop, "
                         "for submission from a machine with network access")
    args = ap.parse_args(argv)
    panel = pd.read_csv(args.panel, dtype=str)
    batch = build_batch_input(panel)
    if args.write_input:
        batch.to_csv(args.write_input, header=False, index=False,
                     quoting=csv.QUOTE_NONE)
        _log.info("wrote %d rows to %s", len(batch), args.write_input)
        return 0

    raw = geocode(batch, chunk_size=args.chunk)
    out = assemble(panel, raw, batch)
    out.to_csv(args.out, index=False)
    _log.info("wrote %s", args.out)
    print(summarise(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
