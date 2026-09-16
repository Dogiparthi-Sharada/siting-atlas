"""V2 research deck, slides 17-30: evaluation, decision layer, agent, threats."""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scope import SCOPE
from hazard_metrics import HAZARD

from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from pptx_kit import (BLUE, BLUE_L, GREEN, GREEN_L, INK, INK_2, LINE, MARGIN,
                      MUTED, ORANGE, ORANGE_L, PLANE, RED, RED_L, W, WHITE,
                      banner, blank, bullets, card, eq, figure_slide, footer,
                      picture, stat, table, text, title)

FOOT = "Siting Atlas  ·  technical supplement"


def v17_protocol(prs):
    """The evaluation protocol: out-of-time and out-of-metro, with
    targets fixed before estimation."""
    s = blank(prs)
    top = title(s, "Evaluation protocol",
                "Targets fixed before estimation. They were missed, and the "
                "next slide reports the miss rather than retraining it away.")
    rows = [
        ["Metric", "Target", "Rationale"],
        ["AUC-ROC, out-of-time", "≥ 0.80",
         "Rank quality on a forecast that was scored. Above ~0.95 would "
         "suggest leakage on public covariates"],
        ["PR-AUC (base rate ≈ 0.06)", "≫ base rate",
         "Positive class is rare; ROC is flattered by abundant true "
         "negatives"],
        ["Brier score", "≤ 0.06", "Proper scoring rule; calibration and "
         "sharpness jointly"],
        ["Expected calibration error", "< 0.05",
         "Councils act on the stated probability, so it must mean what it "
         "says"],
        ["precision@100", "≥ 0.60", "Matches the decision: a shortlist, not "
         "a full ranking"],
        ["Conformal coverage", "within 2pp of nominal",
         "Empirically verified, not assumed"],
        ["Spearman vs LightGBM, top decile", "≥ 0.80, bootstrap CI",
         "Convergent validity across parametric and non-parametric forms"],
        ["AUC under 15% label noise", "≥ 0.78",
         "Bounds the effect of target measurement error"],
        ["Top-100 overlap, H3 vs ZCTA", "≥ 0.70",
         "Ranking is not an artefact of the spatial partition"],
    ]
    table(s, MARGIN, top, W - 2 * MARGIN, rows,
          col_w=[Inches(3.5), Inches(2.3), Inches(6.3)], size=11,
          row_h=Inches(0.42))
    footer(s, FOOT, 17)
    return s


def v18_backtest(prs, fig_dir):
    """The measured result against the targets. Embeds fig08_backtest."""
    return figure_slide(
        prs, fig_dir, "fig08_backtest",
        "Measured, against every target on the previous slide",
        f"Primary hold-out splits whole units; the secondary split is "
        f"temporal. AUC {HAZARD.auc:.4f} and {HAZARD.t_auc:.4f} against "
        f"{HAZARD.null_auc:.4f}. Brier {HAZARD.brier:.6f} against "
        f"{HAZARD.null_brier:.6f} for a constant.",
        note="The raw Brier pair, not a skill score: Gneiting and Raftery "
             "(2007) section 2.3 p.362, skill scores are generally improper even "
             "when the underlying rule is proper. The geographic hold-out is "
             "not on this slide because Phoenix and Boise hold two dated "
             "stations between them, which is a smoke test, not a transfer "
             "test.")


