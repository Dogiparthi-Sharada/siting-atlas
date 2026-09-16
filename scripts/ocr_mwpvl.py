"""OCR the MWPVL facility tables to WORD COORDINATES, not to text.

Why coordinates and not text
----------------------------
The first version of this script wrote plain text and was thrown away after
one slice proved it cannot carry the only field we came for. MWPVL's table
rows wrap over two to four printed lines, and plain-text OCR emits them in
reading order, which splits a date across lines:

    7200 Chavenelle Road,          January          <- line 1
    Iowa  WWI2  Dubuque, Iowa, USA, 52002  120,000  9022   <- line 2

"January" and "2022" are one cell. Nothing downstream can reliably rejoin
them, because the line above a year is sometimes its month and sometimes the
previous facility's street address.

With `tesseract ... tsv` the same two words come back as

    January  left=1923 top=47
    9022     left=1969 top=119

— 46 pixels apart horizontally, both inside the Year Opened column. Columns
are recovered from x, rows from y, and the cell reassembles. So this script's
output is a TSV of words and boxes, and `ingest/mwpvl_tables.py` turns that
into facilities. Splitting it there keeps the expensive, slow, non-repeatable
half separate from the parse, which will be revised many times.

    python scripts/ocr_mwpvl.py            # all tables, priority order
    python scripts/ocr_mwpvl.py --only 069 # just the US delivery stations

Resumable, because it has to be
-------------------------------
Every strip writes its own TSV under `data/raw/mwpvl/tsv/` and is skipped if
that file exists. The first run of the text version was killed at 40% and lost
everything, which is what this fixes. Delete a strip's file to redo it.

Machine manners
---------------
One worker at `nice -n 19`, and `OMP_NUM_THREADS=1` on the child because
tesseract links OpenMP and otherwise fans out to 265% CPU regardless of the
worker count. This runs on a workstation somebody else is using; it is meant
to be unnoticeable, not fast.

Settings
--------
Measured on a 1,400-pixel sample: upscale 1x -> 23 ZIPs, 2x -> 26, 4x -> 26;
psm 4 -> 15 dates, psm 6 -> 17, psm 11 -> 5. 2x saturates on that sample and
4x is used anyway, because one worker's wall-clock time is the cheap resource
here and a recovered digit is a facility that need not be discarded.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from PIL import Image

Image.MAX_IMAGE_PIXELS = None

REPO = Path(__file__).resolve().parents[1]
IMAGES = Path("/tmp/mwpvl_tables")
OUT = REPO / "data" / "raw" / "mwpvl" / "tsv"

#: Which table each image holds, identified by OCR'ing the first 700 rows of
#: each on 2026-09-14. Ordered by value to this project, because the run is
#: long and resumable and the useful half should land first: the US delivery
#: station table is the target, and the rest-of-world tables are a bonus for
#: the coverage work rather than anything the choice model consumes.
TABLES = (
    ("img-069", "us_delivery_station"),      # 32,729 px -- THE TARGET
    ("img-092", "us_delivery_station_cont"),  # 5,909 -- its tail
    ("img-097", "us_delivery_heavy_bulky"),   # 7,434 -- separate network, 2017+
    ("img-034", "us_fulfillment_center"),     # 26,480
    ("img-062", "us_sortation_center"),       # 7,222
    ("img-103", "row_fulfillment_center"),    # 21,733 -- rest of world
    ("img-118", "row_mixed"),                 # 32,729
    ("img-141", "row_delivery_station"),      # 6,966
)

#: Pixels per strip before upscaling, and the overlap between them. A printed
#: row runs about 60 pixels, and a wrapped one up to 250, so 400 is enough
#: slack that no row is cut by both of the strips that contain it.
STRIP = 1400
OVERLAP = 400

UPSCALE = 4
PSM = 6
NICENESS = 19


def strips(height: int) -> list[tuple[int, int]]:
    """Overlapping (top, bottom) spans covering the image."""
    spans, top = [], 0
    while top < height:
        bottom = min(top + STRIP, height)
        spans.append((top, bottom))
        if bottom >= height:
            break
        top = bottom - OVERLAP
    return spans


def _ocr(job: tuple[str, str, int, int, int, int, str]) -> str:
    """OCR one strip to a TSV whose coordinates are in ORIGINAL image pixels.

    tesseract reports boxes in the upscaled crop's frame. Dividing by the
    upscale factor and adding the crop's top puts every word back where it
    sits on the page, which is what lets strips be stitched and deduplicated
    by position rather than by string equality.
    """
    src, stem, top, bottom, upscale, psm, dest = job
    out = Path(dest)
    if out.exists():
        return f"skip {out.name}"
    try:
        os.nice(NICENESS)
    except (AttributeError, OSError):
        pass

    with Image.open(src) as im:
        crop = im.crop((0, top, im.width, bottom)).convert("L")
        crop = crop.resize((crop.width * upscale, crop.height * upscale),
                           Image.LANCZOS)
    with tempfile.TemporaryDirectory() as tmp:
        png, base = Path(tmp) / "s.png", Path(tmp) / "o"
        crop.save(png)
        subprocess.run(["tesseract", str(png), str(base), "--psm", str(psm),
                        "tsv"], capture_output=True, timeout=900,
                       env={**os.environ, "OMP_NUM_THREADS": "1"})
        tsv = base.with_suffix(".tsv")
        if not tsv.exists():
            return f"FAIL {out.name}"
        rows = tsv.read_text(encoding="utf-8", errors="replace").splitlines()

    kept = [rows[0] + "\tstem\timg_top"] if rows else []
    for line in rows[1:]:
        f = line.split("\t")
        if len(f) < 12 or f[0] != "5" or not f[11].strip():
            continue
        f[6] = str(int(f[6]) // upscale)
        f[7] = str(int(f[7]) // upscale + top)
        f[8] = str(int(f[8]) // upscale)
        f[9] = str(int(f[9]) // upscale)
        kept.append("\t".join(f) + f"\t{stem}\t{top}")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(kept), encoding="utf-8")
    return f"  {out.name}  {len(kept) - 1} words"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--images", default=str(IMAGES))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--only", help="substring of an image stem, e.g. 069")
    ap.add_argument("--upscale", type=int, default=UPSCALE)
    ap.add_argument("--psm", type=int, default=PSM)
    ap.add_argument("--workers", type=int, default=1,
                    help="default 1 -- this runs on a workstation somebody "
                         "else is using")
    args = ap.parse_args()

    src_dir, out_dir = Path(args.images), Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    jobs: list[tuple] = []
    for stem, table in TABLES:
        if args.only and args.only not in stem:
            continue
        png = src_dir / f"{stem}.png"
        if not png.exists():
            print(f"  MISSING {png}")
            continue
        with Image.open(png) as im:
            height = im.height
        spans = strips(height)
        print(f"  {stem}  {table:28} {height:>7,} px  {len(spans):>3} strips")
        jobs += [(str(png), stem, t, b, args.upscale, args.psm,
                  str(out_dir / f"{table}__{t:06d}.tsv")) for t, b in spans]

    todo = [j for j in jobs if not Path(j[6]).exists()]
    print(f"\n  {len(jobs)} strips, {len(jobs) - len(todo)} already done, "
          f"{len(todo)} to do")
    print(f"  {args.upscale}x, psm {args.psm}, {args.workers} worker(s) at "
          f"nice {NICENESS}, OMP_NUM_THREADS=1\n")

    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for i, msg in enumerate(pool.map(_ocr, todo), 1):
            if not msg.startswith("skip"):
                print(f"  [{i}/{len(todo)}] {msg}", flush=True)

    print(f"\n  -> {out_dir}\n"
          "  next: python -m siting_atlas.ingest.mwpvl_tables\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
