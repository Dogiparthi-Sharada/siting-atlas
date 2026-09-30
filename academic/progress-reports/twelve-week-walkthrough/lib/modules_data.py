"""Weeks 1-5: getting from fourteen public sources to a panel.

The data half of the twelve. See ``spec.py`` for the conventions these
entries obey and ``modules_models.py`` / ``modules_delivery.py`` for 6-12.
"""

from __future__ import annotations

from modmeta import INSPECT, pct

WEEKS = [
    dict(
        n=1, title="Where every number comes from", mode=INSPECT,
        question="Can a stranger fetch every ingredient of this project "
                 "themselves, and is each one licensed for that?",
        artefacts=["source_probe", "acquire_report"],
        why_inspect=(
            "re-fetching needs three API keys and ~4 GB of downloads"),
        runs="reads the probe and acquisition reports",
        body="""
Fourteen public sources, each fetched into a content-addressed cache with a
SHA-256 per file, so a later run can prove it read the same bytes.

`make probe` checks every endpoint is still alive BEFORE anything is
downloaded. That ordering is the cheap half of reproducibility: a project
that only discovers a dead URL after four gigabytes cannot tell a moved
source from a broken parser.

Six sources cannot be fetched automatically and must be placed by hand. Two
of those are licensed and are deliberately not redistributed.
""",
        nums=lambda L: [
            ("Sources probed", len(L("source_probe")["results"]),
             "source_probe.results"),
            ("Probed on", L("source_probe")["probed_on"],
             "source_probe.probed_on"),
            ("Sources acquired", len(L("acquire_report")["results"]),
             "acquire_report.results"),
        ],
        limits=[
            "Two sources are licensed — a paid CSV and two industry PDFs — "
            "and are excluded from the public repository. The DERIVED "
            "tables built from them ship; the originals do not.",
            "Some sources are single-vintage snapshots that will never "
            "reproduce byte-for-byte if re-fetched later. "
            "`docs/DATA_SOURCES.md` names which ones.",
        ],
        nxt=[("docs/DATA_SOURCES.md",
              "every source, its licence, and how to fetch it")],
    ),
    dict(
        n=2, title="A facility network read out of an image-only PDF",
        mode=INSPECT,
        question="The best public census of this operator's buildings is a "
                 "PDF whose tables are pictures. Can it be recovered, and "
                 "can the result be trusted?",
        artefacts=["mwpvl_extraction", "mwpvl_validation"],
        why_inspect=(
            "the OCR needs tesseract, poppler and the licensed source PDFs, "
            "which are not redistributed"),
        runs="reads the extraction and validation reports",
        body="""
Thirteen tables, no text layer — so `tesseract` plus `poppler`, and then a
validation problem rather than an OCR problem. The question is not "did the
characters come out" but "is a row claiming a 2019 opening actually true".

Three independent checks: internal consistency, date plausibility against
the operator's known network start, and an EXTERNAL falsification bound.
That third one is the load-bearing check — a row linkable to an OSHA
inspection record that predates its claimed opening is impossible, and is
counted as a failure rather than explained away.

Four earlier collection methods failed before this one worked. They are
written down rather than quietly dropped.
""",
        nums=lambda L: [
            ("Facilities recovered",
             f"{L('mwpvl_extraction')['facilities']:,}",
             "mwpvl_extraction.facilities"),
            ("With an opening year",
             f"{L('mwpvl_extraction')['with_year']:,}",
             "mwpvl_extraction.with_year"),
            ("Linked to an OSHA record",
             L("mwpvl_validation")["linked_to_osha"],
             "mwpvl_validation.linked_to_osha"),
            ("Falsified by that link", L("mwpvl_validation")["falsified"],
             "mwpvl_validation.falsified"),
            ("Pass rate", pct(L("mwpvl_validation")["pass_rate"]),
             "mwpvl_validation.pass_rate"),
        ],
        limits=[
            "The pass rate is computed on the rows that could be linked to "
            "OSHA at all, not on all dated rows. It bounds ONE failure "
            "mode; it is not an overall accuracy figure.",
            "The facts are MWPVL International's and are credited as "
            "theirs. The source PDFs are not redistributed.",
        ],
        nxt=[("docs/DATA_SOURCES.md",
              "the four collection methods that failed first")],
    ),
    dict(
        n=3, title="Typed layers and a star schema", mode=INSPECT,
        question="How do fourteen differently-shaped public files become "
                 "one thing a model can query?",
        artefacts=["normalise_report", "warehouse_report"],
        why_inspect=(
            "rebuilding the star schema needs the L0 source cache"),
        runs="reads the normalise and warehouse reports",
        body="""
Two layers, and the split is the point.

**L1** turns each source into one typed parquet and does nothing else — no
joins, no derived columns — so a parsing bug is always attributable to
exactly one file. **L2** is a DuckDB star schema: conformed dimensions for
ZCTA, county and date, with facts hanging off them.

Everything above L2 is ignorant of where the bytes came from. That is why a
second operator, or a second country, would be a data swap rather than a
rewrite.
""",
        nums=lambda L: [(k, f"{v:,}", f"warehouse_report.tables.{k}")
                        for k, v in L("warehouse_report")["tables"].items()],
        limits=[
            "ZCTA geography is the 2020 TIGER vintage only. ZCTAs are "
            "redrawn each decade, so a cross-decade panel would need a "
            "crosswalk this schema does not carry.",
            "Rebuilding L2 needs the L0 cache, so this week inspects the "
            "shipped report rather than re-running the build.",
        ],
        nxt=[("docs/ARCHITECTURE.md", "the six layers and what each owns")],
    ),
    dict(
        n=4, title="The panel every model reads", mode=INSPECT,
        question="What is the unit of analysis, and how much of the country "
                 "does it actually cover?",
        artefacts=["panel_report_expanded", "scope"],
        why_inspect=(
            "rebuilding the panel needs the whole L0-to-L2 chain"),
        runs="reads the panel report and the study-scope artefact",
        body="""
One row per ZIP-code area per quarter. This is the object all three L4
models consume, and it ships with the repository — the single decision that
makes an offline ten-minute reproduction possible instead of a day of
downloads.

`enabled_cells` is worth reading twice. The panel is large, but the subset
where a facility could plausibly open AND every covariate is present is far
smaller, and it is that number the models are actually fitted on. Quoting
the panel row count as the sample size would overstate the evidence by more
than an order of magnitude.
""",
        nums=lambda L: [
            ("Panel rows", f"{L('panel_report_expanded')['rows']:,}",
             "panel_report_expanded.rows"),
            ("Columns", L("panel_report_expanded")["cols"],
             "panel_report_expanded.cols"),
            ("Enabled cells",
             f"{L('panel_report_expanded')['enabled_cells']:,}",
             "panel_report_expanded.enabled_cells"),
            ("ZCTAs nationally", f"{L('scope')['national_zctas']:,}",
             "scope.national_zctas"),
            ("Pilot ZCTAs", f"{L('scope')['pilot']['zctas']:,}",
             "scope.pilot.zctas"),
            ("On disk", f"{L('scope')['panel']['megabytes']} MB",
             "scope.panel.megabytes"),
        ],
        limits=[
            "A ZCTA is a postal-delivery construct, not a polygon. It is "
            "the finest grain most free US data publishes at, which is why "
            "it was chosen, and it is coarser than a parcel or a building.",
            "Fifty columns are carried. Week 8 shows how few survive.",
        ],
        nxt=[("docs/MODEL_SPEC.md", "the panel's schema, column by column")],
    ),
    dict(
        n=5, title="What the public record cannot see", mode=INSPECT,
        question="Before modelling anything — how much of this network is "
                 "visible in free public data at all?",
        artefacts=["mwpvl_coverage"],
        why_inspect=(
            "the intersection needs the OSHA enforcement extract from the "
            "L0 cache"),
        runs="reads the two-list coverage intersection",
        body="""
OSHA enforcement data is the best free source of facility addresses in the
United States. Set its city list against an independent industry census of
delivery-station cities, and intersect.

This is a **two-list intersection, counted** — not a capture-recapture
estimate, and deliberately so. It is a FLOOR on the gap: MWPVL's side is
restricted to small-package delivery stations while OSHA's side is every
facility class, so the comparison is biased towards making the public
record look BETTER than it is. The real gap is at least this wide.

This week is the project's pivot. It is why the prediction question in week
7 was always going to be hard, and it is the finding that survived when the
prediction did not.
""",
        nums=lambda L: [
            ("Cities with a delivery station",
             L("mwpvl_coverage")["mwpvl_delivery_station_cities"],
             "mwpvl_coverage.mwpvl_delivery_station_cities"),
            ("Of those, in OSHA records",
             L("mwpvl_coverage")["cities_in_both"],
             "mwpvl_coverage.cities_in_both"),
            ("Never inspected",
             L("mwpvl_coverage")[
                 "cities_mwpvl_names_that_osha_never_inspected"],
             "mwpvl_coverage.cities_..._never_inspected"),
            ("Share OSHA has seen",
             pct(L("mwpvl_coverage")[
                 "share_of_mwpvl_cities_osha_has_seen"]),
             "mwpvl_coverage.share_of_mwpvl_cities_osha_has_seen"),
        ],
        limits=[
            "Cities, not buildings. This panel cannot say what share of "
            "individual facilities are unrecorded, only what share of the "
            "places holding them are.",
            "Matching is by a normalised city+state key, and 39 MWPVL rows "
            "have no usable city; they are excluded from both sides.",
        ],
        nxt=[("docs/NUMBERS.md",
              "the intersection re-derived, with the matching rule stated")],
    ),
]