def v19_robustness(prs):
    """The robustness programme, each check aimed at a specific way the
    headline result could be an artefact."""
    s = blank(prs)
    top = title(s, "Robustness programme",
                "Each check targets a specific way the headline result could "
                "be an artefact.")
    rows = [
        ["Threat", "Check", "Failure would mean"],
        ["Target measurement error",
         "Corrupt a known fraction of open dates by ±1 quarter; re-run the "
         "backtest across the grid",
         "Reported AUC is not interpretable without a stated error rate"],
        ["Spatial partition artefact (MAUP)",
         "Re-run at H3 hexagonal grain; compare top-100 overlap",
         "The ranking reflects ZIP boundaries, not geography"],
        ["Functional form",
         "LightGBM benchmark; Spearman on top decile with bootstrap CI",
         "The result is an artefact of the cloglog specification"],
        ["Selection",
         "Corrected vs naive coefficients; sensitivity path over an assumed "
         "direct instrument effect",
         "The estimate confounds viability with revealed preference"],
        ["Spillover mis-specification",
         "Vary ρ̂ across its confidence band; re-estimate θ at each",
         "θ is an artefact of the assumed neighbourhood"],
        ["Covariate noise",
         "Propagate ACS margins of error through the Monte Carlo",
         "Rankings are spuriously precise"],
        ["Margin heterogeneity",
         "Re-rank under a margin varying with income; measure top-100 churn",
         "Scale-invariance of the ranking does not hold"],
    ]
    table(s, MARGIN, top, W - 2 * MARGIN, rows,
          col_w=[Inches(2.7), Inches(4.6), Inches(4.8)], size=11,
          row_h=Inches(0.42))
    footer(s, FOOT, 19)
    return s


def v20_cost(prs):
    """The Daganzo continuous-approximation cost model and the BHH
    result it rests on."""
    s = blank(prs)
    top = title(s, "Cost model — continuous approximation",
                "Beardwood–Halton–Hammersley (1959); Daganzo (1984). The "
                "distance term is precomputed, not served.")
    _, y = eq(s, MARGIN, top, W - 2 * MARGIN,
              "BHH        tour length  ~  k * sqrt( N * A )\n"
              "per stop   ~ k * sqrt( A / N )  =  k / sqrt( delta )\n\n"
              "c_i  =  c_fixed  +  b_stem * d_stem(i)  +  "
              "b_local * A_i / sqrt( delta_i * N_i )",
              size=13.5, align=PP_ALIGN.LEFT)
    card(s, MARGIN, y + Inches(0.22), Inches(6.0), Inches(2.1),
         "THE ENGINEERING CONSEQUENCE",
         "d_stem is a finite precomputable set — ~800,000 within-metro OD "
         "pairs, 10 MB as parquet.\n\n"
         "Routing is therefore an offline, one-time job. Process one metro, "
         "extract the matrix, delete every artifact. Peak disk 8 GB rather "
         "than 60; the deployed system carries no routing dependency.",
         accent=GREEN, fill=GREEN_L, bsize=12)
    card(s, MARGIN + Inches(6.3), y + Inches(0.22), Inches(6.0), Inches(2.1),
         "AND THE FALLBACK",
         "Daganzo is already a continuous approximation, so exact routing is "
         "precision in the wrong place.\n\n"
         "Circuity: road ≈ great-circle × k, k ≈ 1.35, calibrated on one "
         "metro against routed truth with the residual reported. A large "
         "residual is a finding; a small one saves two weeks.",
         accent=BLUE, bsize=12)
    footer(s, FOOT, 20)
    return s


