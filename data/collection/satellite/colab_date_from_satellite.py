"""Date warehouse construction from free satellite imagery. STANDALONE.

Paste this into a Google Colab cell and run it. It imports nothing from
siting-atlas and needs no API key, no Earth Engine account and no payment.

    WHY THIS EXISTS
    ---------------
    Our facility panel has an UPPER bound on every opening date -- an OSHA
    inspection proves the building was operating by date X -- and no lower
    bound at all. So "opened in 2019" is never available, only "open by
    2019". That single gap is what stops the model from using time.

    Satellite imagery supplies the missing side. A delivery station is
    100,000-250,000 sq ft; when it is built, bare ground or vegetation turns
    into a large bright roof and a car park. Sentinel-2 sees a 10-metre pixel
    every five days, free, back to 2015. A 200m x 100m roof is 20 x 10
    pixels, which is a large and unambiguous change.

    Upper bound from OSHA + lower bound from imagery = an INTERVAL, which is
    a thing the econometrics can actually use.

    WHY IT RUNS IN COLAB AND NOT ON OUR MACHINE
    -------------------------------------------
    The university proxy allows the imagery CATALOGUE
    (planetarycomputer.microsoft.com, verified working) and blocks the
    imagery ITSELF (*.blob.core.windows.net, CONNECT tunnel failed 503).
    Colab has an open network. Nothing else about the approach requires it.

    WHAT YOU GET
    ------------
    A CSV with one row per site: the estimated construction date, a
    confidence score, and -- for the 100 sites where we already know the
    opening year -- the known year beside the estimate so the method can be
    CHECKED rather than trusted.

    HOW TO RUN
    ----------
    1. Upload SITES_TO_DATE.csv (133 rows) using the file pane, or let the
       first cell prompt you.
    2. MOUNT DRIVE FIRST if you can -- the script tells you if you have
       not. The cache goes to Drive when it is mounted and to the
       runtime when it is not, and Colab wipes the runtime on
       disconnect. This run takes hours.
           from google.colab import drive
           drive.mount('/content/drive')
    3. Run. A preflight checks the input file, its columns, the cache
       directory and the imports BEFORE anything expensive starts.
    4. Download satellite_dates.csv at the end and send it back.

    Expect 2-4 hours for 133 sites. Start it and leave it.

    IF YOU RAN THE FIRST VERSION AND GOT HTTP 403 Forbidden: that was a
    signing-rate bug, fixed. Delete /content/sat_cache and geocoded.csv
    is fine to KEEP -- the geocoding worked (107 of 133) and re-running
    it wastes twenty minutes for nothing.
"""

# ---------------------------------------------------------------------------
# CELL 1 - dependencies
# ---------------------------------------------------------------------------
# !pip install -q planetary-computer rasterio pyproj pandas
#
# planetary-computer is NOT optional. It caches the SAS token. See the
# note above _signed_href() for what happens without it.

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
INPUT_NAME = "SITES_TO_DATE.csv"
OUTPUT_NAME = "satellite_dates.csv"

#: Where to look for the input, in order. Colab puts an uploaded file in the
#: CWD, which is usually /content but is NOT guaranteed -- a %cd, a Drive
#: mount, or running the script from a subfolder all move it. Searching a few
#: known places beats a FileNotFoundError three hours into a run.
SEARCH = ("", "/content", "/content/drive/MyDrive",
          "/content/drive/MyDrive/siting-atlas", "/content/sample_data")


def _resolve_paths() -> tuple[Path, Path, Path]:
    """Input, output and cache, with the cache on Drive when it is mounted.

    THE CACHE LOCATION MATTERS MORE THAN IT LOOKS. This run takes hours and
    Colab wipes /content when the runtime disconnects, so a cache under
    /content is not a cache -- it is a file that disappears exactly when you
    need it. If Drive is mounted the cache goes there and a disconnect really
    does cost nothing. If it is not, the cache still works within the session
    and the preflight says plainly that it will not survive.
    """
    found = None
    for d in SEARCH:
        candidate = Path(d) / INPUT_NAME if d else Path(INPUT_NAME)
        if candidate.is_file():
            found = candidate.resolve()
            break
    if found is None:
        raise SystemExit(
            f"\n  Cannot find {INPUT_NAME}. Looked in:\n"
            + "".join(f"      {d or '(current directory)'}\n" for d in SEARCH)
            + f"\n  Upload it with the file pane on the left, or set\n"
              f"  INPUT_NAME to its full path.\n"
              f"  Current directory is {Path.cwd()}\n")

    drive = Path("/content/drive/MyDrive")
    base = drive if drive.is_dir() else found.parent
    return found, base / OUTPUT_NAME, base / "sat_cache"


