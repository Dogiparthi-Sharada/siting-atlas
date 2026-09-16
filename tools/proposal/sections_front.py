"""Title page, executive summary, Introduction and Related Work."""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scope import SCOPE

from docx_kit import (BLUE, CRITICAL, GOOD, INK, INK_2, MUTED, ORANGE,
                      bullets, callout, figure, page_break, para, rich, table)


def title_page(doc, meta):
    """Append the title page."""
    para(doc, "", space_after=60)
    para(doc, "SITING ATLAS", size=30, bold=True, color=BLUE, align="c",
         space_after=4)
    para(doc, "Volume I  |  Last-Mile Delivery", size=13, color=ORANGE,
         align="c", space_after=26)
    para(doc, "Agent-Assisted Spatial Causal Inference for Sub-24-Hour "
              "Delivery Territory Expansion under Cannibalization "
              "Constraints", size=15, bold=True, align="c", space_after=10)
    para(doc, "An open, reproducible model of where private infrastructure "
              "gets built — and who bears the consequences.",
         size=11, italic=True, color=INK_2, align="c", space_after=40)
    para(doc, "Applied Research Project Proposal", size=12,
         bold=True, align="c", space_after=26)
    for line in (f"P1: {meta['p1']}", f"P2: {meta['p2']}",
                 f"P3: {meta['p3']}"):
        para(doc, line, size=11.5, align="c", space_after=3)
    para(doc, "", space_after=22)
    for line in ("Master of Science in Business Analytics",
                 "California State University, East Bay",
                 f"Course Instructor: {meta['instructor']}"):
        para(doc, line, size=11, color=INK_2, align="c", space_after=3)
    para(doc, "", space_after=22)
    para(doc, meta["date"], size=10.5, color=MUTED, align="c", space_after=30)
    para(doc, "Not affiliated with, endorsed by, or sponsored by Amazon.com, "
              "Inc., Walmart Inc., Costco Wholesale Corporation, or any other "
              "operator analysed. All operator names are used descriptively "
              "to identify the subject of study.",
         size=8, italic=True, color=MUTED, align="c")
    page_break(doc)



def executive_summary(doc):
    """Append the executive summary."""
    doc.add_heading("Executive Summary", level=1)
    para(doc,
         "Between 2023 and 2026 major retailers restructured national "
         "fulfilment networks into regionalised, node-based architectures "
         "capable of sub-24-hour delivery. Each ZIP-code area enrolled in "
         "same-day service carries a $3–5M capital footprint, and the "
         "profitability of that footprint depends on three interacting "
         "quantities: genuinely incremental demand, spatial route density, "
         "and cannibalization of existing standard-shipping orders. Across "
         f"the {SCOPE.zctas_label} ZIP-code areas in scope, that is {SCOPE.capital} "
         "of capital allocation.", align="j")
    para(doc,
         "Those decisions are made inside proprietary models. The public "
         "bears their consequences — property values, air quality, "
         "municipal budgets, and tax abatements granted to attract "
         "facilities — with no way to check the reasoning. Siting Atlas "
         "is an open, reproducible model of that decision, built entirely "
         "from public data.", align="j")
    para(doc,
         "The system combines a discrete-time hazard model of service "
         "enablement at ZIP-code grain, a spatial synthetic-control estimator "
         "of cannibalization with an empirically estimated decay radius, a "
         "continuous-approximation cost model, and a portfolio optimiser that "
         "treats expansion as a bundle-selection problem rather than a "
         "ranking. A retrieval-augmented agent ingests unstructured "
         "competitor intelligence and re-parameterises the underlying "
         "estimators under six validation gates.", align="j")
    callout(doc, "THE CENTRAL CLAIM",
            "Two of those gates are new. Existing work on gated LLM writes "
            "protects data integrity — do not corrupt rows, do not leak "
            "records. We identify a distinct failure class, inferential "
            "integrity, in which a write satisfying every data-integrity gate "
            "nonetheless invalidates a downstream causal identification "
            "assumption, and we propose two gates that detect it.")
    para(doc,
         "A second contribution is a number nobody has published: how much of "
         "a major operator's revealed siting behaviour is explainable from "
         "public data alone. A high figure is a result about the transparency "
         "of logistics decisions; a low figure is a result about their "
         "opacity, and tells regulators how much disclosure would be needed "
         "to close the gap.", align="j")
    para(doc,
         "The deliverable is a deployed application answering, in dollars and "
         "in probabilities, the question every last-mile operator answers "
         "weekly — which areas should be activated next — and the "
         "question every city council facing an abatement request should ask "
         "but currently cannot: would they have built here anyway?",
         align="j")
    page_break(doc)