def v21_npv(prs):
    """NPV kept linear in the unobservable contribution margin, so the
    output is a break-even margin rather than a guessed dollar figure."""
    s = blank(prs)
    top = title(s, "NPV under an unobservable margin",
                "Contribution margin is not identified from public data. We "
                "factor it out rather than invent it.")
    _, y = eq(s, MARGIN, top, W - 2 * MARGIN,
              "NPV_i  =  SUM_{t=1..5}  [ (1 - theta_i) N_it m  -  c_it N_it ] "
              "/ (1+r)^t   -   K_i\n\n"
              "reported as        NPV_i  =  a_i * m  -  b_i\n"
              "break-even         m*_i   =  b_i / a_i",
              size=13.5, align=PP_ALIGN.LEFT)
    card(s, MARGIN, y + Inches(0.22), Inches(6.0), Inches(2.2),
         "WHAT SURVIVES WITHOUT m",
         "Ranking is invariant to a common positive scale factor, so the "
         "ranked list, bundle selection, rank stability, break-even "
         "thresholds, timing and the selection propensity are all "
         "unaffected.\n\n"
         "Six of eight outputs need no margin at all.",
         accent=GREEN, fill=GREEN_L, bsize=12)
    card(s, MARGIN + Inches(6.3), y + Inches(0.22), Inches(6.0), Inches(2.2),
         "WHAT DOES NOT, AND THE TEST",
         "If m varies systematically across areas, scale-invariance fails and "
         "the RANKING moves, not just the level.\n\n"
         "We re-rank under m varying with median income as a plausible worst "
         "case and report top-100 churn. K_i is validated externally against "
         "disclosed capital expenditure, target within 25%.",
         accent=RED, fill=RED_L, bsize=12)
    footer(s, FOOT, 21)
    return s


def v22_portfolio(prs):
    """The decision layer: set selection, not ranking, and why no
    greedy guarantee applies."""
    s = blank(prs)
    top = title(s, "Decision layer — set selection, not ranking",
                "The objective is neither submodular nor supermodular, so no "
                "greedy guarantee applies.")
    _, y = eq(s, MARGIN, top, W - 2 * MARGIN,
              "maximise   V(S)  =  SUM_{i in S} v_i  "
              "-  SUM_{i,j in S} theta_ij  +  g( delta(S) )\n"
              "                                  cannibalisation      "
              "shared-density gain\n\n"
              "theta_ij  induces DIMINISHING returns  ->  submodular\n"
              "g(delta)  induces INCREASING  returns  ->  supermodular\n"
              "V is neither  ->  the (1 - 1/e) greedy bound does not apply",
              size=12.5, align=PP_ALIGN.LEFT)
    w, gap = Inches(3.86), Inches(0.24)
    x = MARGIN
    for head, body, acc in [
        ("SEARCH SPACE",
         f"ranking   → {SCOPE.zctas_label} independent decisions\n"
         f"bundling  → {SCOPE.search_space} candidate sets\n"
         "top 200   → ≈ 1.6 × 10^60", BLUE),
        ("WHAT WE ACTUALLY SOLVE",
         "Greedy construction plus pairwise-swap local search over the top "
         "candidate set. We report the optimality gap against pure greedy "
         "ranking, not a claim of optimality.", BLUE),
        ("NOT A CONTRIBUTION",
         "Multi-facility location optimisation is textbook OR (p-median, "
         "maximal covering) and a mature commercial category. We include it "
         "because ranking is the wrong model of the decision.",
         ORANGE),
    ]:
        card(s, x, y + Inches(0.2), w, Inches(2.0), head, body, accent=acc,
             fill=ORANGE_L if acc == ORANGE else WHITE, bsize=11.5)
        x += w + gap
    footer(s, FOOT, 22)
    return s


