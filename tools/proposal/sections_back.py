"""Sections 6-9: References, Roles, Timeline, Budget."""

from __future__ import annotations

from docx_kit import (BLUE, CRITICAL, GOOD, INK, INK_2, MUTED, ORANGE,
                      bullets, callout, figure, page_break, para, rich, table)

REFERENCES = [
    "Abadie, A., Diamond, A., & Hainmueller, J. (2010). Synthetic control "
    "methods for comparative case studies. Journal of the American "
    "Statistical Association, 105(490), 493–505.",
    "Abadie, A., & Gardeazabal, J. (2003). The economic costs of conflict. "
    "American Economic Review, 93(1), 113–132.",
    "Amazon.com Inc. (2024). Annual Report (Form 10-K). SEC.",
    "Angelopoulos, A. N., & Bates, S. (2021). A gentle introduction to "
    "conformal prediction and distribution-free uncertainty quantification. "
    "arXiv:2107.07511.",
    "Anselin, L. (1988). Spatial Econometrics: Methods and Models. Kluwer.",
    "Ansari, S., Başdere, M., Li, X., Ouyang, Y., & Smilowitz, K. (2018). "
    "Advancements in continuous approximation models for logistics. "
    "Transportation Research Part B, 107, 229–252.",
    "Anthropic. (2024). Model Context Protocol Specification.",
    "Beardwood, J., Halton, J. H., & Hammersley, J. M. (1959). The shortest "
    "path through many points. Mathematical Proceedings of the Cambridge "
    "Philosophical Society, 55(4), 299–327.",
    "Cameron, A. C., & Trivedi, P. K. (2013). Regression Analysis of Count "
    "Data (2nd ed.). Cambridge University Press.",
    "Caoui, E. H., Hollenbeck, B., & Osborne, M. Dynamic entry and spatial "
    "competition: an application to dollar store expansion. Working paper.",
    "Chen, T., & Guestrin, C. (2016). XGBoost: A scalable tree boosting "
    "system. Proceedings of KDD, 785–794.",
    "Daganzo, C. F. (1984). The distance travelled to visit N points with a "
    "maximum of C stops per vehicle. Transportation Science, 18(4), 331–350.",
    "Egami, N., Hinck, M., Stewart, B. M., & Wei, H. (2023). Using imperfect "
    "surrogates for downstream inference. NeurIPS 2023. arXiv:2306.04746.",
    "Heckman, J. J. (1979). Sample selection bias as a specification error. "
    "Econometrica, 47(1), 153–161.",
    "Houde, J.-F., Newberry, P., & Seim, K. (2023). Nexus tax laws and "
    "economies of density in e-commerce: a study of Amazon's fulfillment "
    "center network. Econometrica.",
    "Huff, D. L. (1964). Defining and estimating a trading area. Journal of "
    "Marketing, 28(3), 34–38.",
    "Hyndman, R. J., & Koehler, A. B. (2006). Another look at measures of "
    "forecast accuracy. International Journal of Forecasting, 22(4), 679–688.",
    "Ke, G., Meng, Q., Finley, T., et al. (2017). LightGBM: a highly "
    "efficient gradient boosting decision tree. NeurIPS 2017.",
    "Krisztin, T., & Piribauer, P. A Bayesian approach for estimation of "
    "weight matrices in spatial autoregressive models. arXiv:2101.11938.",
    "Lambert, D. (1992). Zero-inflated Poisson regression. Technometrics, "
    "34(1), 1–14.",
    "LeSage, J. P., & Pace, R. K. (2009). Introduction to Spatial "
    "Econometrics. Chapman and Hall/CRC.",
    "LeSage, J. P., & Pace, R. K. (2014). The biggest myth in spatial "
    "econometrics. Econometrics, 2(4), 217–249.",
    "Lewis, P., Perez, E., Piktus, A., et al. (2020). Retrieval-augmented "
    "generation for knowledge-intensive NLP tasks. NeurIPS 33, 9459–9474.",
    "Li, J., Hui, B., Qu, G., et al. (2023). Can LLM already serve as a "
    "database interface? (BIRD). NeurIPS 2023. arXiv:2305.03111.",
    "Lundberg, S. M., & Lee, S.-I. (2017). A unified approach to interpreting "
    "model predictions. NeurIPS 2017.",
    "Luxen, D., & Vetter, C. (2011). Real-time routing with OpenStreetMap "
    "data. Proceedings of ACM SIGSPATIAL, 513–516.",
    "Openshaw, S. (1984). The Modifiable Areal Unit Problem. CATMOG 38.",
    "Pagan, A. (1984). Econometric issues in the analysis of regressions with "
    "generated regressors. International Economic Review, 25(1), 221–247.",
    "Pollmann, M. Causal inference for spatial treatments. arXiv:2011.00373.",
    "Reich, B. J., et al. A review of spatial causal inference methods. "
    "International Statistical Review. arXiv:2007.02714.",
    "Reilly, W. J. (1931). The Law of Retail Gravitation.",
    "Schorung, M., Lecourt, T., & Dablanc, L. (2023). Assessing the spatial "
    "patterns of Amazon warehouse network in the United States. WCTR.",
    "Souza, P. C. L. (2019). Estimation and selection of the spatial weight "
    "matrix in a spatial lag model. Working paper.",
    "South Coast Air Quality Management District. (2021). Rule 2305 — "
    "Warehouse Indirect Source Rule (WAIRE Program).",
    "US Environmental Protection Agency. EJScreen: Environmental Justice "
    "Screening and Mapping Tool.",
    "Yao, S., Zhao, J., Yu, D., et al. (2023). ReAct: synergizing reasoning "
    "and acting in language models. ICLR 2023.",
]


