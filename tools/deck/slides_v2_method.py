"""V2 research deck, slides 1-16: positioning, estimand, identification."""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scope import SCOPE

from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from pptx_kit import (BLUE, BLUE_L, GREEN, GREEN_L, INK, INK_2, LINE, MARGIN,
                      MUTED, ORANGE, ORANGE_L, PLANE, RED, RED_L, W, WHITE,
                      banner, blank, bullets, card, eq, figure_slide, footer,
                      picture, stat, table, text, title)

FOOT = "Siting Atlas  ·  technical supplement"


def v01_title(prs, meta):
    """Title slide for the technical supplement."""
    s = blank(prs)
    bar = s.shapes.add_shape(1, Inches(0), Inches(0), W, Inches(0.16))
    bar.fill.solid(); bar.fill.fore_color.rgb = BLUE
    bar.line.fill.background(); bar.shadow.inherit = False

    text(s, MARGIN, Inches(1.35), Inches(12), Inches(0.9), "SITING ATLAS",
         size=44, bold=True, color=BLUE)
    text(s, MARGIN, Inches(2.22), Inches(12), Inches(0.45),
         "TECHNICAL SUPPLEMENT  ·  identification, estimation, inference",
         size=15, color=ORANGE)
    text(s, MARGIN, Inches(3.0), Inches(11.6), Inches(1.1),
         "Agent-Assisted Spatial Causal Inference for Sub-24-Hour Delivery\n"
         "Territory Expansion under Cannibalization Constraints",
         size=20, bold=True, color=INK, spacing=1.24)
    text(s, MARGIN, Inches(4.25), Inches(11.6), Inches(0.9),
         "Companion to the overview deck. Assumes familiarity with potential "
         "outcomes,\npanel methods and synthetic control.",
         size=13, color=INK_2, italic=True, spacing=1.3)
    text(s, MARGIN, Inches(5.35), Inches(7), Inches(1.1),
         f"{meta['p1']}   ·   {meta['p2']}   ·   {meta['p3']}\n"
         f"MS Business Analytics, CSU East Bay   ·   "
         f"{meta['instructor']}",
         size=12.5, color=INK_2, spacing=1.35)
    text(s, MARGIN, Inches(6.62), Inches(12.1), Inches(0.4),
         "Not affiliated with any operator analysed. Operator names are used "
         "descriptively.", size=9, color=MUTED, italic=True)
    return s


def v02_contribution(prs):
    """The four contribution claims, each bounded against both the
    literature and shipped commercial products."""
    s = blank(prs)
    top = title(s, "Contribution, stated precisely",
                "Four claims, each bounded so that neither a published paper "
                "nor a product datasheet falsifies it.")
    rows = [
        ["", "Claim", "Bounded by", "Status"],
        ["C1", "Inferential integrity as a distinct failure mode for "
               "state-mutating agents: a write satisfying schema, geocoding, "
               "confidence and audit gates may still violate a downstream "
               "identification assumption",
         "Not a claim to novelty in gating writes (arXiv:2608.14590; "
         "2511.06778; 2211.15363)", "Novel"],
        ["C2", "Distance-decay parameter of same-day cannibalization, used "
               "to construct W endogenously",
         "Estimator is Pollmann (arXiv:2011.00373). Parameter is the "
         "contribution", "Novel parameter"],
        ["C3", "Public-data explainability ceiling for firm siting; "
               "cross-operator transferability of the fitted preference",
         "Descriptive, but unreported in the literature", "Novel measurement"],
        ["C4", "Open, re-runnable artifact: panel, harness and estimates",
         "All techniques have licensed commercial equivalents", "Access"],
    ]
    _, tb = table(s, MARGIN, top, W - 2 * MARGIN, rows,
                  col_w=[Inches(0.45), Inches(4.9), Inches(4.6),
                         Inches(2.15)], size=11, row_h=Inches(0.5))
    banner(s, tb + Inches(0.16),
           "Withdrawn after prior-art review: novelty in gated writes; "
           "novelty in relaxing fixed-W; any latency comparison against an "
           "operator's governance cycle.", accent=RED, fill=RED_L, size=13)
    footer(s, FOOT, 2)
    return s


