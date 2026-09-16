"""Standalone OCR of the MWPVL facility tables. Runs on the grid, Python 3.6.

Standalone means standalone: this imports Pillow and the standard library and
nothing else. It does not import siting_atlas, it does not read the project
config, and it can be copied to any machine on its own.

    bash tools/ocr/README.md
    source /tmp/mwpvl_venv/bin/activate
    python tools/ocr/grid_ocr.py --pdf "<the MWPVL pdf>" --workers 14

Output is `data/raw/mwpvl/tsv/<image>__<offset>.tsv`, one file per strip,
which is then parsed by `ingest/mwpvl_tables.py` back in the project venv.

PYTHON 3.6 -- the grid ships 3.6.8 at /bin/python
-------------------------------------------------
Four things that are second nature on 3.7+ are syntax or runtime errors here,
and every one of them fails at a point that does not name the interpreter:

    from __future__ import annotations     3.7+   SyntaxError on import
    subprocess.run(capture_output=True)    3.7+   TypeError at the first call
    subprocess.run(text=True)              3.7+   TypeError at the first call
    @dataclass                             3.7+   ImportError

So: no postponed annotations, `stdout=PIPE`, `universal_newlines=True`, and
plain tuples. Do not "modernise" this file -- it is the one that has to run
on the old interpreter.

WHY COORDINATES AND NOT TEXT
----------------------------
MWPVL's rows wrap over two to four printed lines, so plain-text OCR splits a
date across lines and nothing downstream can rejoin them reliably:

    7200 Chavenelle Road,          January
    Iowa  WWI2  Dubuque, Iowa, USA, 52002  120,000  9022

"January" and "2022" are one cell. In `tsv` mode they come back as
`January left=1923 top=47` and `9022 left=1969 top=119` -- 46 pixels apart in
x, both inside the Year Opened column -- and the cell reassembles from
geometry. Opening dates are the only reason this document is being mined, so
the text mode was measured, found unable to carry them, and abandoned.

WHICH IMAGES ARE TABLES
-----------------------
An earlier run kept only images taller than 5,000 px and silently lost five
tables: Amazon Fresh DC (1,576), Whole Foods (665), Fresh Hub (3,744),
Inbound Cross Dock (3,975) and Air Gateway (1,753). The filter here is on
WIDTH instead, because every table in this document is rendered 803-828 px
wide while the furniture -- banners at 1137x42, the logo at 2525x254, the
per-page decoration at 1464x1103 -- is not. Height is only used to drop
slivers. Getting this wrong is invisible: you simply get fewer facilities and
no error.

RESUMABLE
---------
Each strip writes its own file and is skipped if that file exists, so the job
survives being killed, and a partial run can be parsed while the rest
continues. Delete a strip's TSV to redo just that strip.
"""

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor

from PIL import Image

# Same directory, standard library only. Keeps the "which table is this"
# evidence -- page numbers, section headings, the five-tables-lost incident --
# next to the reasoning instead of buried in a constant here.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mwpvl_layout  # noqa: E402
import mwpvl_strip  # noqa: E402
from mwpvl_strip import UPSCALE, PSM, ocr_strip, strips  # noqa: E402

Image.MAX_IMAGE_PIXELS = None

#: Where the repo is, derived from THIS FILE rather than from the working
#: directory. The script must behave identically whether it is launched from
#: the repo root, from a home directory, or from wherever a grid job happens
#: to land, and it must never chdir -- a script that moves the caller's shell
#: is a script that has to be run in a subshell to be safe.
_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(_HERE))

#: A table image is this wide, give or take the border. See the docstring --
#: this replaced a height filter that lost five tables.
TABLE_WIDTH = (780, 900)

#: Below this a "table" is a rule or a caption fragment, not rows.
MIN_HEIGHT = 300



