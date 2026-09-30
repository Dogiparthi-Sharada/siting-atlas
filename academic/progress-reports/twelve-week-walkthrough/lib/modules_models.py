"""Weeks 7-9: commit in advance, fit, and report what came back.

Week 7 is what makes week 9 evidence rather than an excuse.
"""

from __future__ import annotations

from modmeta import RECOMPUTE

WEEKS = [
    dict(
        n=7, title="Pre-registration — writing down what would count",
        mode=RECOMPUTE,
        question="Before fitting anything: what result would we accept as "
                 "success, and how do we stop ourselves moving that line "
                 "afterwards?",
        artefacts=["metro_entry"],
        secs=1,
        measured_note="the seal check itself is instant",
        runs="md5sum of the sealed pre-registration, compared against the "
             "hash recorded inside the result artefact",
        status="Specification hashed and sealed before a single model was "
               "fitted. CI re-checks the match on every push.",
        risk="Committing in advance means we might have to publish a "
             "failure. That is the cost, and we accepted it in writing. "
             "The alternative — deciding what counts as success after "
             "seeing the answer — is not a cheaper option, it is a "
             "different and worse study.",
        body="""
The question, the sample, the covariates, the baselines, the evaluation and
a numeric success criterion were all fixed and hashed **before** a single
model was fitted.

The mechanism is deliberately boring, which is why it works. The
pre-registration is a file in the repository. Its md5 is written inside the
result artefact. A CI job re-computes both on every push and fails if they
disagree. Editing the specification after seeing the answer is therefore not
something we promise not to do — it is something that turns the build red.

    md5sum docs/PREREG_METRO_MODEL.md

**This is the single most defensible week of the twelve.** A negative result
from a sealed specification is evidence. The identical result from an
unsealed one is indistinguishable from having tried things until something
looked good. Week 6 told us failure was likely; week 7 is what made that
failure worth reporting.

Corrections discovered later go in a separate errata file. The seal is never
edited — not even to fix a genuine mistake in it — because a seal that can
be improved is not a seal.
""",
        nums=lambda L: [
            ("Pre-registration", L("metro_entry")["prereg"],
             "metro_entry.prereg"),
            ("Sealed md5", L("metro_entry")["prereg_md5"],
             "metro_entry.prereg_md5"),
            ("Question committed to", L("metro_entry")["question"],
             "metro_entry.question"),
            ("Held-out years declared",
             len(L("metro_entry")["held_out_years"]),
             "metro_entry.held_out_years"),
            # The field holds WHEN the arm was declared, not which one.
            ("Arm declared", L("metro_entry")["verdict_arm_declared"],
             "metro_entry.verdict_arm_declared"),
            ("Arm scored", L("metro_entry")["verdict_arm"],
             "metro_entry.verdict_arm"),
            ("Coverage floor", L("metro_entry")["coverage_floor"],
             "metro_entry.coverage_floor"),
        ],
        limits=[
            "A pre-registration constrains the analysis, not the data. It "
            "cannot rescue a panel that lacks the variables that drive the "
            "decision — which is exactly what week 6 suggested.",
            "Three corrections to the sealed text exist and are recorded "
            "in the errata rather than patched into the file.",
        ],
        nxt=[("docs/PREREG_METRO_MODEL.md", "the sealed specification"),
             ("docs/PREREG_METRO_MODEL_ERRATA.md",
              "what was corrected afterwards, and why the seal stands")],
    ),
    dict(
        n=8, title="Model 1 — which ZIP, given that one opening happens",
        mode=RECOMPUTE,
        question="Conditional on a facility opening somewhere in a metro, "
                 "can public data say which ZIP code it lands in?",
        artefacts=["choice_report"],
        secs=165,
        runs="make model — refits the conditional choice model offline",
        status="Fits and converges. McFadden rho-squared around 0.20 — but "
               "on 94 decisions, and we lead with that rather than with "
               "the rho-squared.",
        risk="n = 94. Small enough that textbook standard errors would be "
             "misleading, because openings inside one metro are not "
             "independent draws. Inference is a metro-clustered bootstrap "
             "instead, which is the honest cost of the sample we have.",
        body="""
A conditional logit over the ZIP codes inside a metro. Utility is
`V = ln(beta' a)`, with `beta = exp(theta)` so every weight stays positive,
and households as the numeraire so the remaining coefficients read as
"worth this many households".

The sample size is the thing to look at first, not the fit statistic.
Ninety-odd decisions is what a national panel of openings actually yields
once you condition on the metro. That is a real constraint, not a
presentational one, and it is why inference here is a clustered bootstrap.

Note what this model does and does not claim. It answers **which ZIP, given
an opening**. It says nothing at all about whether an opening happens. That
is the harder question, it is the pre-registered one, and it is week 9.
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
            ("Bootstrap unit",
             L("choice_report")["inference"]["resampling_unit"],
             "choice_report.inference.resampling_unit"),
        ],
        limits=[
            "One operator. Nothing here transfers to another carrier "
            "without refitting, and this panel cannot test whether it "
            "would.",
            "Conditional on an opening. The model is silent on whether one "
            "occurs, which is the question that actually matters "
            "commercially.",
        ],
        nxt=[("docs/MODEL_SPEC.md", "the utility specification in full"),
             ("docs/ALGORITHMS.md",
              "conditional logit, in plain language then precisely")],
    ),
    dict(
        n=9, title="Model 2 — the pre-registered test, and its answer",
        mode=RECOMPUTE,
        question="Which metro gets the next delivery station? Scored "
                 "against the criterion we sealed in week 7.",
        artefacts=["metro_entry"],
        secs=56,
        runs="make metro — reruns the out-of-time test end to end",
        status="It lost to a zero-parameter baseline in every held-out "
               "year. We are reporting that, in the wording week 7 "
               "committed us to.",
        risk="The risk we took in week 7 came due. A model that loses is "
             "uncomfortable to present; a model that loses against a "
             "criterion you wrote down first is a result. The failure "
             "mode to avoid now is quietly adding a specification that "
             "wins — which the seal prevents.",
        body="""
Trained on everything before the held-out year, scored on that year. The
comparison is against a baseline with **no parameters at all**: rank metros
by household count.

The model lost every year. Not narrowly — the clustered bootstrap difference
excludes zero comfortably.

The verdict holds across all nine arm-by-form combinations tried, so it is
not an artefact of one specification. Those nine are not independent tests
and we do not present them as if they were.

What makes this publishable rather than embarrassing is the ordering. The
criterion existed, hashed, before the fit. The paragraph reporting the
failure was written into the pre-registration in advance, and it is quoted
verbatim rather than softened:

> *Free public data cannot predict siting at any grain tested. The
> ZIP-level failure is not a resolution problem but a general one: the
> variables that drive the decision are not public at any resolution.*

Losing to a households baseline is not the same as being uninformative. It
means the model adds nothing **over a number anyone can look up** — which,
given week 6, is close to what we should have expected.
""",
        nums=lambda L: [
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
             "...clustered_bootstrap.auc_minus_baseline2_households"),
            ("Bootstrap clusters",
             L("metro_entry")["clustered_bootstrap"]["n_clusters"],
             "metro_entry.clustered_bootstrap.n_clusters"),
            ("Seal still intact", L("metro_entry")["prereg_md5"],
             "metro_entry.prereg_md5"),
            ("Verdict", L("metro_entry")["verdict"]["hypothesis"],
             "metro_entry.verdict.hypothesis"),
        ],
        limits=[
            "Nine arm-by-form combinations all return the same verdict, "
            "which is reassuring but not nine independent tests.",
            "This is a statement about FREE PUBLIC DATA, not about "
            "predictability in principle. An operator with its own "
            "pipeline data is answering a different question.",
        ],
        nxt=[("docs/PREREG_METRO_MODEL.md",
              "the criterion this was scored against"),
             ("docs/NUMBERS.md", "every figure above, re-derived")],
    ),
]