def v03_positioning(prs, fig_dir):
    """Prior art: what is closed and what remains open.
    Embeds fig10_positioning."""
    return figure_slide(
        prs, fig_dir, "fig10_positioning",
        "Prior art: what is closed and what remains open",
        "Two reviews — published literature and shipped commercial "
        "product. Both reported.")


def v04_questions(prs):
    """The research questions, pre-registered and falsifiable."""
    s = blank(prs)
    top = title(s, "Research questions")
    y = top
    for tag, q, note in [
        ("RQ1", "Can a discrete-time hazard over public ZCTA covariates "
                "recover the operator's siting and timing decision at "
                "out-of-time AUC ≥ 0.80 on metros withheld from training?",
         "Falsifiable. Pre-registered target; failure reported, no retraining "
         "on the validation set."),
        ("RQ2", "Does event-driven revision of the spatial weight matrix "
                "materially change the estimated cannibalization "
                "coefficient, or are estimates robust to revision as LeSage "
                "and Pace (2014) argue?",
         "Pre-registered before estimation. Publishable under either "
         "outcome — a moved coefficient challenges a robustness claim; an "
         "unmoved one confirms it under a novel perturbation."),
        ("RQ3", "Can validation gates be constructed that detect when an "
                "agent-proposed write preserves data integrity while "
                "invalidating a causal identification assumption?",
         "Evaluated on a seeded adversarial set of 50 perturbations; target "
         "≥ 90% detection of mutations that move θ beyond threshold."),
        ("RQ4", "What share of the operator's revealed siting behaviour is "
                "explainable from public data alone?",
         "Descriptive. A low value is a finding about opacity, not a failed "
         "project."),
    ]:
        card(s, MARGIN, y, W - 2 * MARGIN, Inches(1.18), None,
             "", accent=BLUE if tag != "RQ2" else ORANGE,
             fill=WHITE if tag != "RQ2" else ORANGE_L)
        text(s, MARGIN + Inches(0.22), y + Inches(0.14), Inches(0.8),
             Inches(0.4), tag, size=15, bold=True,
             color=BLUE if tag != "RQ2" else ORANGE)
        text(s, MARGIN + Inches(1.05), y + Inches(0.12), Inches(11.0),
             Inches(0.52), q, size=12.5, color=INK)
        text(s, MARGIN + Inches(1.05), y + Inches(0.68), Inches(11.0),
             Inches(0.42), note, size=10.5, color=MUTED, italic=True)
        y += Inches(1.30)
    footer(s, FOOT, 4)
    return s


def v05_setup(prs):
    """Setup and notation: the ZCTA-quarter panel and the estimand."""
    s = blank(prs)
    top = title(s, "Setup and notation",
                "Panel of ZCTA i in quarter t; treatment is first enablement "
                "of same-day service.")
    _, y = eq(s, MARGIN, top, W - 2 * MARGIN,
              f"i = 1..N   ZCTA          N = {SCOPE.zctas_label} modelled  /  {SCOPE.national_zctas_label} national\n"
              "t = 1..T   quarter       T = 44   (2015Q1 - 2025Q4)\n"
              "D_it in {0,1}            same-day service available\n"
              "E_i = min{ t : D_it = 1 }    first enablement (right-censored)\n"
              "X_it                     public covariates, vintage-aligned\n"
              "Y_it                     2-day order proxy (secondary)\n"
              "W(rho)                   spatial weights, radius rho\n"
              "theta                    cannibalization coefficient",
              size=13.5, align=PP_ALIGN.LEFT)
    card(s, MARGIN, y + Inches(0.22), Inches(6.0), Inches(1.72),
         "PRIMARY ESTIMAND",
         "h_it = P( E_i = t | E_i >= t , X_it )\n\n"
         "The conditional hazard of first enablement. Observable, "
         "right-censored, and scoreable out of time.",
         accent=GREEN, fill=GREEN_L, bsize=12.5)
    card(s, MARGIN + Inches(6.3), y + Inches(0.22), Inches(6.0), Inches(1.72),
         "SECONDARY ESTIMAND",
         "theta = E[ Y_it(0) - Y_it(1) | D_it = 1 ] / E[ Y_it(0) | D_it = 1 ]\n"
         "\nCannibalization as a proportional treatment effect on the "
         "incumbent channel.",
         accent=BLUE, bsize=12.5)
    footer(s, FOOT, 5)
    return s