def introduction(doc, fig_dir):
    """Append the introduction and problem statement."""
    doc.add_heading("1.  Introduction", level=1)

    doc.add_heading("1.1  The last-mile paradigm shift", level=2)
    para(doc,
         "National fulfilment centres that once shipped to any US address in "
         "2–5 days are being complemented — and in dense metros "
         "replaced — by delivery stations, same-day distribution centres "
         "and oversize nodes positioned within thirty minutes of the average "
         "consumer. Amazon operated 175 US same-day-capable facilities in "
         "2024 and committed to 200+ by the end of 2026 (Amazon 10-K, 2024). "
         "In June 2025 it announced over $4 billion to extend same-day and "
         "next-day service to more than 4,000 smaller cities, towns and rural "
         "communities by the end of 2026. Walmart, Target and Costco have "
         "announced parallel expansions.", align="j")
    para(doc,
         "The consumer-facing consequence is a delivery-speed race. The "
         "operator-facing consequence is a capital-allocation problem of "
         "unprecedented granularity: a wrong answer at ZIP-code level "
         "converts a $4M investment into a permanent operating loss. The "
         "public-facing consequence is that private siting decisions now "
         "reshape neighbourhoods faster than any public process can review "
         "them.", align="j")

    doc.add_heading("1.2  The analytical problem", level=2)
    para(doc, "Adding a ZIP Code Tabulation Area (ZCTA) to a same-day "
              "footprint is not a demand-forecasting problem. It is a joint "
              "estimation problem across three interacting quantities:")
    bullets(doc, [
        [("Incremental demand. ", "b"),
         ("What fraction of post-launch orders are genuinely new spend, and "
          "what fraction shifted tier from existing standard orders?",)],
        [("Route-density economics. ", "b"),
         ("Cost per delivered package falls with drop density (Daganzo, "
          "1984). A ZCTA with weak density can be unprofitable even at high "
          "average order value.",)],
        [("Cannibalization spillovers. ", "b"),
         ("Launching same-day in area A shifts behaviour in contiguous areas "
          "B and C — a violation of the Stable Unit Treatment Value "
          "Assumption that standard estimators cannot handle.",)],
    ])
    callout(doc, "AND A FOURTH, USUALLY MISSED",
            "These decisions are not independent. Two adjacent areas that "
            "are each unprofitable alone can be jointly profitable when they "
            "share a delivery station and pool drop density. Expansion is "
            "therefore a portfolio-selection problem, not a ranking problem "
            "— see §5.6 and Figure 6.", accent=ORANGE)

    doc.add_heading("1.3  Why this matters now, and to whom", level=2)
    para(doc,
         "Three forces make the problem urgent. First, unstructured "
         "competitor intelligence — press releases, permit filings "
         "— can now be integrated into quantitative pipelines at near "
         "zero marginal cost. Second, spatial causal inference has matured to "
         "the point where synthetic-control estimation runs on commodity "
         "hardware. Third, and least discussed, the regulatory environment "
         "has changed.", align="j")
    para(doc,
         "The South Coast Air Quality Management District's Rule 2305 "
         "— the Warehouse Indirect Source Rule, adopted 2021 and "
         "approved by the US EPA — obliges warehouses at or above "
         "100,000 square feet to earn emission-reduction points or pay "
         "mitigation fees, and other regions are considering equivalents. "
         "Air districts operating such rules need to forecast where "
         "warehouses will appear in order to plan mitigation capacity. "
         "Municipalities granting tax abatements to attract facilities need "
         "the counterfactual: would the operator have built here anyway? "
         "Neither has an open model available.", align="j")
    figure(doc, fig_dir, "fig11_stakeholders",
           "Figure 1.  Four user groups, each with a decision the model "
           "changes. The selection propensity in §4.5 is, read in the "
           "opposite direction, the tax-abatement counterfactual.")

    doc.add_heading("1.4  Research questions", level=2)
    bullets(doc, [
        [("RQ1. ", "b"),
         ("Can a discrete-time hazard model trained on publicly available "
          "ZCTA covariates predict which areas an operator enables for "
          "same-day service, and when, at an out-of-time AUC of 0.80 or "
          "better on metros withheld from training?",)],
        [("RQ2. ", "b"),
         ("Does event-driven revision of the spatial weight matrix "
          "materially change the estimated cannibalization coefficient, or "
          "are spatial causal estimates robust to such revision as LeSage "
          "and Pace (2014) argue?",)],
        [("RQ3. ", "b"),
         ("Can validation gates be designed that detect when an "
          "agent-proposed write to an analytical warehouse preserves data "
          "integrity while invalidating a causal identification assumption?",)],
        [("RQ4. ", "b"),
         ("What share of a major operator's revealed siting behaviour is "
          "explainable from public data alone?",)],
    ])
    callout(doc, "NOTE ON RQ2 — A PRE-REGISTERED TEST WITH TWO PUBLISHABLE "
                 "OUTCOMES",
            "If the coefficient moves materially, the result pushes back on a "
            "well-known robustness claim in spatial econometrics. If it does "
            "not, the result confirms that claim under a novel perturbation "
            "and reports an honest engineering finding: the mutable-W "
            "machinery is elegant but not decision-relevant. The prediction "
            "is recorded before the test is run.", accent=GOOD, fill="EAF7EA")
    page_break(doc)
