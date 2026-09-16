"""Which table is which, derived from the document rather than guessed.

Standalone and Python 3.6, like its caller. Imports nothing but the standard
library.

HOW THE MAPPING WAS ESTABLISHED
-------------------------------
The PDF has no table captions inside the images -- a table is a bare grid of
pixels with no title -- so an image on its own cannot say what it holds. Two
independent facts pin it down:

  1. `pdftotext` gives the section HEADINGS and the page each one sits on,
     because the prose is a real text layer. "The Amazon 'Last Mile' Delivery
     Station Network for Small Packages in the United States" is on page 38.

  2. `pdfimages -list` gives the first page each IMAGE appears on. The image
     of object 137 first appears on page 39.

A table on page 39 belongs to the heading on page 38. That is deterministic,
it is checkable by anyone re-running the two commands, and it does not depend
on reading the table's contents. The assignment was then verified by OCR'ing
the first 700 rows of each image and confirming the facility codes matched the
section -- DBM3/DBM4 delivery stations under the delivery station heading,
YYC1/YHM2 Canadian sites under rest-of-world, HBM3/HPX1 under heavy/bulky.

WHY THE BOUNDARIES ARE TABLE PAGES AND NOT HEADING PAGES
--------------------------------------------------------
Page 24 carries TWO headings: Whole Foods, then Fresh Hub. Boundaries keyed on
heading pages cannot separate them. Boundaries keyed on the page each table
actually begins can, and those pages are known exactly from `pdfimages -list`.
So the numbers below are first-table-pages. They are data, not estimates.

A SILENT FAILURE THIS PREVENTS
------------------------------
An earlier run filtered images by height > 5000 px and lost five tables --
Amazon Fresh DC (1,576 px), Whole Foods (665), Fresh Hub (3,744), Inbound
Cross Dock (3,975) and Air Gateway (1,753): 11,713 pixel-rows, about 8% of the
document's table content. Nothing failed. The run completed, wrote output, and
reported success. `expected_tables()` below exists so that a run which finds
the wrong number of tables says so.
"""

import re

#: (first page of the table, slug). Document order. See the docstring for
#: where the page numbers come from -- they are measured, not assumed.
SECTIONS = (
    (4,   "us_fulfillment_center"),
    (23,  "us_fresh_dc"),
    (24,  "us_whole_foods_dc"),
    (25,  "us_fresh_hub"),
    (28,  "us_inbound_cross_dock"),
    (31,  "us_sortation_center"),
    (37,  "us_air_gateway_hub"),
    (39,  "us_delivery_station"),
    (67,  "us_delivery_heavy_bulky"),
    (74,  "row_fulfillment_center"),
    (89,  "row_sortation_delivery_air"),
)

#: How many distinct table images the 2025 Q1 document holds. Two sections run
#: to a second image -- delivery stations (objects 137 and 184) and
#: rest-of-world (243 and 290) -- so this exceeds len(SECTIONS) by two.
EXPECTED_TABLES = 13

#: A table is rendered this wide; page furniture is not. Filtering on WIDTH
#: rather than height is what stops the five short tables being dropped.
TABLE_WIDTH = (780, 900)
MIN_HEIGHT = 300


def section_for_page(page):
    """The slug and 1-based index of the section a table on `page` belongs to."""
    chosen, index = SECTIONS[0][1], 1
    for i, (start, slug) in enumerate(SECTIONS, 1):
        if page >= start:
            chosen, index = slug, i
        else:
            break
    return chosen, index


def parse_image_list(text):
    """Distinct table images from `pdfimages -list` output.

    Returns a list of dicts with `num` (the sequence number pdfimages uses in
    its output FILENAMES), `obj`, `page`, `width`, `height`, `slug`, `order`
    and `part`.

    Deduplication is by PDF object id, not by pixel hash. A long table is
    embedded once and referenced from every page it spans -- the delivery
    station table is one object referenced from twenty-three pages -- so the
    object id identifies it exactly, and the first page it appears on is the
    page the table starts. Hashing the extracted PNGs gives the same answer
    but costs a decode of every copy.
    """
    rows = []
    for line in text.splitlines():
        f = line.split()
        # page num type width height color comp bpc enc interp object ID ...
        if len(f) < 12 or not re.match(r"^\d+$", f[0]) or f[2] != "image":
            continue
        width, height = int(f[3]), int(f[4])
        if not (TABLE_WIDTH[0] <= width <= TABLE_WIDTH[1]
                and height >= MIN_HEIGHT):
            continue
        rows.append({"page": int(f[0]), "num": int(f[1]), "width": width,
                     "height": height, "obj": f[10]})

    first = {}
    for r in rows:
        if r["obj"] not in first:
            first[r["obj"]] = r
    tables = sorted(first.values(), key=lambda r: r["page"])

    counts = {}
    for t in tables:
        slug, order = section_for_page(t["page"])
        counts[slug] = counts.get(slug, 0) + 1
        t["slug"], t["order"], t["part"] = slug, order, counts[slug]
    return tables


def directory_for(table):
    """`08_us_delivery_station` or `08_us_delivery_station_part2`.

    Numbered so that an `ls` of the output shows the tables in the order they
    appear in the article, which is the order somebody reading the source
    would expect and makes a missing one obvious at a glance.
    """
    name = "%02d_%s" % (table["order"], table["slug"])
    if table["part"] > 1:
        name += "_part%d" % table["part"]
    return name


def check(tables):
    """Lines describing what was found, and whether it is all of it."""
    out = []
    total = 0
    for t in tables:
        total += t["height"]
        out.append("      %-34s obj %-5s p%-4d %4d x %9s"
                   % (directory_for(t), t["obj"], t["page"], t["width"],
                      format(t["height"], ",")))
    out.append("      %s pixel-rows across %d tables"
               % (format(total, ","), len(tables)))
    if len(tables) != EXPECTED_TABLES:
        out.append("")
        out.append("  WARNING: expected %d tables, found %d. The 2025 Q1 "
                   "article has %d;" % (EXPECTED_TABLES, len(tables),
                                        EXPECTED_TABLES))
        out.append("  a different count means either a different vintage of "
                   "the page or a")
        out.append("  filter that is dropping real tables. Do not treat the "
                   "output as complete.")
    return out