def v23_agent_formal(prs):
    """Inferential integrity defined formally — the failure class the
    gated-write literature does not cover."""
    s = blank(prs)
    top = title(s, "Inferential integrity — a definition",
                "The failure class the gated-write literature does not "
                "cover.")
    _, y = eq(s, MARGIN, top, W - 2 * MARGIN,
              "Let  M  be a proposed mutation to warehouse state  s.\n\n"
              "DATA INTEGRITY          G_data(M) = 1   iff  schema, "
              "geocoding, confidence, audit all hold\n"
              "INFERENTIAL INTEGRITY   G_inf(M)  = 1   iff  the "
              "identification assumptions of\n"
              "                                          the estimator on "
              "s + M still hold\n\n"
              "CLAIM   there exist M with  G_data(M) = 1  and  G_inf(M) = 0 ,"
              "  and no published gate detects them",
              size=12.5, align=PP_ALIGN.LEFT)
    card(s, MARGIN, y + Inches(0.2), Inches(6.0), Inches(2.1),
         "GATE 5 — DONOR-POOL INTEGRITY",
         "Reject or escalate if M moves any j ∈ J into treatment or within "
         "ρ̂ of a treated unit.\n\n"
         "Formally: J(s + M) ≠ J(s) ⇒ recompute and flag. Never silently "
         "re-weight — a silent re-weight keeps producing a plausible "
         "number.", accent=ORANGE, fill=ORANGE_L, bsize=12)
    card(s, MARGIN + Inches(6.3), y + Inches(0.2), Inches(6.0), Inches(2.1),
         "GATE 6 — ESTIMATE STABILITY",
         "Re-estimate θ on s and on s + M. Escalate to human review if\n\n"
         "        | θ(s + M) − θ(s) |  >  κ\n\n"
         "κ is pre-registered. Fixing it after seeing results would make the "
         "gate a rationalisation rather than a control.",
         accent=ORANGE, fill=ORANGE_L, bsize=12)
    footer(s, FOOT, 23)
    return s


def v24_gates_fig(prs, fig_dir):
    """The six-gate mutation path. Embeds fig03_agent_gates."""
    return figure_slide(
        prs, fig_dir, "fig03_agent_gates",
        "The six-gate mutation path",
        "Gates 1–4 protect data integrity and have prior art. Gates 5–6 "
        "protect identification and are the contribution.",
        note="Evaluated on a seeded adversarial set of 50 perturbations; "
             "target ≥ 90% detection of mutations that move θ beyond κ.")


def v25_agent_eval(prs):
    """Agent evaluation calibrated against the field, because a
    self-authored benchmark is unfalsifiable."""
    s = blank(prs)
    top = title(s, "Agent evaluation, calibrated against the field",
                "A self-authored benchmark is unfalsifiable unless it is "
                "positioned against a public one.")
    w, gap = Inches(3.86), Inches(0.24)
    x = MARGIN
    for v, lab, acc, fill in [
        ("~80%", "best public systems, BIRD execution accuracy\n"
                 "(Li et al., NeurIPS 2023)", BLUE, PLANE),
        ("~93%", "human baseline on the same benchmark", BLUE, PLANE),
        ("75%", "our target, at n ≥ 100, reported per tier", GREEN, GREEN_L),
    ]:
        stat(s, x, top, w, Inches(1.82), v, lab, accent=acc, fill=fill)
        x += w + gap
    card(s, MARGIN, top + Inches(2.1), Inches(6.0), Inches(2.1),
         "SAMPLE SIZE IS NOT A DETAIL",
         "At n = 40 an observed 0.85 carries a 95% Wilson interval of roughly "
         "[0.71, 0.93]. A 'pass' at 0.85 and a 'fail' at 0.72 are not "
         "distinguishable.\n\n"
         "n ≥ 100, intervals reported, stratified into four difficulty tiers "
         "— spatial joins are where these systems fail and our warehouse "
         "is spatial.", accent=RED, fill=RED_L, bsize=12)
    card(s, MARGIN + Inches(6.3), top + Inches(2.1), Inches(6.0), Inches(2.1),
         "AND FOR THE MODEL COMPARISON WE DEFERRED",
         "At n = 200 with a hit rate near 0.8, SE ≈ 2.8pp, so differences "
         "below ~8pp are not detectable.\n\n"
         "Stating the minimum detectable effect in advance is what stops an "
         "82 / 84 / 85 result being reported as a ranking.",
         accent=ORANGE, fill=ORANGE_L, bsize=12)
    footer(s, FOOT, 25)
    return s