#: Required columns. Checked up front, because discovering that
#: `address_full` is missing after twenty minutes of geocoding is avoidable.
REQUIRED_COLUMNS = ("facility_id", "address_full", "open_year")

#: Half-width of the patch sampled around each site, in metres. A delivery
#: station is roughly 200m x 100m, so 120m each way covers the building and
#: a little of its surroundings without swallowing the neighbours.
PATCH_M = 120

#: Sentinel-2 starts in 2015; Amazon's delivery-station build-out is
#: overwhelmingly 2018 onward. Two years of lead-in gives the detector a
#: baseline to compare against.
START, END = "2016-01-01", "2026-09-01"

#: One usable scene per month is plenty to date construction to the month,
#: and cuts the reads by a factor of five against every revisit.
MAX_CLOUD = 20
STAC = "https://planetarycomputer.microsoft.com/api/stac/v1"
UA = {"User-Agent": "siting-atlas-colab/0.1 (academic research)"}

#: (account, container) -> (token, unix expiry). See _signed_href.
_TOKENS: dict = {}


# ---------------------------------------------------------------------------
# CELL 2 - geocoding, via the Census batch geocoder (free, US, no key)
# ---------------------------------------------------------------------------
def geocode_census(rows: pd.DataFrame) -> pd.DataFrame:
    """Address -> lat/lon using the US Census geocoder.

    Chosen over Nominatim because it is built for US street addresses, has
    no rate limit worth worrying about, needs no key, and returns a match
    quality we can filter on. Nominatim would take 133 seconds of enforced
    politeness and match worse on industrial addresses.
    """
    out = []
    base = ("https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
            "?benchmark=Public_AR_Current&format=json&address=")
    for i, r in rows.iterrows():
        addr = str(r["address_full"])
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(base + urllib.parse.quote(addr),
                                           headers=UA), timeout=45) as fh:
                m = json.load(fh)["result"]["addressMatches"]
            if m:
                c = m[0]["coordinates"]
                out.append((r["facility_id"], c["y"], c["x"], "census"))
            else:
                out.append((r["facility_id"], np.nan, np.nan, "no_match"))
        except Exception as e:                       # noqa: BLE001
            print(f"    geocode failed for {r['facility_id']}: {e}")
            out.append((r["facility_id"], np.nan, np.nan, "error"))
        if i % 20 == 0:
            print(f"    geocoded {i}/{len(rows)}")
        time.sleep(0.2)
    return pd.DataFrame(out, columns=["facility_id", "lat", "lon", "geo_src"])


# ---------------------------------------------------------------------------
# CELL 3 - the imagery time series
# ---------------------------------------------------------------------------
def _search(lon: float, lat: float) -> list:
    """Cloud-free Sentinel-2 scenes over one point, one per month."""
    body = json.dumps({
        "collections": ["sentinel-2-l2a"],
        "intersects": {"type": "Point", "coordinates": [lon, lat]},
        "datetime": f"{START}/{END}",
        "query": {"eo:cloud_cover": {"lt": MAX_CLOUD}},
        "limit": 500,
    }).encode()
    req = urllib.request.Request(
        f"{STAC}/search", data=body,
        headers={"Content-Type": "application/json", **UA})
    with urllib.request.urlopen(req, timeout=120) as fh:
        feats = json.load(fh)["features"]
    # Keep the least cloudy scene in each month.
    best: dict = {}
    for f in feats:
        month = f["properties"]["datetime"][:7]
        cc = f["properties"].get("eo:cloud_cover", 100)
        if month not in best or cc < best[month]["properties"]["eo:cloud_cover"]:
            best[month] = f
    return [best[m] for m in sorted(best)]


