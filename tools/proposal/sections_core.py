"""Sections 3-4: Research Objectives and Data."""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scope import SCOPE
from hazard_metrics import HAZARD

from docx_kit import (BLUE, CRITICAL, GOOD, INK, INK_2, MUTED, ORANGE,
                      bullets, callout, figure, page_break, para, rich, table)


def objectives(doc, fig_dir):
    """Append the objectives section, with its success criteria."""
    doc.add_heading("3.  Research Objectives", level=1)
    para(doc,
         "Consistent with the identification discussion in §4.5, model output "
         "is interpreted as operator-consistent expansion desirability rather "
         "than objective demand. Because the outcome we model is observable, "
         "that framing is literally accurate rather than a hedge: the model predicts what the "
         "operator did, which is what we observe.", align="j")

    doc.add_heading("Objective 1  —  Siting and timing model with a real "
                    "backtest", level=2)
    para(doc,
         "Estimate, for each ZCTA and quarter, the probability that the "
         "operator enables same-day service, as a discrete-time hazard model "
         "over ACS demographics, TIGER/Line geography, Zillow property "
         "covariates, Census CBP retail density, a Huff-style gravity pull "
         "factor, and rate-of-change features derived from the monthly "
         "sources in §4.2. A zero-inflated negative binomial volume model and a "
         "LightGBM benchmark with SHAP attribution are retained as secondary "
         "analyses.", align="j")
    table(doc,
          ["Metric", "Target", "Why this metric"],
          [["AUC-ROC, out-of-time", "≥ 0.80",
            "Rank quality on a forecast that was actually scored"],
           ["PR-AUC", "Well above base rate (~0.06)",
            "The positive class is rare; ROC alone flatters it"],
           ["Brier score", "≤ 0.06", "Combines calibration and sharpness"],
           ["Expected calibration error", "< 0.05",
            "A stated 60% probability should occur ~60% of the time"],
           ["precision@100", "≥ 0.60",
            "The decision is a shortlist, so shortlist quality is the test"],
           ["Conformal interval coverage", "Within 2pp of nominal",
            "Distribution-free and empirically verified, not assumed"],
           ["Spearman vs LightGBM, top decile", "≥ 0.80 (bootstrap CI)",
            "Convergent validity across two structurally different models"],
           ["AUC under simulated label noise", "≥ 0.78 at 15% date error",
            "Bounds the effect of target-variable measurement error (§4.3)"],
           ["Top-100 overlap, H3 vs ZCTA grain", "≥ 0.70",
            "Shows the ranking is not an artefact of the spatial partition"]],
          widths=[1.9, 1.7, 2.5])
    callout(doc, "WHY NOT MAPE",
            "MAPE divides by the actual value "
            "and is undefined wherever that value is zero — and the "
            "premise of the demand model is that many areas are structural "
            "zeros. It also would have been computed against a target "
            "constructed from its own predictors (§4.2). Hyndman and Koehler "
            "(2006) is the standard reference for why percentage errors fail "
            "on such data.", accent=CRITICAL, fill="FBEAEA")
    para(doc,
         "Validation is out-of-time, not merely out-of-sample: the model is "
         "trained on facilities open through 2023 and scored against openings "
         "observed in 2024–2025. Two metros are additionally withheld from "
         "training entirely. If the criteria are not met, the failure is "
         "reported; the validation set is not used for retraining.", align="j")
    callout(doc, "THE CRITERIA ABOVE WERE NOT MET",
            "The model has since been fitted and scored, and Figure 4 shows "
            f"the measured result rather than the target. On the primary "
            f"hold-out AUC is {HAZARD.auc:.4f} against {HAZARD.null_auc:.4f} "
            f"for a constant; on the secondary temporal hold-out it is "
            f"{HAZARD.t_auc:.4f}. The Brier score is {HAZARD.brier:.6f} "
            f"against {HAZARD.null_brier:.6f} for the same constant over the "
            f"same {HAZARD.n_rows:,} rows, and the calibration error is "
            f"{HAZARD.ece:.5f} against {HAZARD.null_ece:.5f} — a model that "
            "ignores every covariate is better calibrated than ours. "
            "precision@100 was never computed. We report the raw Brier pair "
            "rather than a skill score, because Gneiting and Raftery (2007, "
            "§2.3 p.362) show skill scores are generally improper even when "
            "the underlying score is proper. The diagnosis is a unit-of-analysis "
            "error rather than a sample-size one — one delivery station "
            "switches on a median of 58 ZCTAs at once, so what the panel "
            "records as hundreds of independent events is a much smaller "
            "number of siting decisions plus a catchment circle — and it "
            "is the reason §5.3 is being respecified as a conditional "
            "choice over ZCTAs given that a station opens.",
            accent=CRITICAL, fill="FBEAEA")
    figure(doc, fig_dir, "fig08_backtest",
           "Figure 4.  The measured backtest. Ranking, the proper score and "
           "calibration, each against a null model that predicts one "
           f"constant. Source: outputs/metrics/hazard_report.json, run "
           f"{HAZARD.run_id}.")

    doc.add_heading("Objective 2  —  Cannibalization as a causal decay curve",
                    level=2)
    para(doc,
         "Estimate the cannibalization effect by distance band using spatial "
         "synthetic control with placebo inference, and use the estimated "
         "decay to construct W. Success criteria: pre-treatment fit RMSE "
         "below 8% of the outcome mean; a post/pre RMSPE-ratio permutation "
         "p-value below 0.10 against in-space placebos; and a reported decay "
         "curve with confidence bands at each distance band.", align="j")
    para(doc,
         "Pre-treatment fit alone is necessary but not sufficient — it is possible to fit the "
         "pre-period well and estimate a treatment effect indistinguishable "
         "from placebo noise. Permutation inference is the Abadie standard "
         "and its absence is a legitimate reviewer objection.", align="j")

    doc.add_heading("Objective 3  —  Agent with identification gates", level=2)
    para(doc,
         "Implement a ReAct agent with three MCP-wrapped tools and a six-gate "
         "mutation path. Evaluation uses execution accuracy — does the "
         "generated query return the same result set as a gold query — "
         "on at least 100 questions stratified into four difficulty tiers, "
         "reported with Wilson confidence intervals.", align="j")
    callout(doc, "CALIBRATING THE TARGET AGAINST THE FIELD",
            "On the BIRD benchmark (Li et al., NeurIPS 2023) the best public "
            "systems reach roughly 80% execution accuracy against a human "
            "baseline near 93%. Any target above that on a self-authored "
            "question set would be an above-state-of-the-art claim on an "
            "unfalsifiable test. At n = 40 an observed 85% carries a 95% "
            "Wilson interval of roughly [71%, 93%], so success and failure "
            "are statistically indistinguishable. We target 75% overall at "
            "n ≥ 100 and report per-tier.")
    para(doc,
         "Separately, for the mutation path: at least 90% of mutations that "
         "materially change the cannibalization coefficient must be caught by "
         "gate 6 on a seeded adversarial set of 50 perturbations.", align="j")

    doc.add_heading("Objective 4  —  Deployable application and open dataset",
                    level=2)
    bullets(doc, [
        "A deployed application with an operator view and a public planning "
        "view, loading in under five seconds.",
        "The ZCTA-level facility-opening panel published as an open dataset "
        "with a data card — the most durable artifact the project produces.",
        "Metro-level capital aggregates validated against public "
        "capital-expenditure disclosures to within 25% — the only "
        "externally falsifiable number in the system.",
        "Net present value reported in units of contribution margin with "
        "explicit break-even thresholds, so that no unobservable revenue "
        "figure is asserted (§5.6).",
        "A methods paper draft, a reproducibility write-up, and a "
        "timestamped public forecast registry so predictions can be scored "
        "later by anyone.",
    ])
    page_break(doc)