def extract_images(pdf, out_dir):
    """The distinct table images, each tagged with the table it belongs to.

    Two passes over the same PDF. `pdfimages -list` is read FIRST, before
    anything is written, because it names every image with its PDF object id
    and its first page -- which is what `mwpvl_layout` turns into "this is
    table 08, the small-package delivery stations". The second pass extracts.

    Deduplication is by object id rather than by pixel hash. A long table is
    stored once and referenced from every page it spans, so the object id is
    exact and free, while hashing costs a decode of all 112 copies of the
    fulfilment-centre table to learn what the object id already said.

    Returns [(path, table_dict)] in document order.
    """
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    # `pdfimages -list` first, always. It is fast, it needs no disk, and it is
    # the authority on which image is which table.
    listing = subprocess.run(["pdfimages", "-list", pdf],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             universal_newlines=True)
    tables = mwpvl_layout.parse_image_list(listing.stdout)
    print("  tables found in the document:")
    for line in mwpvl_layout.check(tables):
        print(line)
    print()

    # Reuse an extraction only when the workdir holds EXACTLY the images the
    # listing calls for and nothing else. Extraction is six single-threaded
    # minutes against roughly one minute of parallel OCR, so re-running it on
    # every retry dominates the job -- and this pipeline has needed several
    # retries.
    #
    # The check is strict in both directions on purpose. An earlier version of
    # this script used a different image filter and left EIGHT files here
    # under names the corrected thirteen-image run also wants; reusing that
    # blindly would silently OCR the wrong pictures. Requiring the exact set,
    # by name and non-zero size, makes reuse safe rather than hopeful.
    existing = {n for n in os.listdir(out_dir) if n.endswith(".png")}
    pad_guess = 3
    wanted = {"img-%s.png" % str(t["num"]).zfill(pad_guess) for t in tables}
    reusable = (existing == wanted and all(
        os.path.getsize(os.path.join(out_dir, n)) > 0 for n in wanted))

    if reusable:
        print("  reusing the %d image(s) already in %s (exact match; delete\n"
              "  that directory to force re-extraction)\n"
              % (len(wanted), out_dir))
    else:
        for name in existing:
            os.unlink(os.path.join(out_dir, name))
        if existing:
            print("  cleared %d stale PNG(s) from %s (did not match the "
                  "expected set)" % (len(existing), out_dir))
        print("  extracting images (slow, single-threaded, ~6 min)...")
        subprocess.run(["pdfimages", "-png", pdf,
                        os.path.join(out_dir, "img")],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       check=True)

    # pdfimages names its output by the `num` column of -list, zero-padded to
    # the width of the largest index. Recovering the width from the files
    # themselves avoids assuming 3 digits, which is right for this document
    # and wrong for a longer one.
    names = [n for n in os.listdir(out_dir)
             if n.startswith("img-") and n.endswith(".png")]
    if not names:
        raise SystemExit("  pdfimages wrote nothing to %s" % out_dir)
    pad = len(names[0][len("img-"):-len(".png")])

    out = []
    keep = set()
    for t in tables:
        name = "img-%s.png" % str(t["num"]).zfill(pad)
        path = os.path.join(out_dir, name)
        if not os.path.exists(path):
            print("  MISSING %s for %s" % (name, mwpvl_layout.directory_for(t)))
            continue
        keep.add(name)
        out.append((path, t))

    for name in names:
        if name not in keep:
            os.unlink(os.path.join(out_dir, name))
    print("  %d duplicate/furniture images deleted, %d tables kept\n"
          % (len(names) - len(keep), len(out)))
    return out