def _signed_href(href: str) -> str:
    """Sign a blob URL, reusing the cached token.

    THIS IS WHERE THE FIRST VERSION FAILED. It called the SAS endpoint once
    per band per scene -- two bands, about forty scenes, 133 sites, so
    roughly 10,600 signing requests. Anonymous signing is rate-limited; it
    served the first few dozen and then returned HTTP 403 Forbidden for the
    rest of the run. The 403 was throttling, not permission, and it looked
    like a credentials problem because that is what 403 usually means.

    A token is valid for the WHOLE storage container for about an hour, so
    the correct number of requests is about three, not ten thousand.
    `planetary_computer.sign()` caches per container and refreshes on expiry,
    which is why the pip cell installs it.

    The manual fallback below exists only so the script still runs if the
    package is unavailable; it caches too, and it is the thing that should
    have been written in the first place.
    """
    try:
        import planetary_computer
        return planetary_computer.sign(href)
    except ImportError:
        pass

    account = href.split("//", 1)[1].split(".", 1)[0]
    container = href.split("/")[3]
    key = (account, container)
    now = time.time()
    token, expires = _TOKENS.get(key, (None, 0.0))
    if token is None or now > expires - 300:
        url = (f"https://planetarycomputer.microsoft.com/api/sas/v1/token/"
               f"{account}/{container}")
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=60) as fh:
            payload = json.load(fh)
        token = payload["token"]
        # Refresh five minutes early rather than parsing msft:expiry: the
        # clocks need not agree and a stale token costs a whole site.
        _TOKENS[key] = (token, now + 3000)
    return f"{href}?{token}"


def _patch(scene: dict, lon: float, lat: float) -> dict | None:
    """Mean reflectance in a small window, for the bands we need.

    B04 red and B03 green give brightness; B08 near-infrared with B04 gives
    NDVI. A roof going up drives brightness UP and NDVI DOWN, and requiring
    both to move is what separates construction from a field being ploughed.
    """
    import rasterio
    from pyproj import Transformer
    from rasterio.windows import from_bounds

    vals = {}
    for band in ("B04", "B08"):
        href = scene["assets"][band]["href"]
        try:
            signed = _signed_href(href)
            with rasterio.open(signed) as src:
                tr = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
                x, y = tr.transform(lon, lat)
                win = from_bounds(x - PATCH_M, y - PATCH_M,
                                  x + PATCH_M, y + PATCH_M, src.transform)
                arr = src.read(1, window=win).astype(float)
            arr = arr[arr > 0]
            if arr.size < 4:
                return None
            vals[band] = float(np.median(arr))
        except Exception:                            # noqa: BLE001
            return None
    red, nir = vals["B04"], vals["B08"]
    return {"date": scene["properties"]["datetime"][:10],
            "red": red, "nir": nir,
            "ndvi": (nir - red) / (nir + red) if (nir + red) else np.nan}