def v06_estimand_choice(prs):
    """Why the estimand is enablement rather than volume — an
    identification argument, not a data-availability excuse."""
    s = blank(prs)
    top = title(s, "Why the estimand is enablement, not volume",
                "An identification argument, not a data-availability excuse.")
    card(s, MARGIN, top, Inches(6.0), Inches(2.45),
         "THE CONSTRUCTED-TARGET FAILURE",
         "Volume is unobserved, so it must be allocated:\n\n"
         "   Y~_i = Q · g(X_i) / Σ_j g(X_j)\n\n"
         "Fitting f(X_i) → Y~_i recovers g, not the data-generating\n"
         "process. R² is bounded below by the approximation error of\n"
         "f to g and is uninformative about the phenomenon.\n\n"
         "A GOOD fit is evidence of the defect.",
         accent=RED, fill=RED_L, bsize=12, mono=False)
    card(s, MARGIN + Inches(6.3), top, Inches(6.0), Inches(2.45),
         "WHAT ENABLEMENT BUYS",
         "D_it is directly observable from the operator's own service\n"
         "check and from facility records.\n\n"
         "  · admits a genuine out-of-time backtest\n"
         "  · supports proper scoring rules (Brier, log loss)\n"
         "  · makes 'operator-consistent desirability' literal rather\n"
         "    than a hedge\n"
         "  · censoring is handled, not mislabelled as a negative",
         accent=GREEN, fill=GREEN_L, bsize=12)
    banner(s, Inches(4.42),
           "The volume model is retained as specification recovery under a "
           "stated allocation assumption, and every dollar figure derived "
           "from it is labelled conditional.", accent=BLUE, fill=BLUE_L,
           size=13)
    footer(s, FOOT, 6)
    return s


def v07_hazard(prs):
    """The siting model: discrete-time hazard with a cloglog link."""
    s = blank(prs)
    top = title(s, "Siting model — discrete-time hazard",
                "Complementary log-log link; grouped-duration data with "
                "time-varying covariates.")
    _, y = eq(s, MARGIN, top, W - 2 * MARGIN,
              "cloglog( h_it )  =  log( -log( 1 - h_it ) )\n"
              "                 =  alpha(t)  +  X_it' beta  +  u_m(i)\n\n"
              "alpha(t)   flexible baseline in time since nearest node opened\n"
              "u_m(i)     metro random effect,  u ~ N(0, sigma^2)\n"
              "S_i(t)     = PROD_{s<=t} ( 1 - h_is )     survival to t",
              size=13.5, align=PP_ALIGN.LEFT)
    card(s, MARGIN, y + Inches(0.2), Inches(3.9), Inches(2.0),
         "WHY CLOGLOG",
         "It is the grouped-duration analogue of a proportional-hazards "
         "model, so coefficients carry a hazard-ratio reading and the "
         "specification is invariant to the interval width we happened to "
         "choose.", accent=BLUE, bsize=12)
    card(s, MARGIN + Inches(4.2), y + Inches(0.2), Inches(3.9), Inches(2.0),
         "WHY NOT A CLASSIFIER",
         "A logit on 'ever enabled' mislabels censored units as negatives, "
         "discards timing, and cannot use time-varying covariates at their "
         "contemporaneous value.", accent=BLUE, bsize=12)
    card(s, MARGIN + Inches(8.4), y + Inches(0.2), Inches(3.9), Inches(2.0),
         "COVARIATE VINTAGE",
         "X_it uses the vintage AVAILABLE at t, not the latest release. "
         "Levels from slow sources, rates of change from monthly ones. "
         "Anything else leaks future information.",
         accent=ORANGE, fill=ORANGE_L, bsize=12)
    footer(s, FOOT, 7)
    return s