def v26_threats(prs):
    """Threats to validity — internal, external, construct, statistical
    — each with its response."""
    s = blank(prs)
    top = title(s, "Threats to validity",
                "Internal, external, construct and statistical — with the "
                "response to each.")
    rows = [
        ["Type", "Threat", "Response"],
        ["Internal", "Endogenous treatment assignment",
         "Heckman on the pilot metro; explicit disclosure elsewhere; "
         "sensitivity over the exclusion restriction"],
        ["Internal", "Interference contaminating controls",
         "Donor exclusion by estimated ρ̂ rather than contiguity; staggered "
         "adoption"],
        ["Construct", "Enablement ≠ viability",
         "Framed throughout as operator-consistent desirability; equity audit "
         "by demographic stratum"],
        ["Construct", "Proxies for land cost and retail attraction",
         "External capex validation of the composite; per-proxy sensitivity"],
        ["Statistical", "One treated unit per SCM estimate",
         "Permutation inference rather than asymptotic standard errors"],
        ["Statistical", "Generated regressors understate variance",
         "Design-based supervised learning on the labelled subsample"],
        ["External", "Ten metros, one operator, one country",
         "Cross-operator transfer test; national propensity fit; explicit "
         "scope statement"],
        ["External", "Regime change in the network architecture",
         "Out-of-time design surfaces drift; coverage reported by year"],
    ]
    table(s, MARGIN, top, W - 2 * MARGIN, rows,
          col_w=[Inches(1.35), Inches(4.15), Inches(6.6)], size=11,
          row_h=Inches(0.4))
    footer(s, FOOT, 26)
    return s


def v27_not_identified(prs):
    """What the design cannot identify, stated plainly."""
    s = blank(prs)
    top = title(s, "What we cannot identify",
                "Stated plainly, because it is the reason to believe "
                "everything else.")
    y = top
    for head, body in [
        ("Order volume, revenue and margin",
         "Not observable in public data and not recoverable by any "
         "transformation. No accuracy claim is made on dollar figures; "
         "results are reported as a multiple of margin with break-even "
         "thresholds, and the capital side is validated externally."),
        ("The true cannibalization coefficient",
         "Estimated with placebo inference and confidence bands, but no "
         "public number exists to check it against. We claim identification "
         "under assumptions, not correctness — and it feeds NPV directly."),
        ("Internal constraints on the operator",
         "Lease obligations, capital rationing, portfolio strategy and "
         "outright mistakes are unobservable. Hence operator-consistent "
         "desirability rather than viability."),
        ("Whether the public-data ceiling is high enough",
         "This is RQ4, not an aside. If public data explains too little for "
         "the decision, that is the finding and we publish it."),
    ]:
        card(s, MARGIN, y, W - 2 * MARGIN, Inches(1.28), head, body,
             accent=RED, fill=RED_L, hsize=13, bsize=11.5)
        y += Inches(1.38)
    footer(s, FOOT, 27)
    return s


def v28_extensions(prs):
    """Named extensions, out of scope for this build."""
    s = blank(prs)
    top = title(s, "Named extensions",
                "Out of scope for this build, and named as directions rather "
                "than commitments.")
    rows = [
        ["Direction", "What it would add", "Why not now"],
        ["Causal forests (Wager & Athey 2018); DoubleML "
         "(Chernozhukov et al. 2018)",
         "Heterogeneous treatment effects at ZCTA grain; extends the "
         "selection correction beyond one metro",
         "Engineering cost of ten formal corrections exceeds the window"],
        ["Graph neural network over the ZCTA adjacency graph "
         "(Kipf & Welling 2017)",
         "Cross-metro transfer without a parametric form; a natural "
         "comparison against the hazard model",
         "Adds a benchmark, not an identification argument"],
        ["Bayesian synthetic control with spillovers "
         "(arXiv:2408.00291)",
         "Full posterior over θ and over the donor weights",
         "Permutation inference already gives assumption-light inference"],
        ["Volume II — data-centre siting",
         "Same machinery, hotter subject: opaque siting, large capital, "
         "abatements, an active civic ecosystem",
         "A data swap below the feature layer; post-capstone"],
        ["Public forecast registry with periodic scoring",
         "Timestamped predictions scored later by anyone",
         "Cheap; scheduled for the release phase"],
    ]
    table(s, MARGIN, top, W - 2 * MARGIN, rows,
          col_w=[Inches(3.6), Inches(4.5), Inches(4.0)], size=11,
          row_h=Inches(0.42))
    footer(s, FOOT, 28)
    return s


