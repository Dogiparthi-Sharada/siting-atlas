"""Weeks 6-8: the two models, and the diagnosis of why one failed.

See ``spec.py`` for the conventions these entries obey.
"""

from __future__ import annotations

from modmeta import INSPECT, RECOMPUTE

WEEKS = [
    dict(
        n=6, title="Which ZIP, given that one opening happens", mode=RECOMPUTE,
        question="Conditional on a facility opening somewhere in a metro, "
                 "can public data say which ZIP code it lands in?",
        artefacts=["choice_report"],
        secs=151,
        runs="make model — refits the conditional choice model",
        body="""
A conditional logit over the ZIP codes inside a metro. Utility is
`V = ln(beta' a)`, with `beta = exp(theta)` so every weight stays positive,
and households as the numeraire so the remaining coefficients read as
"worth this many households".

Note the sample size. Ninety-odd decisions is what a national panel of
openings actually yields once you condition on the metro — and the honest
consequence is that inference is by a metro-clustered bootstrap, not by the
textbook standard errors, because openings inside one metro are not
independent draws.
""",
        nums=lambda L: [
            ("Frame", L("choice_report")["frame"], "choice_report.frame"),
            ("Decisions", L("choice_report")["n_decisions_total"],
             "choice_report.n_decisions_total"),
            ("Train / test",
             f"{L('choice_report')['n_train_decisions']} / "
             f"{L('choice_report')['n_test_decisions']}",
             "choice_report.n_train_decisions, n_test_decisions"),
            ("Parameters", L("choice_report")["fit"]["n_parameters"],
             "choice_report.fit.n_parameters"),
            ("McFadden rho-squared",
             round(L("choice_report")["fit"]["mcfadden_rho_squared"], 4),
             "choice_report.fit.mcfadden_rho_squared"),
            ("Converged", L("choice_report")["fit"]["converged"],
             "choice_report.fit.converged"),
        ],
        limits=[
            "One operator. Nothing here transfers to another carrier "
            "without refitting, and the panel cannot test whether it would.",
            "The model answers WHICH ZIP GIVEN AN OPENING. It says nothing "
            "about whether an opening happens — that is week 7, and it is "
            "the harder question.",
        ],
        nxt=[("docs/MODEL_SPEC.md", "the utility specification in full"),
             ("docs/ALGORITHMS.md", "conditional logit, in plain language "
              "then precisely")],
    ),
    dict(
        n=7, title="A pre-registered test that was allowed to fail",
        mode=RECOMPUTE,
        question="Which metro gets the next delivery station? And — "
                 "committed in writing beforehand — what would count as "
                 "getting that right?",
        artefacts=["metro_entry"],
        secs=50,
        runs="make metro — reruns the pre-registered out-of-time test",
        body="""
The question, sample, covariates, baselines, evaluation and a numeric
success criterion were fixed and hashed BEFORE a single model was fitted.
The pre-registration sits in the repository, its md5 is recorded inside the
result artefact, and CI re-checks the match on every push — so the
specification cannot be edited after seeing the answer without the check
going red.

    md5sum docs/PREREG_METRO_MODEL.md

The model lost to a zero-parameter rule that ranks metros by household
count, in every held-out year. That is the headline, and it is reported in
the wording the pre-registration committed to publishing if the model
failed.

**This is the most valuable week of the twelve to defend.** A negative
result from a sealed specification is evidence; the same result from an
unsealed one is indistinguishable from having tried until something worked.
""",
        nums=lambda L: [
            ("Pre-registration md5", L("metro_entry")["prereg_md5"],
             "metro_entry.prereg_md5"),
            ("Held-out years", len(L("metro_entry")["held_out_years"]),
             "metro_entry.held_out_years"),
            ("Years the model won",
             f"{L('metro_entry')['verdict']['clause1']['wins']} of "
             f"{L('metro_entry')['verdict']['clause1']['of']}",
             "metro_entry.verdict.clause1"),
            ("Pooled AUC, model",
             L("metro_entry")["pooled_out_of_time"]["model"]["auc"],
             "metro_entry.pooled_out_of_time.model.auc"),
            ("Pooled AUC, households baseline",
             L("metro_entry")["pooled_out_of_time"][
                 "baseline2_households"]["auc"],
             "...pooled_out_of_time.baseline2_households.auc"),
            ("Clustered bootstrap difference",
             "{mean:+.4f} [{lo:.4f}, {hi:.4f}]".format(
                 mean=L("metro_entry")["clustered_bootstrap"][
                     "auc_minus_baseline2_households"]["model"]["mean"],
                 lo=L("metro_entry")["clustered_bootstrap"][
                     "auc_minus_baseline2_households"]["model"]["ci2.5"],
                 hi=L("metro_entry")["clustered_bootstrap"][
                     "auc_minus_baseline2_households"]["model"]["ci97.5"]),
             "...clustered_bootstrap.auc_minus_baseline2_households.model"),
            ("Verdict", L("metro_entry")["verdict"]["hypothesis"],
             "metro_entry.verdict.hypothesis"),
        ],
        limits=[
            "The verdict holds across all nine arm-by-form combinations "
            "tried, so it is not an artefact of one specification — but "
            "those nine are not independent tests.",
            "Losing to a households baseline is not the same as the model "
            "being uninformative. It means it adds nothing OVER a variable "
            "anyone can look up.",
            "Three corrections to the sealed text are in "
            "`docs/PREREG_METRO_MODEL_ERRATA.md`. The seal is never edited; "
            "corrections go in the errata.",
        ],
        nxt=[("docs/PREREG_METRO_MODEL.md", "the sealed specification"),
             ("docs/PREREG_METRO_MODEL_ERRATA.md",
              "what was corrected afterwards, and why the seal stands")],
    ),
    dict(
        n=8, title="Why it failed — a screening rule you can run first",
        mode=INSPECT,
        question="Was the failure about this model, or about what free "
                 "public data can carry? And can you tell in advance?",
        artefacts=["covariate_search"],
        extra_json={"gravity":
                    "experiments/gravity-network/artefacts/"
                    "gravity_network.json"},
        why_inspect=(
            "a live covariate refit is about ninety minutes on two workers"),
        runs="reads the covariate search and the gravity-network arms "
             "(a live refit is ~90 minutes)",
        body="""
A conditional choice model can only use a covariate that varies INSIDE a
metro. Most free US public data is published at county grain, so across two
hundred candidate ZIP codes it arrives as a handful of distinct values. A
near-constant cannot rank anything, however large its real-world effect.

That gives a test you can run BEFORE fitting: measure each covariate's
within-metro coefficient of variation.

The rule runs **one way**. Low dispersion is sufficient for failure; high
dispersion is necessary but not sufficient. Stating it as a two-sided rule
would be the overclaim, and the empty middle band is what makes the
one-sided version worth anything.
""",
        nums=lambda L: [
            ("Facilities in the search", L("covariate_search")["facilities"],
             "covariate_search.facilities"),
            ("Repeats", L("covariate_search")["repeats"],
             "covariate_search.repeats"),
            ("Terms screened",
             len(L("gravity")["terms"]["dispersion"]["mean_within_metro_cv"]),
             "gravity_network.terms.dispersion.mean_within_metro_cv"),
            ("Below cv 0.6 — all fail",
             sum(1 for v in L("gravity")["terms"]["dispersion"][
                 "mean_within_metro_cv"].values() if v < 0.6),
             "derived from the same field"),
            ("In the band cv 0.6 to 1.3",
             sum(1 for v in L("gravity")["terms"]["dispersion"][
                 "mean_within_metro_cv"].values() if 0.6 <= v <= 1.3),
             "derived from the same field"),
        ],
        limits=[
            "Descriptive. 21 non-independent terms from one run — this is a "
            "rule of thumb worth checking on your own data, not an "
            "estimated threshold with a confidence interval.",
            "The empty band is an observation about THESE covariates. It is "
            "not a claim that no covariate can sit at cv 1.0.",
        ],
        nxt=[("docs/EXPERIMENTS.md", "all 21 experiments and what each does "
              "NOT support"),
             ("experiments/gravity-network/", "the arms behind the rule")],
    ),
]
