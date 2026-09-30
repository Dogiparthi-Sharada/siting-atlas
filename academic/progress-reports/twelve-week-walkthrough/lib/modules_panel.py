"""Weeks 4-6: build the target variable, build the table, find the finding.

Week 6 is the midterm and the turn of the whole project.
"""

from __future__ import annotations

from modmeta import INSPECT, pct

WEEKS = [
    dict(
        n=4, title="The hard one — a network read out of an image-only PDF",
        mode=INSPECT,
        question="The best public census of this operator's buildings is a "
                 "PDF whose tables are pictures. Can it be recovered, and "
                 "can the result be trusted?",
        artefacts=["mwpvl_extraction", "mwpvl_validation"],
        why_inspect=(
            "the OCR needs tesseract, poppler and the licensed source "
            "PDFs, which are not redistributed"),
        runs="reads the extraction and validation reports",
        status="1,904 facilities recovered. 94.71% survive an external "
               "falsification bound — and the 11 that fail are excluded, "
               "not argued with.",
        risk="If the OCR is unreliable the target variable is unusable and "
             "the project has no dependent variable. Four earlier "
             "collection methods had already failed; this was the week "
             "that decided whether there was a project.",
        body="""
Thirteen tables, no text layer. So `tesseract` and `poppler` — and then the
real problem, which is not OCR at all. Getting the characters out is easy to
check. Knowing whether a row claiming a 2019 opening is *true* is not.

Three independent checks: internal consistency, date plausibility against
the operator's known network start, and an **external falsification bound**.
That third is the load-bearing one. A row linkable to an OSHA inspection
record that predates its claimed opening is not merely doubtful — it is
impossible, because the building was demonstrably operating earlier. Those
rows are counted as failures and dropped.

Four earlier collection methods failed before this one worked. They are
written down rather than quietly omitted, because a reader deciding whether
to repeat this needs to know what does not work.
""",
        nums=lambda L: [
            ("Facilities recovered",
             f"{L('mwpvl_extraction')['facilities']:,}",
             "mwpvl_extraction.facilities"),
            ("With an opening year",
             f"{L('mwpvl_extraction')['with_year']:,}",
             "mwpvl_extraction.with_year"),
            ("Linkable to an OSHA record",
             L("mwpvl_validation")["linked_to_osha"],
             "mwpvl_validation.linked_to_osha"),
            ("Falsified by that link", L("mwpvl_validation")["falsified"],
             "mwpvl_validation.falsified"),
            ("Pass rate", pct(L("mwpvl_validation")["pass_rate"]),
             "mwpvl_validation.pass_rate"),
        ],
        limits=[
            "The pass rate is computed on the rows that could be linked to "
            "OSHA at all, not on every dated row. It bounds one failure "
            "mode; it is not an overall accuracy figure.",
            "The facts are MWPVL International's and are credited as "
            "theirs. The source PDFs are not redistributed.",
        ],
        nxt=[("docs/DATA_SOURCES.md",
              "the four collection methods that failed first")],
    ),
    dict(
        n=5, title="One table every model reads", mode=INSPECT,
        question="How do fourteen differently-shaped files become something "
                 "three different models can all query?",
        artefacts=["warehouse_report", "panel_report_expanded"],
        why_inspect=(
            "rebuilding needs the whole L0 source cache, so this reads the "
            "shipped reports"),
        runs="reads the warehouse and panel reports",
        status="One panel, 1,081,312 rows, 50 columns — and everything "
               "above it is ignorant of where the bytes came from.",
        risk="A silent join error here corrupts every downstream model at "
             "once, and would be invisible in the results. The defence is "
             "the layer split: L1 does no joins, so a parsing bug is "
             "always attributable to exactly one source file.",
        body="""
Two layers, and the split is the point.

**L1** turns each source into one typed parquet and does nothing else — no
joins, no derived columns. **L2** is a DuckDB star schema: conformed
dimensions for ZCTA, county and date, with facts hanging off them. **L3** is
the panel, one row per ZIP-code area per quarter.

The panel ships with the repository. That single decision is what makes an
offline ten-minute reproduction possible instead of a day of downloads, and
it is why a reader can check our numbers rather than deciding not to bother.

Read `enabled_cells` twice. The panel is large, but the subset where a
facility could plausibly open AND every covariate is present is far smaller
— and that is the number the models are fitted on. Quoting the panel row
count as a sample size would overstate the evidence by more than an order
of magnitude, and we say so wherever the figure appears.
""",
        nums=lambda L: (
            [(k, f"{v:,}", f"warehouse_report.tables.{k}")
             for k, v in L("warehouse_report")["tables"].items()]
            + [("Panel rows", f"{L('panel_report_expanded')['rows']:,}",
                "panel_report_expanded.rows"),
               ("Columns", L("panel_report_expanded")["cols"],
                "panel_report_expanded.cols"),
               ("Enabled cells",
                f"{L('panel_report_expanded')['enabled_cells']:,}",
                "panel_report_expanded.enabled_cells")]),
        limits=[
            "ZCTA geography is the 2020 TIGER vintage only. ZCTAs are "
            "redrawn each decade, so a cross-decade panel would need a "
            "crosswalk this schema does not carry.",
            "Fifty columns are carried. Week 10 shows how few survive "
            "contact with a model.",
        ],
        nxt=[("docs/ARCHITECTURE.md", "the six layers and what each owns"),
             ("docs/MODEL_SPEC.md", "the panel schema, column by column")],
    ),
    dict(
        n=6, title="What the public record cannot see",
        mode=INSPECT,
        question="Before modelling anything: how much of this network is "
                 "visible in free public data at all?",
        artefacts=["mwpvl_coverage"],
        why_inspect=(
            "the intersection needs the OSHA enforcement extract from the "
            "L0 cache"),
        runs="reads the two-list coverage intersection",
        midterm=True,
        status="138 of 488 cities. This is the project's actual finding, "
               "and it arrived in the middle of the semester and changed "
               "what the rest of it was for.",
        risk="This is the week we learned the prediction question might be "
             "unanswerable. Raising it at the midterm rather than in week "
             "11 is what made weeks 7-10 a designed response instead of a "
             "scramble.",
        body="""
OSHA enforcement data is the best free source of facility addresses in the
United States. Set its city list against an independent industry census of
delivery-station cities, and intersect them.

This is a **two-list intersection, counted** — not a capture-recapture
estimate, and deliberately so. It is a FLOOR on the gap: MWPVL's side is
restricted to small-package delivery stations while OSHA's side spans every
facility class, so the comparison is biased towards making the public record
look *better* than it is. The real gap is at least this wide.

**Why this is the turn of the project.** We came in intending to predict
where the next facility opens. This week said the public record cannot see
roughly three in four of the places that already have one. That does not
make prediction impossible, but it makes failure the likely outcome — and it
turns "our model lost" from an embarrassment into a measurement of something
real, *provided* we commit to the test in advance. Which is week 7.
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
            "Matching is by a normalised city and state key, and 39 rows "
            "have no usable city; they are excluded from both sides.",
        ],
        nxt=[("docs/NUMBERS.md",
              "the intersection re-derived, with the matching rule stated"),
             ("docs/DECISION_LOG.md",
              "the decision to keep going, and on what basis")],
    ),
]