def v08_selection(prs):
    """Heckman two-step, because treatment assignment is endogenous by
    construction — the operator chose where to build."""
    s = blank(prs)
    top = title(s, "Selection — Heckman two-step",
                "Treatment assignment is endogenous by construction: the "
                "operator selects on expected profitability.")
    _, y = eq(s, MARGIN, top, W - 2 * MARGIN,
              "STEP 1   S_i* = Z_i' gamma + X_i' delta + e_i ,   "
              "S_i = 1{ S_i* > 0 }\n"
              "         lambda_i = phi(Z_i'gamma) / Phi(Z_i'gamma)   "
              "(inverse Mills ratio)\n\n"
              "STEP 2   outcome equation augmented with lambda_i ; "
              "rho·sigma identified from its coefficient",
              size=13.5, align=PP_ALIGN.LEFT)
    card(s, MARGIN, y + Inches(0.2), Inches(6.0), Inches(2.35),
         "THE INSTRUMENT, AND ITS WEAKNESS",
         "Z = distance to nearest commercially zoned centroid.\n\n"
         "RELEVANCE — testable. Report first-stage F; convention F > 10.\n\n"
         "EXCLUSION — not testable. Commercial zoning correlates with "
         "employment density and traffic, either of which could enter demand "
         "directly. We do not assert the restriction holds.",
         accent=RED, fill=RED_L, bsize=12)
    card(s, MARGIN + Inches(6.3), y + Inches(0.2), Inches(6.0), Inches(2.35),
         "WHAT WE REPORT INSTEAD",
         "· first-stage F and partial R²\n"
         "· corrected AND naive coefficients side by side\n"
         "· a sensitivity analysis over an assumed direct effect "
         "gamma_direct ∈ [0, δ̄], showing the path of the corrected estimate\n"
         "· the value of gamma_direct at which the sign flips\n\n"
         "Survival under a plausible violation is worth more than a claim of "
         "no violation.", accent=GREEN, fill=GREEN_L, bsize=12)
    footer(s, FOOT, 8)
    return s


def v09_assumptions(prs):
    """Every identification assumption, labelled testable, partially
    testable or untestable."""
    s = blank(prs)
    top = title(s, "Identification assumptions, and how each is handled",
                "Testable, partially testable, and untestable — labelled "
                "as such.")
    rows = [
        ["Assumption", "Status", "What we do"],
        ["Conditional independence of enablement given X and λ",
         "Untestable",
         "Heckman correction on the pilot metro; explicit disclosure "
         "elsewhere"],
        ["Exclusion restriction on Z", "Untestable",
         "Sensitivity path over an assumed direct effect; report the "
         "sign-flip point"],
        ["Parallel trends (pre-treatment)", "Partially testable",
         "Pre-period fit reported and plotted; placebo distribution built "
         "from untreated units"],
        ["No interference (SUTVA)", "Known violated",
         "Not assumed. Spillover reach estimated by distance band; "
         "contaminated donors excluded by the measured radius"],
        ["Correct functional form", "Partially testable",
         "Non-parametric LightGBM benchmark; convergent-validity Spearman "
         "with bootstrap CI"],
        ["Covariates measured without error", "Known violated",
         "ACS margins of error propagated; LLM-extracted fields corrected as "
         "generated regressors (Egami et al. 2023)"],
        ["Target measured without error", "Known violated",
         "a 43-row census with per-row sources, a measured accuracy "
         "bound, and a label-noise "
         "simulation bounding the effect on AUC"],
    ]
    table(s, MARGIN, top, W - 2 * MARGIN, rows,
          col_w=[Inches(3.7), Inches(2.1), Inches(6.3)], size=11,
          row_h=Inches(0.42))
    footer(s, FOOT, 9)
    return s