def check_settings(out_dir, upscale, psm):
    """Refuse to mix OCR settings inside one output directory.

    Resuming works by filename: a strip whose TSV already exists is skipped.
    That is right when the run is a continuation and WRONG when somebody has
    changed --upscale or --psm in between, because then the skipped files were
    produced at the old settings and the new ones at the new settings, and the
    directory silently becomes a blend of two extractions that no downstream
    consumer can tell apart. The row counts would look fine.

    So the settings are stamped on first use and compared thereafter. Changing
    them is allowed -- it just requires saying so by emptying the directory,
    which is the honest way to start a different extraction.
    """
    stamp_path = os.path.join(out_dir, "SETTINGS.json")
    stamp = {"upscale": upscale, "psm": psm, "strip": mwpvl_strip.STRIP,
             "overlap": mwpvl_strip.OVERLAP}
    if os.path.exists(stamp_path):
        with open(stamp_path) as fh:
            old = json.load(fh)
        if old != stamp:
            raise SystemExit(
                "\n  This output directory was written with DIFFERENT settings:\n"
                "      existing : %s\n      requested: %s\n\n"
                "  Resuming would mix two extractions in one directory and\n"
                "  nothing downstream could tell them apart. Either re-run with\n"
                "  the existing settings, or start clean:\n"
                "      rm -rf %s\n" % (old, stamp, out_dir))
    else:
        with open(stamp_path, "w") as fh:
            json.dump(stamp, fh, indent=2)
    print("  settings : %dx upscale, psm %d, strip %d/%d overlap"
          % (upscale, psm, stamp["strip"], stamp["overlap"]))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pdf", required=True, help="the saved MWPVL page")
    ap.add_argument("--out",
                    default=os.path.join(REPO, "data", "raw", "mwpvl", "tsv"),
                    help="absolute by default, so the output lands in the "
                         "repo no matter where this was launched from")
    # SHARED storage, not /tmp.
    #
    # /tmp on a grid node is node-local and swept. Extraction costs six
    # single-threaded minutes against about one minute of parallel OCR, so
    # paying it again is the dominant cost of any retry -- and putting the
    # images somewhere the next job cannot see guarantees paying it every
    # time, since a grid run has no reason to land on the same node twice.
    # On /weka they persist, the reuse check finds them, and a retry starts
    # OCR'ing immediately.
    #
    # They are derived from a PDF that is itself in the repo, so they are
    # regenerable and safe to delete whenever the space is wanted.
    ap.add_argument("--workdir",
                    default=os.path.join(REPO, "data", "raw", "mwpvl",
                                         "images"))
    ap.add_argument("--workers", type=int, default=14)
    ap.add_argument("--upscale", type=int, default=UPSCALE)
    ap.add_argument("--psm", type=int, default=PSM)
    args = ap.parse_args()

    # PREFLIGHT: prove tesseract works before spending five minutes extracting
    # images and then discovering it does not.
    #
    # Both failures this catches were real and both were expensive. A wrapper
    # that exec'd itself through a symlink returned ELOOP, so every worker
    # wrote "FAIL" and no output, for four minutes, with no error. Then the
    # shared bundle was rebuilt under the running job and the symlink went
    # dangling, which raised FileNotFoundError inside ONE worker and -- because
    # ProcessPoolExecutor re-raises on the consumer -- killed the whole run.
    #
    # `--version` costs a few milliseconds and both failures are visible in it.
    try:
        probe = subprocess.run(["tesseract", "--version"],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               universal_newlines=True, timeout=30)
        banner = (probe.stdout or "").splitlines()[:1]
    except FileNotFoundError:
        raise SystemExit(
            "\n  tesseract is not on PATH.\n"
            "  Run: bash tools/ocr/README.md\n")
    except subprocess.TimeoutExpired:
        raise SystemExit(
            "\n  tesseract hung on --version. That is the signature of a\n"
            "  wrapper script exec'ing itself through a symlink. Rebuild it:\n"
            "      bash tools/ocr/README.md --test\n")
    if probe.returncode != 0 or not banner or "tesseract" not in banner[0]:
        raise SystemExit(
            "\n  tesseract is present but will not run (exit %d):\n      %s\n"
            "  Rebuild: bash tools/ocr/README.md --test\n"
            % (probe.returncode, "\n      ".join(
                (probe.stdout or "(no output)").splitlines()[:4])))
    print("  tesseract: %s  OK" % banner[0].strip())

    # --pdf is required, and there is deliberately no --images escape hatch.
    # The table tagging comes from `pdfimages -list`, which needs the PDF; a
    # bare directory of PNGs cannot say which table is which, and guessing
    # from filenames is how the previous run mislabelled its output.
    images = extract_images(args.pdf, args.workdir)

    if not os.path.isdir(args.out):
        os.makedirs(args.out)

    # One directory per table, numbered in document order, so that an `ls` of
    # the output reads like the article's contents page and a table that
    # failed to OCR is a visibly missing number rather than a silent absence.
    jobs = []
    for path, table in images:
        im = Image.open(path)
        height = im.height
        im.close()
        folder = os.path.join(args.out, mwpvl_layout.directory_for(table))
        if not os.path.isdir(folder):
            os.makedirs(folder)
        stem = os.path.splitext(os.path.basename(path))[0]
        for top, bottom in strips(height):
            dest = os.path.join(folder, "%s__%06d.tsv" % (stem, top))
            jobs.append((path, stem, top, bottom, args.upscale, args.psm,
                         dest))

    check_settings(args.out, args.upscale, args.psm)

    todo = [j for j in jobs if not os.path.exists(j[6])]
    print("  %d strips, %d already done, %d to do"
          % (len(jobs), len(jobs) - len(todo), len(todo)))
    print("  %dx upscale, psm %d, %d workers, OMP_NUM_THREADS=1\n"
          % (args.upscale, args.psm, args.workers))

    done = 0
    failed = 0
    pool = ProcessPoolExecutor(max_workers=args.workers)
    try:
        for msg in pool.map(ocr_strip, todo):
            done += 1
            if msg and msg.startswith("FAIL"):
                failed += 1
            if msg and done % 10 == 0:
                print("  [%d/%d] %s" % (done, len(todo), msg))
                sys.stdout.flush()
    finally:
        pool.shutdown()

    written = sum(1 for j in todo if os.path.exists(j[6]))
    print("\n  %d strip(s) attempted, %d written, %d failed"
          % (len(todo), written, failed))

    # Exit NON-ZERO when the work did not happen.
    #
    # The previous version counted the TSV files present in the output
    # directory and reported success if there were any. A run that attempted
    # 120 strips, failed all 120, and wrote nothing therefore printed
    # "SUCCESS -- 36 TSV files", because 36 files from an earlier run were
    # sitting there. Fourteen minutes of a 64-core node, a green banner, and
    # zero new data. What a run PRODUCED is the only thing it can honestly
    # report on; what happens to be on disk is somebody else's achievement.
    if todo and written == 0:
        print("\n  EVERY strip failed and nothing was written.")
        print("  The usual cause is tesseract running but unable to emit TSV,")
        print("  which happens when the bundle lacks tessdata/configs. Check:")
        print("      bash tools/ocr/README.md --test")
        return 1
    if failed:
        print("\n  WARNING: %d of %d strips failed. The output is INCOMPLETE;"
              % (failed, len(todo)))
        print("  re-running will retry only the missing ones.")
        return 1

    print("  next: python -m siting_atlas.ingest.mwpvl_tables\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