def references(doc):
    """Append the reference list."""
    doc.add_heading("6.  References", level=1)
    for ref in REFERENCES:
        para(doc, ref, size=9.5, space_after=5, indent=0.35, color=INK_2)
    page_break(doc)


def roles(doc):
    """Append the team roles table."""
    doc.add_heading("7.  Roles and Contributions", level=1)
    para(doc,
         "Roles are defined by module ownership and by pipeline stage. "
         "Assigning modules without assigning stages is how a shared "
         "pipeline becomes nobody's responsibility. All "
         "deliverables are jointly reviewed before submission.", align="j")
    table(doc,
          ["Stage", "Owner", "Definition of done"],
          [["L0  acquire and cache", "P2",
            "Pipeline runs offline against a warm cache"],
           ["L1  normalise to columnar", "P2",
            "Every source typed, documented, contract-tested"],
           ["L2  warehouse and star schema", "P1",
            "Build green; data contracts enforced in CI"],
           ["L3  feature panel", "P1", "One versioned table; models read only "
                                       "this"],
           ["L4  models", "P1", "Backtest reproducible from the manifest"],
           ["Drive-time matrix", "P2",
            "Matrices committed; routing artifacts deleted"],
           ["Application and figures", "P3",
            "Loads under five seconds; reads L3/L4 outputs only"],
           ["CI, contracts, reproducibility", "P2",
            "A red build blocks merge"]],
          widths=[1.75, 0.7, 3.8])

    for tag, name, owns, detail in [
        ("7.1  P1", "Overall technical direction, identification, integration",
         "Warehouse and dbt models; hazard and timing model; synthetic "
         "control and decay estimation; conformal intervals; portfolio "
         "optimiser; agent and MCP tools; identification gates.",
         "Owns the answer to 'how do you know it is causal rather than "
         "selection?'"),
        ("7.2  P2", "Data sources, validation, reproducibility",
         "Ingest for all nine public sources; drive-time matrix extraction "
         "and artifact cleanup; data contracts; pytest suite; CI; "
         "environment pinning and seed management.",
         "Owns the answer to 'does it build from cold, in one command?'"),
        ("7.3  P3", "Delivery, visualisation, communication",
         "Application build-out; operator and public planning views; figure "
         "toolkit; equity overlay; executive deck; the public write-up "
         "series and the open dataset release.",
         "Owns the answer to 'what decision does someone actually make?'"),
    ]:
        doc.add_heading(f"{tag}  —  {name}", level=2)
        para(doc, owns, align="j", space_after=4)
        para(doc, detail, italic=True, color=INK_2, size=10)

    doc.add_heading("7.4  Joint ownership", level=2)
    para(doc,
         "Proposal submission, midterm review, final deployment, paper "
         "submission and the executive presentation require sign-off from all "
         "three contributors.", align="j")
    page_break(doc)