def v10_scm(prs):
    """Cannibalisation via spatial synthetic control, with a restricted
    donor pool."""
    s = blank(prs)
    top = title(s, "Cannibalization — spatial synthetic control",
                "Convex-combination counterfactual with a donor pool "
                "restricted by measured spillover reach.")
    _, y = eq(s, MARGIN, top, W - 2 * MARGIN,
              "w*  =  argmin_w  || X_1 - X_0 w ||_V   "
              "s.t.  w_j >= 0 ,  SUM_j w_j = 1\n\n"
              "tau_1t  =  Y_1t  -  SUM_{j in J} w*_j Y_jt\n\n"
              "J  =  { j : D_jt = 0  for all t <= T }  \\  "
              "{ j : dist(j, treated) < rho^ }",
              size=13.5, align=PP_ALIGN.LEFT)
    card(s, MARGIN, y + Inches(0.2), Inches(6.0), Inches(2.3),
         "DONOR POOL, AND WHY ρ̂ MATTERS",
         "A contiguity rule excludes every neighbour of a treated unit. In a "
         "saturating network that empties the pool.\n\n"
         "Because contamination is defined by the ESTIMATED radius ρ̂ rather "
         "than by shared borders, donors a conservative rule discards are "
         "recovered. Staggered adoption adds later-treated units as controls "
         "for earlier ones.", accent=ORANGE, fill=ORANGE_L, bsize=12)
    card(s, MARGIN + Inches(6.3), y + Inches(0.2), Inches(6.0), Inches(2.3),
         "DIAGNOSTICS REPORTED",
         "· pre-treatment RMSPE, target < 8% of outcome mean\n"
         "· donor-pool size and weight concentration (max w*_j)\n"
         "· the fitted covariate balance table\n\n"
         "Where no credible pool exists the estimate is reported as NOT "
         "ESTIMABLE rather than produced.", accent=BLUE, bsize=12)
    footer(s, FOOT, 10)
    return s


def v11_inference(prs):
    """Permutation inference, because one treated unit makes an
    asymptotic standard error meaningless."""
    s = blank(prs)
    top = title(s, "Inference — permutation, not asymptotics",
                "With one treated unit, a distributional standard error is "
                "not credible. The null is built from the data.")
    _, y = eq(s, MARGIN, top, W - 2 * MARGIN,
              "RMSPE ratio     R_i  =  RMSPE_post(i) / RMSPE_pre(i)\n\n"
              "permutation p   p^  =  ( 1 + #{ j in J : R_j >= R_1 } ) / "
              "( 1 + |J| )",
              size=14, align=PP_ALIGN.LEFT)
    w, gap = Inches(3.86), Inches(0.24)
    x = MARGIN
    for head, body, acc in [
        ("IN-SPACE PLACEBO",
         "Assign the treatment date to each untreated unit in turn and re-run "
         "the full estimator. The resulting effects form a null distribution "
         "under no treatment, with no distributional assumption.", BLUE),
        ("WHY THE RATIO",
         "Units that fit the pre-period badly produce large post-period gaps "
         "for uninteresting reasons. Dividing by pre-period error prevents "
         "poor fit from masquerading as a large effect.", BLUE),
        ("IN-TIME PLACEBO",
         "Re-date the treatment two years earlier. A detected effect there "
         "indicates something other than the treatment is driving the "
         "result.", ORANGE),
    ]:
        card(s, x, y + Inches(0.24), w, Inches(2.15), head, body,
             accent=acc, fill=ORANGE_L if acc == ORANGE else WHITE, bsize=12)
        x += w + gap
    banner(s, Inches(6.05),
           "Pre-treatment fit is necessary and not sufficient. Reporting it "
           "alone was the single clearest methodological gap in the earlier "
           "design.", accent=RED, fill=RED_L, size=13)
    footer(s, FOOT, 11)
    return s


