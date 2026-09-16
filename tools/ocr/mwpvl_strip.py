"""Slice a tall table image and OCR one slice to word coordinates.

Standalone and Python 3.6, like the rest of `tools/ocr/`. Split out of
`grid_ocr.py` to keep that file under the project's 300-line limit; there is
no other reason these two are apart, and `ocr_strip` must stay at module
level because ProcessPoolExecutor pickles it by import path.
"""

import os
import subprocess
import tempfile

from PIL import Image

Image.MAX_IMAGE_PIXELS = None

#: Pixels per strip before upscaling, and the overlap between consecutive
#: strips. A printed row is about 60 px and a row whose address wraps runs to
#: 250, so 400 guarantees no row is cut in half by BOTH of the strips that
#: contain it -- without the overlap, a facility landing on a boundary is lost
#: twice over and leaves no trace that it was ever there.
STRIP = 1400
OVERLAP = 400

#: Measured on a 1,400-px sample: 1x -> 23 ZIPs, 2x -> 26, 3x -> 26, 4x -> 26;
#: psm 4 -> 15 dates, psm 6 -> 17, psm 11 -> 5, psm 12 -> 6. 2x is where the
#: gain saturates. 4x is used anyway because on a 16-core node the extra
#: pixels cost wall-clock nobody is waiting on, and a recovered digit is a
#: facility that does not have to be thrown away.
UPSCALE = 4
PSM = 6


def strips(height):
    """Overlapping (top, bottom) spans covering an image of this height."""
    spans = []
    top = 0
    while top < height:
        bottom = min(top + STRIP, height)
        spans.append((top, bottom))
        if bottom >= height:
            break
        top = bottom - OVERLAP
    return spans


def ocr_strip(job):
    """OCR one strip to a TSV whose boxes are in ORIGINAL image coordinates.

    `job` is (src_png, stem, top, bottom, upscale, psm, dest_tsv), a plain
    tuple because it crosses a process boundary.

    tesseract reports every box in the frame of the upscaled crop it was
    handed. Dividing by the upscale factor and adding the crop's top offset
    puts each word back where it sits on the full page. That is what makes the
    overlapping strips stitchable: two strips that both saw a row report its
    words at the SAME coordinates, so duplicates can be removed by position.
    Deduplicating by string instead would delete real repeats -- two
    facilities in one city share most of their address words.

    Returns a short status string, or None if the strip was already done.
    """
    src, stem, top, bottom, upscale, psm, dest = job
    if os.path.exists(dest):
        return None

    # Be a guest on the machine. The grid node is shared and this fans out to
    # one process per core; niceness costs nothing when the node is idle and
    # keeps it answering ssh when it is not.
    try:
        os.nice(5)
    except (AttributeError, OSError):
        pass

    im = Image.open(src)
    crop = im.crop((0, top, im.width, bottom)).convert("L")
    im.close()
    crop = crop.resize((crop.width * upscale, crop.height * upscale),
                       Image.LANCZOS)

    tmp = tempfile.mkdtemp()
    try:
        png = os.path.join(tmp, "s.png")
        base = os.path.join(tmp, "o")
        crop.save(png)
        # OMP_NUM_THREADS=1 because tesseract links OpenMP and fans out to
        # ~265% CPU inside a single process -- measured. With 14 workers that
        # oversubscribes a 16-core node threefold and everything slows down
        # together, which looks like the job being slow rather than the job
        # fighting itself.
        env = dict(os.environ)
        env["OMP_NUM_THREADS"] = "1"
        subprocess.run(["tesseract", png, base, "--psm", str(psm), "tsv"],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       env=env)
        tsv = base + ".tsv"
        if not os.path.exists(tsv):
            return "FAIL %s" % os.path.basename(dest)
        with open(tsv, "r", errors="replace") as fh:
            rows = fh.read().splitlines()
    finally:
        for name in os.listdir(tmp):
            os.unlink(os.path.join(tmp, name))
        os.rmdir(tmp)

    kept = []
    if rows:
        kept.append(rows[0] + "\tstem\timg_top")
    for line in rows[1:]:
        f = line.split("\t")
        # level 5 is a word. Levels 1-4 are page/block/paragraph/line
        # containers that carry a bounding box and no text; keeping them puts
        # empty rows into the parse and inflates every word count.
        if len(f) < 12 or f[0] != "5" or not f[11].strip():
            continue
        f[6] = str(int(f[6]) // upscale)
        f[7] = str(int(f[7]) // upscale + top)
        f[8] = str(int(f[8]) // upscale)
        f[9] = str(int(f[9]) // upscale)
        kept.append("\t".join(f) + "\t%s\t%d" % (stem, top))

    with open(dest, "w") as fh:
        fh.write("\n".join(kept))
    return "%s  %d words" % (os.path.basename(dest), len(kept) - 1)
