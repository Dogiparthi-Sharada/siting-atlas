"""Section 2: Related Work, with the delta stated against each stream."""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scope import SCOPE

from docx_kit import (BLUE, CRITICAL, GOOD, INK, INK_2, MUTED, ORANGE,
                      bullets, callout, figure, page_break, para, rich, table)


def _delta(doc, text):
    """Format one "what they did / what we add" contrast row."""
    rich(doc, [("Our delta.  ", "b", ORANGE), (text,)], align="j")


def related_work(doc, fig_dir):
    """Append the related-work section to the document."""
    doc.add_heading("2.  Related Work", level=1)
    para(doc,
         "This project intersects six research streams. For each we state the "
         "anchor literature and, explicitly, the delta between our work and "
         "the existing corpus. Two prior-art reviews inform this section: one "
         "over the published literature, and one over shipped commercial "
         "products. Both are reported, because a contribution that has not "
         "been checked against either is not a contribution.", align="j")

    figure(doc, fig_dir, "fig10_positioning",
           "Figure 2.  Novelty positioning after the literature and "
           "commercial prior-art checks. Left: what is already published and "
           "must be cited, not claimed. Right: what remains open.")

    doc.add_heading("2.1  Spatial causal inference and interference", level=2)
    para(doc,
         "The Synthetic Control Method was introduced by Abadie and "
         "Gardeazabal (2003) and formalised by Abadie, Diamond and "
         "Hainmueller (2010). It constructs a counterfactual for a treated "
         "unit as a convex combination of controls matched on pre-treatment "
         "outcomes. Its principal weakness in a logistics setting is the "
         "no-interference assumption: launching in area A materially affects "
         "adjacent areas B and C.", align="j")
    para(doc,
         "That weakness is not unaddressed. Anselin (1988) and LeSage and "
         "Pace (2009) formalised spatial estimators that relax it via a "
         "weight matrix W. More recently, Pollmann (arXiv:2011.00373) gives a "
         "general treatment of causal inference for treatments applied at a "
         "location with effects decaying over distance, including "
         "distance-band estimation; and a body of work extends synthetic "
         "control directly to the spillover case (arXiv:2408.00291; "
         "arXiv:2411.01249; Reich et al., International Statistical Review).",
         align="j")
    _delta(doc, "We adopt Pollmann's distance-band estimator rather than "
           "proposing one. What we contribute is the parameter: the decay "
           "curve of same-day cannibalization has not, to our knowledge, been "
           "estimated or published, and we use the estimate to construct W "
           "instead of assuming binary contiguity.")

    doc.add_heading("2.2  Estimating the spatial weight matrix", level=2)
    para(doc,
         "It is sometimes assumed that spatial econometrics treats W as fixed "
         "ex ante. It does not. Souza (2019), Krisztin and Piribauer "
         "(arXiv:2101.11938) and Political Analysis (2024) all estimate or "
         "select W from data, and LeSage and Pace (2014) argue prominently "
         "that results are less sensitive to the choice of W than "
         "practitioners assume. We therefore make no claim to novelty in "
         "relaxing the fixed-W assumption.", align="j")
    _delta(doc, "Every estimator above recovers W from the same outcome panel used "
           "for inference — an in-sample statistical problem, solved "
           "once. We treat W instead as event-driven state, revised between "
           "estimation cycles from an exogenous text stream under validation "
           "gates. We make no claim to improve on those estimators, and we "
           "test empirically (RQ2) whether the revision changes anything at "
           "all.")

    doc.add_heading("2.3  Routing and density economics", level=2)
    para(doc,
         "The continuous-approximation approach to vehicle routing originates "
         "with Beardwood, Halton and Hammersley (1959). Daganzo (1984) "
         "derived that per-stop distance in a uniform-density zone scales as "
         "the inverse square root of delivery density; Ansari et al. (2018) "
         "survey subsequent work. Luxen and Vetter (2011) introduced the Open "
         "Source Routing Machine, enabling exact drive-time computation on "
         "OpenStreetMap graphs.", align="j")
    _delta(doc, "We retain Daganzo's density law and instantiate the distance term "
           "from a precomputed drive-time matrix. The engineering "
           "contribution is negative and deliberate: the deployed system "
           "carries no routing dependency at all (§5.9).")

    doc.add_heading("2.4  Retail expansion and cannibalization", level=2)
    para(doc,
         "This stream is the closest published analogue to our research "
         "question. Management Science has published "
         "structural analyses of exactly this problem — retail expansion "
         "and cannibalization in a dynamic environment (58(11), 2012) and "
         "demand expansion versus cannibalization from store entry (68(12), "
         "2022) — alongside dynamic entry models of chain expansion "
         "(Caoui, Hollenbeck and Osborne).", align="j")
    _delta(doc, "Those studies use structural models on proprietary firm data at "
           "store grain, in a static information environment, and produce no "
           "runnable artifact. We use reduced-form spatial causal inference "
           "on public data at ZCTA grain, for a service-tier rather than a "
           "store-opening decision, and ship the tool.")

    doc.add_heading("2.5  LLM agents that write to analytical systems",
                    level=2)
    para(doc,
         "Retrieval-augmented generation (Lewis et al., 2020) and the ReAct "
         "pattern (Yao et al., 2023) established the interleaving of "
         "reasoning and tool use; the Model Context Protocol (Anthropic, "
         "2024) formalised a portable tool interface. Applications in "
         "analytics have converged on text-to-SQL agents that are almost "
         "universally read-only.", align="j")
    para(doc,
         "Gated writes, however, are not unexplored. A survey of "
         "specification, verification and enforcement for safe LLM agents "
         "(arXiv:2608.14590), privacy-preserving alignment for natural "
         "language database interfaces (arXiv:2511.06778), text-to-SQL "
         "vulnerability analysis (arXiv:2211.15363) and shipped open-source "
         "write gates all address the pattern. We claim no novelty in gating "
         "an agent write.", align="j")
    _delta(doc, "All of that work protects data integrity: do not corrupt rows, do "
           "not leak records, do not drop tables. Our write target is not a "
           "data table but a parameter of a causal estimator, which creates a "
           "failure class the existing gates do not cover — a write that "
           "is schema-valid, correctly geocoded, high-confidence and fully "
           "logged, and that nonetheless invalidates a downstream "
           "identification assumption. We name this inferential integrity and "
           "propose two gates that detect it (§5.7).")

    doc.add_heading("2.6  Industry practice and the reproduction gap",
                    level=2)
    para(doc,
         "The definitive academic treatment of a large operator's fulfilment "
         "network is Houde, Newberry and Seim, 'Nexus Tax Laws and Economies "
         "of Density in E-Commerce: A Study of Amazon's Fulfillment Center "
         "Network' (Econometrica, 2023), which estimates a structural model "
         "of the firm's own entry decision using state sales-tax nexus "
         "variation. Schorung, Lecourt and Dablanc (2023) map the warehouse "
         "network geographically; the Journal of Policy Analysis and "
         "Management (2025) evaluates local economic impacts.", align="j")
    table(doc,
          ["Dimension", "Houde, Newberry & Seim (2023)", "Siting Atlas"],
          [["Network tier", "2-day fulfilment centres",
            "Sub-24-hour nodes (DS / SDC / oversize)"],
           ["Spatial grain", "State", f"ZCTA ({SCOPE.zctas_label} modelled, {SCOPE.national_zctas_label} US)"],
           ["Period", "Through ~2018, pre-regionalisation", "2015–2026"],
           ["Data", "Proprietary and licensed", "Entirely public"],
           ["Identification", "Sales-tax nexus variation",
            "Selection correction + spatial synthetic control"],
           ["Environment", "Static information", "Event-driven state updates"],
           ["Artifact", "None runnable by a third party",
            "Deployed, open, reproducible"]],
          widths=[1.15, 2.5, 2.45])

    para(doc,
         "Commercial practice must be acknowledged with the same care as the "
         "literature. A capable market already sells siting analytics; the "
         "question for a research contribution is not whether the tools exist "
         "but what none of them does.", align="j")
    figure(doc, fig_dir, "fig14_market",
           "Figure 3.  The market for siting analytics, and the gap that "
           "remains. Every technique here has a paywalled equivalent; what "
           "does not exist is a version anybody can check.")
    callout(doc, "COMMERCIAL PRIOR ART — A DIFFERENT KIND OF PRIOR ART",
            "Esri ArcGIS Business Analyst ships a tool named Measure "
            "Cannibalization. Supply-chain network design software (Coupa, "
            "AIMMS, anyLogistix, Optilogic) has solved multi-facility "
            "location optimisation for two decades. Neither makes a claim in "
            "this proposal false; both make the words 'first' and 'novel' "
            "naive, and we avoid them throughout. The surviving distinction "
            "is methodological: commercial cannibalization tooling measures "
            "trade-area overlap, which is descriptive geometry, and answers "
            "'how much do these areas share?'. It does not answer 'what would "
            "volume in B have been had A never opened?' — there is no "
            "counterfactual, no donor pool and no standard error. Our "
            "estimate is causal.")
    para(doc,
         "What remains genuinely absent is a public one. No open, auditable, "
         "forward-looking model of a competitor's siting behaviour was found; "
         "the commercial-real-estate trade press tracks expansion after the "
         "fact. Throughout this proposal we therefore claim only that a "
         "result is not published in the open literature, or not available as "
         "a public reproducible artifact — statements that remain true "
         "regardless of what any vendor ships or any operator runs "
         "internally, because those systems are proprietary and cannot be "
         "checked.", align="j")
    page_break(doc)