def v12_interference(prs, fig_dir):
    """Estimating the spillover kernel by distance band.
    Embeds fig05_decay."""
    return figure_slide(
        prs, fig_dir, "fig05_decay",
        "Interference — estimating the spillover kernel",
        "Distance-band estimation (Pollmann, arXiv:2011.00373). The "
        "estimator is his; the parameter for same-day delivery is the "
        "contribution.",
        note="ρ̂ is then used twice: to construct W, and to define donor "
             "contamination in the synthetic control.")


def v13_w_construction(prs):
    """Constructing the spatial weight matrix W from the estimated
    kernel, so W carries a standard error rather than an assumption."""
    s = blank(prs)
    top = title(s, "Constructing W from the estimated kernel",
                "W becomes an estimated object with a standard error rather "
                "than a modelling convenience.")
    _, y = eq(s, MARGIN, top, W - 2 * MARGIN,
              "band estimates    tau^(d_k)  for bands  d_1 < d_2 < ... < d_K\n"
              "reach             rho^ = min{ d_k : "
              "H_0( tau(d_k) = 0 ) not rejected }\n\n"
              "weights           w_ij  =  f( dist_ij ; rho^ )  ,  "
              "normalised row-wise\n"
              "                  f decreasing, f(d) = 0 for d > rho^",
              size=13.5, align=PP_ALIGN.LEFT)
    card(s, MARGIN, y + Inches(0.2), Inches(6.0), Inches(2.15),
         "WHAT THIS ANSWERS",
         "The standard objection to a contiguity matrix is 'why contiguity?' "
         "— why not 5 km, why not drive time. There is no principled "
         "answer.\n\n"
         "Deriving W from the measured reach replaces an assumption with an "
         "estimate, and propagates its uncertainty into the spatial term.",
         accent=GREEN, fill=GREEN_L, bsize=12)
    card(s, MARGIN + Inches(6.3), y + Inches(0.2), Inches(6.0), Inches(2.15),
         "WHAT IT DOES NOT CLAIM",
         "Estimating W is not new. Souza (2019), Krisztin and Piribauer, and "
         "Political Analysis (2024) all estimate or select it from the "
         "outcome panel.\n\n"
         "Our difference is the channel: W is revised BETWEEN estimation "
         "cycles from an exogenous text stream, not fitted in-sample once.",
         accent=RED, fill=RED_L, bsize=12)
    footer(s, FOOT, 13)
    return s


def v14_rq2(prs):
    """RQ2: a pre-registered test with two publishable outcomes, so the
    result is informative either way."""
    s = blank(prs)
    top = title(s, "RQ2 — a pre-registered test with two publishable "
                   "outcomes",
                "LeSage and Pace (2014) argue spatial estimates are less "
                "sensitive to W than practitioners assume. This is a direct "
                "test.")
    _, y = eq(s, MARGIN, top, W - 2 * MARGIN,
              "H_0 :   | theta( W_t+1 ) - theta( W_t ) |  <=  kappa\n\n"
              "kappa   pre-registered materiality threshold, fixed before "
              "estimation\n"
              "W_t+1   W revised by a gated agent write at time t",
              size=14, align=PP_ALIGN.LEFT)
    card(s, MARGIN, y + Inches(0.26), Inches(6.0), Inches(2.0),
         "IF H_0 IS REJECTED",
         "Event-driven revision of W materially moves the causal estimate. "
         "That challenges a well-known robustness claim, using an update "
         "channel the literature has not applied.\n\n"
         "→ workshop paper in spatial econometrics.",
         accent=GREEN, fill=GREEN_L, bsize=12.5)
    card(s, MARGIN + Inches(6.3), y + Inches(0.26), Inches(6.0), Inches(2.0),
         "IF H_0 IS NOT REJECTED",
         "The robustness claim survives a novel perturbation — itself a "
         "contribution — and we report an honest engineering finding: the "
         "mutable-W machinery is elegant and not decision-relevant.\n\n"
         "→ negative result, reported.",
         accent=BLUE, fill=BLUE_L, bsize=12.5)
    banner(s, Inches(6.05),
           "κ is fixed in advance precisely so the negative result reads as a "
           "finding rather than a rationalisation.", accent=ORANGE,
           fill=ORANGE_L, size=13)
    footer(s, FOOT, 14)
    return s


