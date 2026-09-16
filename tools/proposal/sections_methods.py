"""Section 5: Proposed Methods."""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scope import SCOPE
from hazard_metrics import HAZARD

from docx_kit import (BLUE, CRITICAL, GOOD, INK, INK_2, MUTED, ORANGE,
                      bullets, callout, figure, page_break, para, rich, table)


def methods(doc, fig_dir):
    """Append the methods section: hazard model, SCM, cost, optimiser."""
    doc.add_heading("5.  Proposed Methods", level=1)

    doc.add_heading("5.1  System architecture", level=2)
    para(doc,
         "The system decomposes into a public-source ingest layer, a "
         "dimensional warehouse, four coupled analytical models, a decision "
         "layer, and two delivery surfaces — one for operators and one "
         "for public planning.", align="j")
    figure(doc, fig_dir, "fig01_architecture",
           "Figure 7.  End-to-end architecture, from public sources through "
           "the warehouse and analytical models to the two delivery "
           "surfaces.")

    doc.add_heading("5.2  Dimensional warehouse", level=2)
    para(doc,
         "The DuckDB warehouse is a Kimball-style star schema. DuckDB is "
         "chosen because columnar vectorised execution suits the analytical "
         "queries the application issues, its spatial extension provides "
         "PostGIS-compatible functions natively, and the entire warehouse is "
         "a single portable file — which is what makes peer-review "
         "reproduction feasible.", align="j")
    figure(doc, fig_dir, "fig02_star_schema",
           "Figure 8.  Star schema. The scenario dimension is what makes "
           "auditability real rather than nominal.")
    para(doc,
         "The scenario dimension deserves comment. Every agent-proposed "
         "mutation of the spatial weight matrix creates a scenario row "
         "recording which matrix version, which mutation and which random "
         "seed produced a given result. Any published number can therefore be "
         "replayed exactly. Without this, a system whose parameters change in "
         "response to text is not auditable in any meaningful sense.",
         align="j")

    doc.add_heading("5.3  Siting and timing model", level=2)
    para(doc,
         "For ZCTA i in quarter t, let the hazard of first enablement be "
         "modelled as a complementary log-log discrete-time hazard over "
         "covariates x, with metro random effects and a flexible baseline in "
         "time since the nearest node opened. Estimation is by penalised "
         "maximum likelihood with the seed recorded in the reproducibility "
         "manifest.", align="j")
    para(doc,
         "Three secondary models are retained. The zero-inflated negative "
         "binomial volume model, framed per §4.2 as specification recovery. A Huff "
         "gravity pull factor (Huff, 1964) with the distance-decay exponent "
         "fixed at 2.0 per the retail-geography literature, so it cannot be "
         "tuned to the data. And a LightGBM benchmark (Ke et al., 2017) with "
         "SHAP attribution (Lundberg and Lee, 2017), whose purpose is "
         "convergent validity: if a parametric hazard model and a "
         "non-parametric tree ensemble rank the same areas highly, the "
         "ranking is unlikely to be an artefact of functional form.",
         align="j")
    para(doc,
         "Two features of the input data are carried explicitly rather than "
         "discarded. Census margins of error, published for every estimate "
         "and routinely ignored, enter the uncertainty model as an input, so "
         "that two areas whose reported incomes differ by less than their "
         "margins are not treated as reliably ordered. And the monthly "
         "sources of §4.2 contribute rate-of-change features alongside the "
         "lagged levels, allowing the model to observe trajectory.", align="j")
    para(doc,
         "Uncertainty is quantified by split conformal prediction "
         "(Angelopoulos and Bates, 2021), which provides distribution-free, "
         "finite-sample coverage. This matters because it converts a claim "
         "about intervals into a verified measurement: we report the "
         "proportion of held-out ZCTAs actually covered by the nominal 90% "
         "interval, rather than assuming the model's own variance estimates "
         "are correct.", align="j")

    doc.add_heading("5.4  Cannibalization and the spatial weight matrix",
                    level=2)
    para(doc,
         "Following Abadie et al. (2010), the counterfactual for a treated "
         "ZCTA is a convex combination of donor-pool areas with weights "
         "chosen to minimise pre-treatment fit error. Inference is by in-space "
         "and in-time placebo permutation, reporting the post/pre RMSPE ratio "
         "and its rank among placebos.", align="j")
    para(doc,
         "Rather than assuming a spillover structure, we estimate it. Using "
         "Pollmann's distance-band approach, the treatment effect is "
         "estimated separately within concentric rings around each activated "
         "ZCTA, producing a decay curve with confidence bands.", align="j")
    figure(doc, fig_dir, "fig05_decay",
           "Figure 9.  Estimated cannibalization decay, and the weight matrix "
           "it implies. Values are illustrative pending estimation.")
    para(doc,
         "The estimated decay then defines W. This closes a gap that binary "
         "contiguity leaves open: the obvious question — why "
         "contiguity? — has no answer. W is "
         "now an estimated object with a standard error, and the "
         "cannibalization radius for same-day delivery is, to our knowledge, "
         "a parameter not previously published.", align="j")
    para(doc,
         "The estimated radius also solves a practical problem. Synthetic "
         "control requires untreated donors, and in a saturating network "
         "those are scarce — more so if every neighbour of a treated unit "
         "is excluded as contaminated. Because contamination is now measured "
         "rather than assumed, only units inside the estimated radius are "
         "excluded, which recovers donors a contiguity rule would discard. "
         "Two further devices widen the pool: staggered adoption, in which "
         "later-treated units serve as controls for earlier-treated ones "
         "before their own treatment, and cross-metro donors, since matching "
         "is on pre-treatment trajectory rather than geography. Donor-pool "
         "size and weight concentration are reported as diagnostics, and "
         "where no credible pool exists the estimate is reported as not "
         "estimable rather than produced.", align="j")
    para(doc,
         "W is also revised at run time by the agent when a competitor "
         "facility event is parsed from text. Whether that revision changes "
         "the estimated coefficient materially is RQ2, and is tested rather "
         "than assumed.", align="j")

    doc.add_heading("5.5  Cost model", level=2)
    para(doc,
         "Cost per delivered package decomposes into a stem cost from the "
         "nearest node to the zone and a local cost within the zone, the "
         "latter scaling as the inverse square root of delivery density per "
         "Daganzo (1984). Stem distance is currently the great-circle "
         "distance scaled by the circuity factor of §5.9; the precomputed "
         "drive-time matrix is designed but not built. Capital is decomposed "
         "into eight buckets, each with a "
         "documented public proxy and each varying by metro: real-estate "
         "lease, building fitout, delivery vehicles, one-time hiring, ongoing "
         "wages, fuel and energy, permitting, and marketing activation.",
         align="j")
    figure(doc, fig_dir, "fig07_tornado",
           "Figure 10.  Capital-bucket sensitivity. Four primary buckets "
           "account for roughly three-quarters of the swing in net present "
           "value.")
    para(doc,
         "The sensitivity analysis is the defence of the cost model. Not all "
         "eight buckets need to be estimated precisely; the two that dominate "
         "the swing do, and the analysis identifies which those are rather "
         "than asserting it.", align="j")

    doc.add_heading("5.6  Net present value and portfolio selection", level=2)
    para(doc,
         "Five-year net present value per ZCTA nets margin on incremental "
         "volume against delivery cost, discounted, less metro-specific "
         "capital. Uncertainty is propagated by Monte Carlo over 10,000 draws "
         "per ZCTA, drawing jointly from the hazard-model posterior, the "
         "synthetic-control weight uncertainty, routing variance and each "
         "capital bucket's proxy uncertainty. A bootstrap wrapper places a "
         f"confidence interval on the median itself — roughly {SCOPE.draws} "
         "simulated realisations in total, which requires vectorised, chunked "
         "evaluation.", align="j")
    callout(doc, "REPORTING NPV WITHOUT AN OBSERVABLE MARGIN",
            "Contribution margin per incremental order is not observable in "
            "public data. Rather than invent it, we factor it out: results "
            "are reported as a multiple of margin together with the "
            "break-even value — for example, 41,000m minus $3.8M, "
            "break-even at m = $0.93. A reader with a view on margin "
            "substitutes it; a reader without one still gets the threshold. "
            "Plausible ranges for m are additionally bounded from disclosed "
            "aggregates so a band can be reported. Because ranking is "
            "invariant to a common scale factor, the ordering of areas, the "
            "choice between bundles and the rank-stability results are all "
            "unaffected by the unknown. We also re-run the ranking under a "
            "margin that varies with income, as a worst case, and report how "
            "far the top-100 list moves.", accent=CRITICAL, fill="FBEAEA")
    callout(doc, "RANK STABILITY, NOT JUST SPREAD",
            "The executive question is not 'what is the error rate' but 'if "
            "the inputs move within their uncertainty bands, does the "
            "recommendation change?'. We will therefore report, for each "
            "candidate area, the share of Monte Carlo draws in which it holds "
            "a top-K position: an area that holds a top-ten place in most "
            "draws is actionable, one that holds it in a minority of draws is "
            "not, and saying so is more useful than a point estimate. "
            "This pass has NOT been run. No rank-stability figure is quoted "
            "anywhere in this document, and earlier drafts carried an "
            "illustration of one that has been withdrawn.")
    para(doc,
         "What has been measured is the interval procedure that sits under "
         "it. Split conformal prediction was run on the hazard model, and "
         "Figure 11 reports the result: coverage against what was asked for, "
         "and the composition of the prediction sets. It is included because "
         "it is the one guarantee that does not require the model to be "
         "correct, and because its cost is visible — at a two per cent base "
         "rate a tenth of the sets contain neither label, which is an honest "
         "refusal to answer and useless for ranking.", align="j")
    figure(doc, fig_dir, "fig09_conformal_coverage",
           "Figure 11.  Split conformal prediction on the hazard model: "
           "measured coverage against nominal, and what the prediction sets "
           f"contain. Source: outputs/metrics/hazard_report.json, run "
           f"{HAZARD.run_id}.")
    para(doc,
         "Ranking areas independently, however, assumes their net present "
         "values add — and they do not. Cannibalization makes adjacent "
         "activations worth less together; shared stations and pooled drop "
         "density make them worth more. Two areas each unprofitable alone can "
         "be jointly profitable.", align="j")
    figure(doc, fig_dir, "fig06_portfolio",
           "Figure 12.  Why a ranking misses profitable bundles, and why "
           "greedy selection carries no approximation guarantee here.")
    para(doc,
         "We therefore solve a bundle-selection problem by greedy "
         "construction with pairwise-swap local search over the top candidate "
         "set, and report the gap against pure greedy ranking. Because "
         "cannibalization produces diminishing returns while density "
         "economics produces increasing returns, the objective is neither "
         "submodular nor supermodular and the standard greedy bound does not "
         "apply, making the size of the gap an empirical question.", align="j")
    para(doc,
         "We do not claim multi-facility optimisation as a contribution "
         "— it is a mature commercial category (§2.6). It is included "
         "because ranking is the wrong model of the decision, and correcting "
         "that is a matter of validity rather than novelty.", align="j")

    doc.add_heading("5.7  Agent layer and the six gates", level=2)
    para(doc,
         "The agent implements the ReAct pattern with three tools exposed as "
         "Model Context Protocol servers: a query generator and a spatial "
         "visualiser, both read-only, and a warehouse mutator that parses "
         "competitor infrastructure text, extracts a facility record and "
         "writes it — triggering downstream re-estimation.", align="j")
    figure(doc, fig_dir, "fig03_agent_gates",
           "Figure 13.  The agent loop and the six-gate mutation path. Gates "
           "5 and 6 are the contribution.")
    para(doc,
         "Gates 1 through 4 — schema conformance, geocoding "
         "reachability, a confidence threshold and audit-log immutability "
         "— protect data integrity and have prior art (§2.5). They are "
         "not sufficient. Consider a press release announcing a competitor "
         "sortation centre in Plano, Texas. The extracted record is "
         "schema-valid, the coordinates resolve, confidence is high and the "
         "write is logged: all four gates pass. Yet the write changes W, "
         "which changes which areas are neighbours, which changes the donor "
         "pool for treated areas in that metro, which changes the "
         "cannibalization coefficient and moves net present value by "
         "millions. The data is correct and the inference is broken.",
         align="j")
    bullets(doc, [
        [("Gate 5 — donor-pool integrity. ", "b", ORANGE),
         ("Does this mutation move a unit currently serving as a control into "
          "a treated or spillover-contaminated state? If so, the donor pool "
          "is recomputed and the affected areas flagged, never silently "
          "re-weighted.",)],
        [("Gate 6 — estimate stability. ", "b", ORANGE),
         ("The cannibalization coefficient is re-estimated with and without "
          "the mutation. If the change exceeds a pre-registered threshold, "
          "the mutation escalates to human review regardless of automation "
          "settings, and the delta is surfaced in the diff card.",)],
    ])
    para(doc,
         "For any public demonstration, human-in-the-loop confirmation is "
         "enabled by default: every mutation that clears all six gates still "
         "requires an explicit human approval before the write lands.",
         align="j")

    doc.add_heading("5.8  Contributions", level=2)
    para(doc,
         "Four claims, each stated so that a product datasheet or an "
         "internal proprietary system cannot falsify it.", align="j")
    table(doc,
          ["#", "Claim", "Stated as"],
          [["1", "Inferential-integrity gates",
            "A failure class not covered by the published gated-write "
            "literature, with two gates that detect it."],
           ["2", "Causal cannibalization radius, and W built from it",
            "The estimator is Pollmann's; the parameter for same-day "
            "delivery is not published in the open literature."],
           ["3", "Public-data explainability ceiling and cross-operator "
                 "transfer",
            "How much siting behaviour is visible from outside, and whether "
            "a model fitted on one operator predicts another. Not previously "
            "reported."],
           ["4", "The artifact",
            "Free, open, reproducible, public-data, and serving regulators "
            "and communities. Every technique here has a paywalled "
            "commercial equivalent; none of them can be checked."]],
          widths=[0.35, 2.25, 3.65])
    para(doc,
         "Three claims that a reader might expect us to make, we deliberately "
         "do not. We do not claim to be first to gate an agent write (§2.5). "
         "We do not claim novelty in relaxing the fixed-W assumption (§2.2). "
         "And we make no comparison between our update latency and an "
         "operator's internal review cycle: that would compare a compute step "
         "to a governance step, since a review cycle is slow because a human "
         "is committing capital, not because software is slow.", align="j")

    doc.add_heading("5.9  Engineering feasibility", level=2)
    para(doc,
         "The analytical panel is 811,200 rows and roughly 260 MB, and the "
         "warehouse compresses to under 500 MB. This is deliberate: the hard "
         "problem is identification, not throughput. No distributed compute "
         "appears anywhere in the design.", align="j")
    para(doc,
         "The one component that does not fit that description is road-network "
         "preprocessing. A full-US extract requires memory well beyond a "
         "laptop, and retaining processed artifacts for ten metros "
         "simultaneously would consume roughly 30 GB. The design therefore "
         "removes routing from the critical path entirely: for each metro in "
         "turn, the road graph is processed offline, the origin-destination "
         "drive-time matrix is extracted, and every intermediate artifact is "
         "deleted before the next metro begins. Peak disk falls from "
         "approximately 60 GB to 8 GB, and the deployed application reads a "
         "single 10 MB lookup with no routing dependency at all.", align="j")
    para(doc,
         "As a fallback, road distance can be approximated as great-circle "
         "distance scaled by a circuity factor calibrated on one metro "
         "against routed ground truth, with the residual error reported. "
         "Since Daganzo's law is itself a continuous approximation, exact "
         "routing is precision in the wrong place if it threatens delivery.",
         align="j")
    figure(doc, fig_dir, "fig12_scale",
           "Figure 14.  Scale and impact. Row count is the only dimension on "
           "which this project is small.")
    page_break(doc)