def timeline(doc):
    """Append the project timeline."""
    doc.add_heading("8.  Timeline", level=1)
    para(doc,
         "Nine weeks, with the final week reserved for polish. Week 0 exists "
         "because six decisions are cheap to make now and expensive to "
         "reverse later.", align="j")
    table(doc,
          ["Week", "Focus", "Milestone", "Lead"],
          [["0", "Decisions and corrections",
            "Estimand, routing strategy, source swap, scope and budget "
            "settled in writing", "All"],
           ["1", "Infrastructure and ingest",
            "Repo, CI, cache, contracts; first sources landing", "P2"],
           ["2", "Facility panel and warehouse",
            "Target variable built: a 43-facility census with per-row "
            "sources and a measured accuracy bound, "
            "label-noise simulation harness in place; star schema live",
            "P1 + P2"],
           ["3", "Drive-time matrices and cost model",
            "Matrices extracted, routing artifacts deleted, cost function "
            "tested", "P2"],
           ["4", "Siting model and backtest",
            "Out-of-time backtest with calibration, conformal coverage, "
            "label-noise bound and H3 robustness check", "P1"],
           ["5", "Causal layer",
            "Decay curve, placebo inference, W constructed from estimate; "
            "staggered-adoption donor pool; generated-regressor correction",
            "P1"],
           ["6", "Decision layer and application",
            "Monte Carlo, rank stability, portfolio optimiser; app deployed",
            "P1 + P3"],
           ["7", "Agent and gates",
            "Six gates implemented; adversarial mutation set passing", "P1"],
           ["8", "Documentation and release",
            "Paper draft, open dataset published, forecast registry tagged",
            "P3"],
           ["9", "Buffer", "Reviewer feedback, recording, archive", "All"]],
          widths=[0.5, 1.7, 3.35, 0.7])
    para(doc,
         "The mitigations set out in §4.5 add roughly ten person-days across "
         "the three contributors — currency features, facility-date "
         "verification and the noise simulation, margin-of-error "
         "propagation, the H3 robustness check, the widened donor pool and "
         "the generated-regressor correction. That work is inside the "
         "envelope created by the scope decisions below rather than "
         "additional to it.", align="j")
    para(doc,
         "Scope is bounded deliberately. Two components a reader might expect "
         "— a fine-tuned narration model and a multi-model language-model "
         "ablation — are out of scope and recorded as such in the project "
         "roadmap, because neither contributes to novelty, model confidence "
         "or the use case.", align="j")
    page_break(doc)


def budget(doc):
    """Append the budget table."""
    doc.add_heading("9.  Budget", level=1)
    table(doc,
          ["Line item", "Provider", "Est. (USD)", "Guardrail"],
          [["Agent and extraction inference", "Hosted API", "$55",
            "Response caching; hard stop in config"],
           ["Contingency reserve", "—", "$25", "Reallocatable"],
           ["Cloud storage", "Free tier", "$0", "Within free credit"],
           ["Application hosting", "Free tier", "$0", "Free tier"],
           ["Warehouse (DuckDB)", "Local file", "$0", "Open source"],
           ["Transformations (dbt Core)", "Local", "$0", "Open source"],
           ["Routing preprocessing", "Free notebook tier", "$0",
            "Offline, once (§5.9)"],
           ["CI / CD", "Free tier", "$0", "2,000 min/month"],
           ["All data acquisition", "Public sources", "$0",
            "No paid API, no key"],
           ["Total estimated", "", "$80", "Under the $100 cap"],
           ["Hard cap", "", "$100", "Course rubric"]],
          widths=[1.95, 1.35, 0.85, 2.1])
    para(doc,
         "Compute cost is zero. The entire budget is language-model "
         "inference, and it is bounded in configuration: cumulative spend is "
         "logged per call with token counts, exposed in the application, and "
         "a guard raises a controlled exception at $80, forcing an explicit "
         "human decision to draw on the contingency.", align="j")
    para(doc,
         "Keeping the fine-tuned narration model and the multi-model ablation "
         "out of scope is what holds spend inside the cap without removing "
         "any component that answers a reviewer question.", align="j")