def v15_generated(prs):
    """Generated regressors: machine-extracted covariates enter
    downstream estimators measured with error."""
    s = blank(prs)
    top = title(s, "Generated regressors",
                "Machine-extracted covariates enter downstream estimators as "
                "if measured exactly. They are not.")
    _, y = eq(s, MARGIN, top, W - 2 * MARGIN,
              "observed        X^_i  =  X_i + eta_i ,   E[eta] != 0 possible\n"
              "naive           Var( beta^ )  understated;  inference "
              "anti-conservative\n\n"
              "correction      design-based supervised learning on a "
              "hand-labelled subsample\n"
              "                (Egami, Hinck, Stewart & Wei, NeurIPS 2023) ; "
              "PPI (Angelopoulos et al. 2023)",
              size=13, align=PP_ALIGN.LEFT)
    card(s, MARGIN, y + Inches(0.24), Inches(6.0), Inches(2.05),
         "WHY IT MATTERS HERE",
         "Facility attributes parsed from text feed both W and the gravity "
         "term. Treating an estimate as an observation makes the model look "
         "more certain than the evidence supports — precisely the failure "
         "this project exists to avoid elsewhere.",
         accent=BLUE, bsize=12.5)
    card(s, MARGIN + Inches(6.3), y + Inches(0.24), Inches(6.0), Inches(2.05),
         "WHY IT IS CHEAP",
         "The 43-row census built for target-quality "
         "assessment is exactly the labelled set these estimators require. "
         "One artefact, two uses; roughly one day of work.\n\n"
         "Not novel. Correct — and rarely done in the agent literature.",
         accent=GREEN, fill=GREEN_L, bsize=12.5)
    footer(s, FOOT, 15)
    return s


def v16_conformal(prs):
    """Split conformal prediction for distribution-free, finite-sample
    coverage."""
    s = blank(prs)
    top = title(s, "Uncertainty — split conformal prediction",
                "Distribution-free, finite-sample coverage under "
                "exchangeability. A verified guarantee rather than an "
                "assumed one.")
    _, y = eq(s, MARGIN, top, W - 2 * MARGIN,
              "fit on D_train ;  scores  s_i = | y_i - f^(x_i) |  on D_cal\n"
              "q^ = Quantile( s ; ceil((n+1)(1-alpha)) / n )\n"
              "C(x) = [ f^(x) - q^ ,  f^(x) + q^ ]\n\n"
              "guarantee   P( y in C(x) )  >=  1 - alpha    "
              "for any underlying model",
              size=13.5, align=PP_ALIGN.LEFT)
    w, gap = Inches(3.86), Inches(0.24)
    x = MARGIN
    for head, body, acc in [
        ("WHAT IT REPLACES",
         "Model-derived intervals inherit every specification assumption. If "
         "the model is misspecified the interval is wrong and nothing "
         "signals it.", BLUE),
        ("WHAT WE REPORT",
         "Nominal 90% against MEASURED coverage on held-out ZCTAs. Target: "
         "within 2 percentage points. The claim is checkable and can fail.",
         GREEN),
        ("CAVEAT WE STATE",
         "Exchangeability is violated under temporal drift. We report "
         "coverage separately by year, and use the out-of-time split so drift "
         "is visible rather than hidden.", ORANGE),
    ]:
        card(s, x, y + Inches(0.24), w, Inches(2.05), head, body,
             accent=acc,
             fill=GREEN_L if acc == GREEN else (
                 ORANGE_L if acc == ORANGE else WHITE), bsize=12)
        x += w + gap
    footer(s, FOOT, 16)
    return s