def data_section(doc, fig_dir):
    """Append the data section, sourced from the source registry."""
    doc.add_heading("4.  Data", level=1)

    doc.add_heading("4.1  Sources", level=2)
    para(doc,
         "Eleven public sources are ingested through a common ELT pipeline. "
         "No licensed panel and no paid API is required, which is what makes "
         "the system reproducible by a third party. Sources are selected not "
         "only for what they measure but for how often they update: two are "
         "included specifically to offset the reporting lag in the census "
         "series (§4.2).", align="j")
    table(doc,
          ["Source", "Grain", "Role", "Access"],
          [["Census ACS 5-year", "ZCTA", "Demographics, income, age",
            "Public API"],
           ["TIGER/Line", "ZCTA polygon", "Geometry for spatial joins",
            "Bulk download"],
           ["Zillow ZORI / ZHVI", "ZIP", "Rent and value bands", "Public CSV"],
           ["Census County Business Patterns", "ZIP × NAICS",
            "Retail density (competitive pull)", "Bulk download"],
           ["BLS OES", "Metro", "Driver and warehouse wages", "Bulk download"],
           ["EIA", "Region", "Fuel and industrial electricity prices",
            "Bulk download"],
           ["Facility panel and open dates", "Facility",
            "The target variable — see §4.2", "Public inventory + filings"],
           ["EPA EJScreen", "Block group",
            "Environmental-justice indices for the equity overlay",
            "Bulk download"],
           ["OpenStreetMap", "Road network",
            "Drive times, used once offline (§5.9)", "Geofabrik / BBBike"]],
          widths=[1.75, 1.15, 2.35, 1.0])
    callout(doc, "WHY AN ADMINISTRATIVE SOURCE RATHER THAN A BUSINESS DIRECTORY",
            "A commercial directory such as Yelp Fusion permits 5,000 requests per day, which "
            "puts acquisition of the retail-density feature on a three-day "
            "critical path and requires an API key that a replicator may not "
            "have. Census County Business Patterns provides establishment "
            "counts by ZIP and NAICS as a bulk download in minutes, with no "
            "key and no rate limit. It is also an administrative universe "
            "rather than a self-selected directory, which avoids a coverage "
            "bias that would otherwise have to be disclosed: directories "
            "under-represent minority-owned, cash and informal businesses, "
            "and if that under-representation correlates with ZCTA "
            "demographics the proxy inherits the bias.")

    doc.add_heading("4.2  Data currency and the reporting lag", level=2)
    para(doc,
         "American Community Survey five-year estimates carry an 18 to 24 "
         "month reporting lag. Taken alone this would be a serious weakness "
         "in a model of decisions being made now. Three features of the "
         "design address it.", align="j")
    para(doc,
         "First, and most importantly, the lag is shared with the "
         "decision-maker. Operators plan siting from the same public census "
         "releases; there is no private real-time census. Our disadvantage "
         "relative to an operator lies in order history, not in demographic "
         "covariates — which is precisely why the estimand in §4.3 is "
         "the siting decision rather than demand.", align="j")
    para(doc,
         "Second, siting decisions have long lead times. Site search, lease "
         "negotiation, permitting, fitout and hiring together span roughly 18 "
         "to 36 months, so a facility opening in 2025 was decided in 2023 on "
         "2021–22 covariates. Aligning covariate vintage to decision vintage "
         "is therefore correct specification. Using contemporaneous data to "
         "explain a decision taken two years earlier would introduce "
         "information the decision-maker did not have.", align="j")
    para(doc,
         "Third, the covariates that genuinely move quickly are sourced "
         "quickly. Zillow rent and value indices are monthly; the Census "
         "Building Permits Survey is monthly and is a forward indicator, "
         "since construction precedes population; EIA prices are monthly; and "
         "ACS one-year estimates give metro-level context at roughly a "
         "nine-month lag. Slow sources supply level features and fast sources "
         "supply rate-of-change features, so the model observes trajectory "
         "rather than only position.", align="j")
    figure(doc, fig_dir, "fig13_currency",
           "Figure 5.  Sources ordered by reporting lag, against the "
           "operator's own decision lead time.")
    para(doc,
         "The residual risk is stated rather than resolved: an area that "
         "changed sharply within the last eighteen months and generates no "
         "permit or rent signal will be misclassified. Where fast and slow "
         "signals disagree materially, the area is flagged as low-confidence "
         "in the application rather than silently ranked.", align="j")

    doc.add_heading("4.3  The target variable", level=2)
    callout(doc, "WHY THE TARGET MUST BE OBSERVABLE",
            "The tempting alternative is to model order volume per ZCTA. "
            "Nobody outside the operator can observe it, so it would have to "
            "be constructed — typically by allocating disclosed "
            "aggregate volume across ZCTAs in proportion to demographics and "
            "retail density. A model of demographics and retail density would "
            "then be fitted to predict it. That target is built from its own "
            "predictors: any fit statistic measures how well the model "
            "reproduces the allocation arithmetic, and a good score is "
            "evidence of the defect rather than of predictive skill. We do "
            "not do this.",
            accent=CRITICAL, fill="FBEAEA")
    figure(doc, fig_dir, "fig04_estimand",
           "Figure 6.  Left: the circularity that arises from a constructed "
           "target. Right: the observable estimand we use instead.")
    para(doc,
         "The primary outcome is now observable: for each ZCTA and quarter, "
         "whether the operator offered same-day service, and the quarter in "
         "which it first did. This is recoverable from the operator's public "
         "delivery-speed checker, from the public facility inventory with "
         "open dates, and from published expansion announcements.", align="j")
    para(doc,
         "The zero-inflated negative binomial volume model is retained as a "
         "secondary analysis and relabelled honestly: it is a "
         "specification-recovery exercise that asks whether ZINB recovers a "
         "known data-generating process under realistic covariate structure. "
         "It is not a demand forecast, and every downstream net-present-value "
         "figure derived from it is labelled as conditional on the volume "
         "allocation assumption.", align="j")
    para(doc,
         "Because facility open dates are the target rather than a covariate, "
         "their quality is a first-order concern and is treated as a "
         "measurement problem in its own right. Four steps apply. A random "
         "census of 43 facilities carries a per-row source, cross-checked "
         "against filings and local "
         "press, and the measured error rate is reported alongside every "
         "accuracy figure. Dates confirmed by two independent sources are "
         "marked high-confidence; single-source dates are flagged. Outcomes "
         "are modelled at quarterly rather than monthly grain, which is "
         "robust to date noise and sufficient for a decision with an "
         "eighteen-month horizon. And where the operator's own "
         "delivery-availability check can be queried directly, it is "
         "preferred over inferring service from a building.", align="j")
    callout(doc, "BOUNDING THE DAMAGE RATHER THAN HOPING",
            "An unmeasured label-error rate makes a headline accuracy figure "
            "uninterpretable. We therefore run a label-noise simulation: "
            "deliberately corrupt a known fraction of open dates by plus or "
            "minus one quarter and re-run the backtest. This converts an "
            "unknown into a bound, producing statements of the form 'at a 15 "
            f"per cent date-error rate, AUC degrades from the measured "
            f"{HAZARD.auc:.4f} to X'. The simulation has not been run; the "
            "form of the statement is given so that the bound is reported "
            "with the headline metric rather than after it is challenged.")

    doc.add_heading("4.4  Sampling frame", level=2)
    para(doc,
         "Causal estimation requires treated and control structure and is "
         f"conducted on ten pilot metros comprising {SCOPE.zctas_label} ZCTAs "
         f"({SCOPE.definition}): "
         "San Francisco Bay Area, New York, Chicago, Austin, Seattle, Denver, "
         "Miami, Nashville, Phoenix and Boise. Phoenix and Boise are withheld "
         "from training and used only for out-of-metro validation.", align="j")
    para(doc,
         "The siting propensity model is additionally fitted across all "
         "33,000 US ZCTAs. Because the analytical panel is small, national "
         "coverage costs approximately 0.46 GB and roughly one day of work "
         "— scope that would be unaffordable if the project were "
         "structured around large data.", align="j")

    doc.add_heading("4.5  Limitations and mitigations", level=2)
    para(doc,
         "Every limitation below is paired with the mitigation applied and "
         "the risk that remains after it. Four limitations at the end of this "
         "section have no mitigation; stating that plainly is what makes the "
         "others credible.", align="j")
    table(doc,
          ["Limitation", "Mitigation applied", "Residual risk"],
          [["ACS reporting lag of 18–24 months",
            "Lag is shared with the decision-maker and aligned to decision "
            "lead time; ACS 1-year metro context; monthly permits, rents and "
            "energy prices supply rate-of-change features (§4.2)",
            "Sharp recent change with no permit or rent signal; flagged "
            "low-confidence"],
           ["Facility open dates may be inaccurate",
            "a 43-row census with per-row sources and a measured bound "
            "(5 of 5 MWPVL cross-checks held, lags 4-345 months); "
            "two-source confirmation; quarterly grain; label-noise simulation "
            "bounding the effect on AUC (§4.3)",
            "Small delivery stations under-reported relative to large "
            "facilities"],
           ["Large ACS margins of error at ZCTA grain",
            "Published margins propagated into the Monte Carlo as an "
            "uncertainty input rather than discarded; high-margin areas "
            "flagged",
            "Small-population areas remain noisy"],
           ["Modifiable areal unit problem",
            "One vintage pinned and crosswalked; ZCTA count enforced by data "
            "contract; conclusions re-run at H3 hexagonal grain",
            "H3 and ZCTA may disagree, in which case both are reported"],
           ["Donor-pool scarcity in saturated metros",
            "Contamination defined by the measured decay radius rather than "
            "by contiguity, recovering donors a conservative rule discards; "
            "staggered adoption uses later-treated units as earlier controls; "
            "cross-metro donors permitted; donor weight concentration "
            "reported",
            "Most saturated metros may be reported as not estimable"],
           ["Machine-extracted facility attributes are generated regressors",
            "Design-based supervised learning (Egami et al., 2023) using the "
            "hand-labelled sample above as the correction set",
            "None material once corrected"],
           ["Residential indices proxy commercial land cost",
            "Composite validated externally against disclosed capital "
            "expenditure; per-proxy sensitivity reported (§5.5)",
            "A proxy biased in a way correlated with the outcome"]],
          widths=[1.5, 2.85, 1.75])
    para(doc,
         "Four limitations admit no mitigation and are therefore not "
         "mitigated. Order volume, revenue and margin are unobservable in "
         "public data, so no accuracy claim is made on dollar figures and "
         "results are reported in units of contribution margin (§5.6). The "
         "cannibalization coefficient cannot be validated against any public "
         "number; we report the placebo distribution and confidence bands and "
         "claim identification under stated assumptions rather than "
         "correctness. Internal constraints — existing lease "
         "obligations, capital rationing, executive preference — are "
         "invisible, which is why output is framed as operator-consistent "
         "desirability. And it is possible that public data has an accuracy "
         "ceiling below what the decision requires; that possibility is RQ4, "
         "and a negative answer is reported as a finding rather than "
         "suppressed.", align="j")

    doc.add_heading("4.6  Identification strategy and selection", level=2)
    para(doc,
         "Observed service enablement is not a random sample of latent "
         "viability. Operators build where they judge it commercially "
         "sensible, and the areas they skipped are not a randomised "
         "counterfactual. Ignoring this would let the model confound "
         "viability with revealed selection preference.", align="j")
    para(doc,
         "For the San Francisco Bay pilot metro we implement the full Heckman "
         "(1979) two-step correction. The selection equation is a probit over "
         "all Bay Area ZCTAs predicting whether a node touching that ZCTA was "
         "opened, using the demand covariates plus one instrument: distance "
         "to the nearest commercially zoned ZIP centroid. The outcome "
         "equation is augmented with the inverse Mills ratio. Corrected and "
         "naive coefficients are both reported so the difference is visible, "
         "along with the first-stage F-statistic.", align="j")
    para(doc,
         "The exclusion restriction deserves scrutiny rather than assertion. "
         "Commercial-zoning proximity plausibly affects an operator's siting "
         "decision, but it also correlates with retail agglomeration, "
         "employment density and traffic, each of which could drive "
         "residential demand directly. We therefore report a sensitivity "
         "analysis showing how the corrected coefficients move under small "
         "assumed direct effects of the instrument, and we state the residual "
         "risk rather than claiming the restriction is satisfied.", align="j")
    para(doc,
         "Formal correction on all ten metros is out of scope for an "
         "eight-week project. For the remaining nine, coefficients are "
         "reported with an explicit footnote that they embed the operator's "
         "selection preference. Extending the correction via causal forests "
         "or double machine learning is named as future work.", align="j")
    para(doc,
         "Finally, an equity audit stratifies results by ZCTA "
         "majority-demographic group and reports per-stratum metrics. Where a "
         "stratum's error exceeds the population error by more than 50%, the "
         "application displays a reliability warning for that context. This "
         "is aggregate-only reporting; no demographic classification enters "
         "any model input.", align="j")
    page_break(doc)