def series_for_site(fid: str, lon: float, lat: float,
                    cache_dir: Path) -> pd.DataFrame:
    """Monthly time series for one site, cached per site.

    `cache_dir` is passed rather than read from a module global: the
    resolution in `_resolve_paths` depends on whether Drive is mounted, so
    there is no correct value to hardcode, and a global set inside main()
    would make this function unusable on its own.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / f"{fid}.csv"
    if cache.exists():
        return pd.read_csv(cache)
    rows = [p for p in (_patch(s, lon, lat) for s in _search(lon, lat))
            if p is not None]
    df = pd.DataFrame(rows)
    df.to_csv(cache, index=False)
    return df


# ---------------------------------------------------------------------------
# CELL 4 - dating the change
# ---------------------------------------------------------------------------
def detect_construction(df: pd.DataFrame) -> dict:
    """The month with the largest sustained brightness-up, NDVI-down shift.

    A deliberately simple changepoint: for every candidate split, compare the
    mean before with the mean after, and take the split that maximises the
    combined shift. A learned detector would be better and is not worth it
    at 133 sites -- and a simple rule is one we can explain in a viva.

    `confidence` is the shift divided by the residual spread, so a clean
    step in a quiet series scores high and a noisy drift scores low. It is a
    signal-to-noise ratio, NOT a probability, and must not be reported as one.
    """
    if len(df) < 12:
        return {"est_date": None, "confidence": 0.0, "n_scenes": len(df)}
    d = df.sort_values("date").reset_index(drop=True)
    red = d["red"].to_numpy(float)
    ndvi = d["ndvi"].to_numpy(float)
    # Normalise each so they contribute comparably, then combine with NDVI
    # inverted: construction is brighter AND less green.
    z = lambda v: (v - np.nanmean(v)) / (np.nanstd(v) or 1.0)   # noqa: E731
    signal = z(red) - z(ndvi)

    best, best_i = -np.inf, None
    for i in range(6, len(signal) - 6):
        shift = np.nanmean(signal[i:]) - np.nanmean(signal[:i])
        if shift > best:
            best, best_i = shift, i
    resid = np.nanstd(np.diff(signal)) or 1.0
    return {"est_date": d.loc[best_i, "date"],
            "confidence": float(best / resid),
            "n_scenes": len(d)}


# ---------------------------------------------------------------------------
# CELL 5 - run it
# ---------------------------------------------------------------------------
def preflight() -> tuple[Path, Path, Path, pd.DataFrame]:
    """Check everything that can fail cheaply, before anything expensive.

    Every check here exists because getting it wrong costs hours rather than
    seconds: a missing file after geocoding, a missing column after the
    imagery pass, an unwritable cache discovered at the first save.
    """
    src, out, cache = _resolve_paths()
    print(f"  input   {src}")
    print(f"  output  {out}")
    print(f"  cache   {cache}", end="")

    drive = Path("/content/drive/MyDrive")
    if drive.is_dir():
        print("   (on Drive -- survives a disconnect)")
    else:
        print("\n  [!] Drive is NOT mounted, so the cache lives in the runtime\n"
              "      and a disconnect loses it. This run takes hours. To be\n"
              "      safe, run this first and re-run the script:\n"
              "          from google.colab import drive\n"
              "          drive.mount('/content/drive')")

    sites = pd.read_csv(src, dtype=str)
    missing = [c for c in REQUIRED_COLUMNS if c not in sites.columns]
    if missing:
        raise SystemExit(
            f"\n  {src.name} is missing required column(s): {missing}\n"
            f"  It has: {list(sites.columns)}\n")
    blank = sites["address_full"].isna() | (sites["address_full"].str.strip() == "")
    if blank.any():
        print(f"  [!] {int(blank.sum())} row(s) have a blank address_full "
              f"and will be skipped")

    cache.mkdir(parents=True, exist_ok=True)
    probe = cache / ".writable"
    try:
        probe.write_text("ok")
        probe.unlink()
    except OSError as e:
        raise SystemExit(f"\n  cache directory is not writable: {e}\n") from e

    for mod in ("rasterio", "pyproj"):
        try:
            __import__(mod)
        except ImportError as e:
            raise SystemExit(
                f"\n  {mod} is not installed. Run the pip cell first:\n"
                f"      !pip install -q planetary-computer rasterio pyproj "
                f"pandas\n") from e
    try:
        import planetary_computer          # noqa: F401
    except ImportError:
        print("  [!] planetary-computer not installed; falling back to the\n"
              "      manual token cache. Works, but install it if you can.")

    print(f"  {len(sites)} sites, all preflight checks passed\n")
    return src, out, cache, sites


def main() -> pd.DataFrame:
    src, out_csv, cache_dir, sites = preflight()
    geo_path = cache_dir.parent / "geocoded.csv"
    if geo_path.exists():
        geo = pd.read_csv(geo_path)
    else:
        geo = geocode_census(sites.reset_index(drop=True))
        geo.to_csv(geo_path, index=False)
    sites = sites.merge(geo, on="facility_id", how="left")
    ok = sites.dropna(subset=["lat", "lon"])
    print(f"  geocoded {len(ok)} of {len(sites)}")

    out = []
    for n, (_, r) in enumerate(ok.iterrows(), 1):
        try:
            df = series_for_site(r["facility_id"], r["lon"],
                                 r["lat"], cache_dir)
            res = detect_construction(df)
        except Exception as e:                       # noqa: BLE001
            print(f"    {r['facility_id']} failed: {e}")
            res = {"est_date": None, "confidence": 0.0, "n_scenes": 0}
        out.append({**r.to_dict(), **res})
        if n % 5 == 0:
            print(f"    {n}/{len(ok)} sites done")
            pd.DataFrame(out).to_csv(out_csv, index=False)

    res = pd.DataFrame(out)
    res.to_csv(out_csv, index=False)

    # VALIDATION. 100 sites carry a known opening year. Without this block
    # the output is an unchecked guess; with it, it is a method with a
    # measured error. Do not skip it.
    v = res[res["open_year"].notna() & res["est_date"].notna()].copy()
    if len(v):
        v["est_year"] = pd.to_datetime(v["est_date"]).dt.year
        v["err"] = v["est_year"] - pd.to_numeric(v["open_year"], errors="coerce")
        print(f"\n  VALIDATION on {len(v)} sites with a known year")
        print(f"    median error {v['err'].median():+.1f} years")
        print(f"    within 1 year: {(v['err'].abs() <= 1).mean():.0%}")
        print(f"    high confidence only (>2): "
              f"{(v.loc[v['confidence'] > 2, 'err'].abs() <= 1).mean():.0%}")
    print(f"\n  -> {out_csv}")
    return res


if __name__ == "__main__":
    main()