def v29_repro(prs):
    """Reproducibility: the artefacts released and the claim they
    support."""
    s = blank(prs)
    top = title(s, "Reproducibility",
                "The claim is that a stranger can rebuild every number. That "
                "has to be literally true.")
    w, gap = Inches(3.86), Inches(0.24)
    x = MARGIN
    for head, body, acc in [
        ("DETERMINISM",
         "Every stochastic step reads its seed from reproducibility/"
         "seeds.toml. Nothing hardcodes one, so changing a seed is a "
         "reviewable act.", BLUE),
        ("PROVENANCE",
         "Content-addressed acquisition cache plus a manifest recording "
         "source, URL, SHA-256, timestamp and size for every fetch. A "
         "reviewer can re-download and verify hashes.", BLUE),
        ("SCENARIO REPLAY",
         "dim_scenario records which W version, which agent mutation and "
         "which seed produced each published figure. A system whose "
         "parameters change in response to text is otherwise not auditable.",
         ORANGE),
    ]:
        card(s, x, top, w, Inches(2.15), head, body, accent=acc,
             fill=ORANGE_L if acc == ORANGE else WHITE, bsize=12)
        x += w + gap
    card(s, MARGIN, top + Inches(2.35), W - 2 * MARGIN, Inches(1.7),
         "ARTIFACTS RELEASED",
         "· the ZCTA-quarter facility-opening panel, with a data card and the "
         "measured date-error rate\n"
         "· the estimation harness and the evaluation protocol\n"
         "· the deployed application, operator view and public planning view\n"
         "· a timestamped forecast registry so predictions can be scored by "
         "third parties\n"
         "· model card stating intended use, out-of-scope use and known "
         "biases", accent=GREEN, fill=GREEN_L, bsize=12)
    footer(s, FOOT, 29)
    return s


def v30_close(prs):
    """Closing summary of what is and is not claimed."""
    s = blank(prs)
    top = title(s, "Summary")
    card(s, MARGIN, top, Inches(6.0), Inches(2.9),
         "WHAT WE CLAIM",
         "C1  Inferential integrity as a distinct failure mode for "
         "state-mutating agents, with two gates that detect it\n\n"
         "C2  A distance-decay parameter for same-day cannibalization, used "
         "to construct W endogenously\n\n"
         "C3  The public-data explainability ceiling, and cross-operator "
         "transfer\n\n"
         "C4  An open, re-runnable artifact",
         accent=GREEN, fill=GREEN_L, bsize=12.5)
    card(s, MARGIN + Inches(6.3), top, Inches(6.0), Inches(2.9),
         "WHAT WE DO NOT",
         "· novelty in gating agent writes\n"
         "· novelty in relaxing fixed-W\n"
         "· any latency comparison against a governance process\n"
         "· novelty in multi-facility optimisation\n"
         "· any accuracy claim on dollar NPV\n"
         "· that the exclusion restriction holds\n"
         "· that θ is correct rather than identified under assumptions",
         accent=RED, fill=RED_L, bsize=12.5)
    banner(s, Inches(4.85),
           "Every technique here has a paywalled commercial equivalent. What "
           "does not exist is a version anyone can check.",
           accent=BLUE, fill=BLUE_L, size=15)
    text(s, MARGIN, Inches(6.0), Inches(12.1), Inches(0.6),
         "Questions.", size=18, bold=True, color=INK, align=PP_ALIGN.CENTER)
    footer(s, FOOT, 30)
    return s
