# References to add in v4 — paste-ready, with verification checklist

Companion to `REVIEW_v4_professor_questions.md`.

> ⚠️ **Verify before pasting.** These were located via search on a host with no direct page
> access, so **titles, journals and years are reliable; some author lists and page numbers are
> not fully confirmed.** Every entry is marked ✅ (high confidence) or ⚠️ (verify author list /
> pages on Google Scholar before submission). Budget 30 minutes for the ⚠️ items.

---

## A. Amazon network and retail expansion — the "is this already done?" defence

**A1. ✅ THE critical one — cite this or be caught.**
Houde, J.-F., Newberry, P., & Seim, K. (2023). Nexus tax laws and economies of density in
e-commerce: A study of Amazon's fulfillment center network. *Econometrica*.
*(Earlier: NBER Working Paper 23361, 2017, "Economies of Density in E-Commerce: A Study of
Amazon's Fulfillment Center Network.")*
→ Use in §2.5 and §5.8. Pair with the delta table in the review, §1.2.

**A2. ⚠️** Empirical investigation of retail expansion and cannibalization in a dynamic
environment. *Management Science*, 58(11), 2001–2018 (2012).
*(Author is most likely Mitsukuni Nishida — confirm.)*
→ §2.2 or a new §2.6. This is your cannibalisation question in structural form.

**A3. ✅** Demand expansion and cannibalization effects from retail store entry: A structural
analysis of multichannel demand. *Management Science*, 68(12), 8829–8856 (2022).
→ Closest published analogue to Objective 2. State the delta explicitly.

**A4. ⚠️** Caoui, E. H., Hollenbeck, B., & Osborne, M. Dynamic entry and spatial competition:
An application to dollar store expansion. *(Working paper — confirm year/venue.)*
→ Comparable retail-siting problem with modern methods.

**A5. ✅** Schorung, M., Lecourt, T., & Dablanc, L. (2023). Assessing the spatial patterns of
Amazon warehouse network in the United States. *World Conference on Transport Research (WCTR)*.
→ Directly on Amazon warehouse geography; supports §4.1 MWPVL approach.

**A6. ✅** The impact of Amazon facilities on local economies. *Journal of Policy Analysis and
Management* (2025). doi:10.1002/pam.70065
→ Anchors the tax-abatement counterfactual use case (review §3.2).

---

## B. Spatial weight matrix estimation — required to rescue Innovation 2

**B1. ⚠️** Krisztin, T., & Piribauer, P. A Bayesian approach for estimation of weight matrices
in spatial autoregressive models. *Spatial Economic Analysis*. arXiv:2101.11938.

**B2. ⚠️** Souza, P. C. L. (2019). Estimation and selection of spatial weight matrix in a
spatial lag model. *(Warwick working paper / JBES — confirm final venue.)*

**B3. ⚠️** Parameterizing spatial weight matrices in spatial econometric models.
*Political Analysis* (2024). doi:10.1017/pan.2024.16

**B4. ✅** LeSage, J. P., & Pace, R. K. (2014). The biggest myth in spatial econometrics.
*Econometrics*, 2(4), 217–249.
→ **Most important of this group.** Turn it into your pre-registered RQ2 test (review §1.3).

**B5. ⚠️** A comparison study on criteria to select the most adequate weighting matrix.
*Entropy*, 21(2), 160 (2019).

---

## C. Synthetic control with interference — required to rescue §2.1

**C0. ✅ SECOND-MOST-CRITICAL CITATION IN THIS FILE, after A1.**
Pollmann, M. Causal inference for spatial treatments. arXiv:2011.00373
(submitted to *Econometrica*; author copy at michaelpollmann.github.io).
→ The definitive treatment of a treatment applied at a **location** with effects
**decaying over distance**, including distance-band / donut estimation. This sits directly on
§5.4 and it is uncited in v3. Cite it, and **adopt his estimator** for the decay-radius
novelty (review §6.2) rather than inventing one.

**C1. ⚠️** Bayesian synthetic control methods with spillover effects. arXiv:2408.00291.

**C2. ✅** A robust regression approach to synthetic control with interference.
arXiv:2411.01249.

**C3. ⚠️** Reich, B. J., et al. A review of spatial causal inference methods for environmental
and epidemiological applications. *International Statistical Review*. arXiv:2007.02714.

**C4. ⚠️** Exploiting neighborhood interference with low-order interactions under unit
randomized design. *Journal of Causal Inference*. doi:10.1515/jci-2022-0051

---

## D. Evaluation, uncertainty and metrics — required for Question 2

**D1. ✅ Highest priority in this section.**
Angelopoulos, A. N., & Bates, S. (2021). A gentle introduction to conformal prediction and
distribution-free uncertainty quantification. arXiv:2107.07511.
→ Justifies the conformal intervals (review §2.4a).

**D2. ✅** Hyndman, R. J., & Koehler, A. B. (2006). Another look at measures of forecast
accuracy. *International Journal of Forecasting*, 22(4), 679–688.
→ **The citation that kills MAPE.** Use it to justify replacing MAPE with deviance / RMSLE /
MASE. Cite it *yourself* before a reviewer cites it at you.

**D3. ✅** Li, J., Hui, B., Qu, G., et al. (2023). Can LLM already serve as a database
interface? A BIg bench for large-scale database grounded text-to-SQLs (**BIRD**).
*NeurIPS 2023*. arXiv:2305.03111.
→ Source for the ~80% SOTA / ~92.96% human baseline used to calibrate Objective 3.

**D4. ✅** Pervasive annotation errors break text-to-SQL benchmarks and leaderboards.
arXiv:2601.08778.
→ Justifies auditing your own gold query set.

**D5. ✅** Judging the judges: A systematic study of position bias in LLM-as-a-judge.
arXiv:2406.07791.

**D6. ⚠️** Reliability without validity: A systematic, large-scale evaluation of LLM-as-a-judge
models. arXiv:2606.19544.

**D7. ⚠️** The coin flip judge? Reliability and bias in LLM-as-a-judge evaluation.
arXiv:2606.13685.
→ D5–D7 support the mitigations in review §2.5 (randomised order, two judges, Cohen's κ).

**D8. ✅** Openshaw, S. (1984). *The Modifiable Areal Unit Problem*. CATMOG 38. Geo Books.
→ Required for the new §4.4 limitation on ZCTA grain.

---

## E. LLM agent safety with write access — required to rescue Innovation 1

**E1. ⚠️** Toward safe LLM agents: A survey of specification, verification, and enforcement.
arXiv:2608.14590.

**E2. ⚠️** SafeNlidb: A privacy-preserving safety alignment framework for LLM-based natural
language database interfaces. arXiv:2511.06778.

**E3. ✅** On the vulnerabilities of text-to-SQL models. arXiv:2211.15363.

**E4. ⚠️** Words become SQL: Securing AI assistants. *IEEE Symposium on Security and Privacy*
(2026).
→ E1–E4 establish the prior art you must acknowledge, so that the *inferential-integrity*
gap (review §1.3) reads as a precise finding rather than an unread literature.

---

## F. Public-interest use case — required for Question 3

**F1. ✅** South Coast Air Quality Management District (2021). *Rule 2305 — Warehouse Indirect
Source Rule: Warehouse Actions and Investments to Reduce Emissions (WAIRE) Program.*
*(EPA-approved; see EPA news release, "EPA Approves South Coast AQMD's Groundbreaking Rule to
Reduce Southern California Air Pollution.")*
→ The concrete regulatory institution behind use case #1.

**F2. ✅** METRANS (2018). *Location of warehouses and environmental justice: Evidence from four
metros in California.* Report MF 1.1g.

**F3. ⚠️** Urban Freight Lab, University of Washington. *Logistics sprawl and environmental
justice.* *(Confirm year — source indicates 2026.)*
→ Documents "a significant spatial and racial mismatch between delivery supply and demand."

**F4. ⚠️** Urban Freight Lab (2025). *Logistics of zoning, zoning for logistics: Toward healthy
and equitable development for urban freight.*

**F5. ✅** US Environmental Protection Agency. *EJScreen: Environmental Justice Screening and
Mapping Tool.*
→ The actual data source for the equity overlay (review §3.3). Free download, joins on census
geography.

**F6. ✅** Amazon.com Inc. (June 2025). Press announcement: over $4bn investment to expand
same-day and next-day Prime delivery to 4,000+ smaller cities, towns and rural communities by
end of 2026.
→ **Two uses.** (a) Topicality hook for §1.3. (b) **It contradicts §2.3's claim that rural
ZCTAs are structural zeros** — you must address this (review, correction #20).

---

## G. Corrections to existing references

| Ref | Problem | Correct form |
|---|---|---|
| **[11]** | *"Chen, T., & Guestrin, C. (2016). **LightGBM**: A scalable tree boosting system"* — that paper is **XGBoost** | Either cite as **XGBoost**, or replace with Ke, G., Meng, Q., Finley, T., et al. (2017). LightGBM: A highly efficient gradient boosting decision tree. *NeurIPS 2017* — which you already have in the second list |
| **Card & Krueger (1994)** | Cited in §5.8, absent from both reference lists | Card, D., & Krueger, A. B. (1994). Minimum wages and employment: A case study of the fast-food industry in New Jersey and Pennsylvania. *American Economic Review*, 84(4), 772–793 |
| **Wei et al.** | Cited as 2022 in text, listed as 2023 in references | Wei, J., et al. (2022). Chain-of-thought prompting elicits reasoning in large language models. *NeurIPS 2022*. Use **2022** in both places |
| **Two reference lists** | Wager & Athey, Yao et al., Chen & Guestrin each appear twice | Merge into one alphabetised list; renumber or drop numbering entirely |
| **Uncited entries** | Angrist & Pischke; Glaeser & Gyourko; Zheng et al.; Chen et al. (2024); Rojas & Nakamura | Either cite them in the text or remove. Rojas & Nakamura is worth *keeping* — cite it in Innovation 5 |

---

## H. Suggested placement map

| Section | Add |
|---|---|
| §2.1 Spatial causal inference | C1, C2, C3, C4, B4 |
| §2.2 Routing / density | A1 *(economies of density is exactly this)* |
| §2.4 LLM agents | E1, E2, E3, E4, D3, D4 |
| §2.5 Industry / reproduction gap | **A1**, A5, A6, F1, F2 |
| §2.6 *(new)* Retail expansion & cannibalisation | A2, A3, A4 |
| §4.2.1 Proxies | D2, D8 |
| §4.4 Limitations | **D8 (MAUP)**, F6 (rural contradiction) |
| §4.5 Identification | A6, F1 *(abatement counterfactual)* |
| §5.3 Demand model | D1, D2 |
| §5.4 Cannibalization | **C0 (Pollmann)**, C1, C2, B1, B2, B3, **B4**, J4–J6 |
| §5.6 NPV → *portfolio optimiser* | J7, J8, J9 |
| *New* LLM-extraction validity | J1, J2, J3 |
| *New* Stated vs revealed siting | J10, J11 |
| §5.6 NPV / UQ | **D1** |
| §5.7 Agent + gates | E1–E4 |
| §5.8 Unique contribution | **A1**, B4, E1, F1, F5 |
| §5.10 Ablation | D3, D5, D6, D7 |
| *New* Public-interest section | F1–F6 |

---

## I. Verification workflow (30 minutes, do it before submitting)

1. Search each ⚠️ entry by **exact title** on Google Scholar.
2. Confirm: author list, year, journal, volume/issue/pages.
3. For arXiv entries, check whether a **peer-reviewed version** now exists — cite that instead;
   a reviewer notices when everything is a preprint.
4. Confirm A1's *Econometrica* volume, issue and page numbers — this is the one citation that
   must be perfect.
5. Confirm **C0 (Pollmann)** — check whether the *Econometrica* version has now appeared; if so
   cite the journal version, not the arXiv preprint.
6. Re-run the LightGBM/XGBoost check across the whole document; the error appears **twice** in v3.

---

## J. New-novelty support — added after the first read-through

Supporting citations for the additions proposed in review §6. Cite these **so that the new
claims are narrow and survive**, rather than repeating the Innovation-2 mistake.

### J.1 — Generated regressors / LLM-extracted variables (review §6.0)

**J1. ✅** Egami, N., Hinck, M., Stewart, B. M., & Wei, H. (2023). Using imperfect surrogates
for downstream inference: Design-based supervised learning for social science applications of
large language models. *NeurIPS 2023*. arXiv:2306.04746.

**J2. ✅** Angelopoulos, A. N., Bates, S., Fannjiang, C., Jordan, M. I., & Zrnic, T. (2023).
Prediction-powered inference. *Science*, 382(6671), 669–674.

**J3. ✅** Pagan, A. (1984). Econometric issues in the analysis of regressions with generated
regressors. *International Economic Review*, 25(1), 221–247.
→ J1–J3 fix a live bug: LLM-extracted facility rows feed W and the Huff factor as if measured
without error, so your standard errors are understated. Not a novelty — but it *is* correct,
and almost nobody in the LLM-agent space does it. ~1 day.

### J.2 — Spatial spillover decay (review §6.2)

**J4. ⚠️** Kerr, W. R., & Kominers, S. D. Agglomerative forces and cluster shapes.
*Review of Economics and Statistics*.

**J5. ⚠️** Gibbons, S., et al. Agglomeration and distance decay. *(LSE working paper — confirm
final venue and co-authors.)*

**J6. ⚠️** The distance decay effect and spatial reach of spillovers.
*(Confirm authors/journal.)*
→ Establishes that distance-decay estimation is a **standard method**, so your contribution is
the *number* for same-day delivery, not the estimator. Frame it that way.

### J.3 — Portfolio / location-allocation optimisation (review §6.1)

**J7. ⚠️** Hernandez, T. Retail location decision-making and store portfolio management.
*Canadian Journal of Regional Science / RCSR*, 24(3).

**J8. ⚠️** Kim, C. Optimal retail location: Empirical methodology and application to practice.
Baker Retailing Center, Wharton.

**J9. —** Standard p-median / maximal covering location problem literature (ReVelle & Swain
1970; Church & ReVelle 1974). Pick one canonical cite.
→ J7–J9 exist precisely so you do **not** claim location-allocation optimisation is new. Your
claim is narrower: solving it with an *empirically estimated* cannibalisation coefficient and
*estimated* density externalities jointly, and reporting the greedy-vs-optimised gap.

### J.4 — Stated vs. revealed corporate rationale (review §6.4)

**J10. ⚠️** When large employers come to town: Labor market entry and corporate disclosure.
*The Accounting Review*. doi:10.2308/TAR-2024-0309

**J11. ⚠️** Corporate disclosure: Facts or opinions? Federal Reserve Bank of Philadelphia
Working Paper 21-40.
→ Establishes disclosure-vs-behaviour as an existing literature in accounting/finance. Your
delta is applying it to **siting criteria**, with an LLM extracting the stated rationale and
comparing it against fitted model weights.

---

## K. The two citations that would have cost you most

If you verify nothing else, verify these two. Each is a published, findable paper that sits
directly on a claim v3 makes, and neither is cited:

| | Paper | Kills which claim | Where it goes |
|---|---|---|---|
| **A1** | Houde, Newberry & Seim, *Econometrica* 2023 | "nobody has modelled Amazon's network" | §2.5, §5.8 |
| **C0** | Pollmann, *Causal Inference for Spatial Treatments* | "SCM can't handle spatial spillovers and nobody has fixed it" | §2.1, §5.4 |

And one commercial source in the same category of danger:

| | Source | Undercuts which claim | Where it goes |
|---|---|---|---|
| **L1** | Esri ArcGIS *Measure Cannibalization* | any wording implying cannibalization measurement is new | §5.4, as a "relation to commercial practice" note |

---

## L. Commercial / industry prior art — cite these to stay honest

Added after a second challenge. Sections A–K cover the **academic** literature. These are
**commercial products and industry practice** — a different kind of prior art with a different
severity (see review §6.7). None of these makes a claim *false*; they make the words
"first" and "novel" naive. Cite them in a short "Relation to commercial practice" paragraph and
the problem disappears.

**L1. ✅** Esri. *How Measure Cannibalization works* — ArcGIS Pro, Business Analyst Tools
documentation. Also *Analyze and resolve interactions between trade areas*.
→ Cannibalization measurement is a shipped GIS tool. **Your delta: theirs is trade-area overlap
(descriptive geometry); yours is a causal treatment effect with a counterfactual and a decay
curve.** Say this explicitly in §5.4 — it is a real distinction and it pre-empts the challenge.

**L2. ✅** Supply-chain network design (SCND) software category: Coupa Supply Chain Guru
(formerly LLamasoft), AIMMS SC Navigator, anyLogistix, Optilogic.
→ Multi-facility location optimisation has been a mature commercial category for 20+ years.
**This demotes "portfolio, not ranking" from a contribution to a method fix.** Still build it;
do not claim it. Delta if you need one: SCND tools optimise *your own* network with *assumed*
demand and *known* costs — not a competitor's network from public data with an *estimated
causal* interaction term.

**L3. ⚠️** Commercial site-selection and location-intelligence platforms: Buxton ("Factor"),
Kalibrate, Placer.ai, Esri Business Analyst.
→ Context for §5.8 Innovation 4. Raises the bar on "first public tool" — which is why the
review recommends "no public, reproducible artifact" instead.

**L4. —** Commercial-real-estate trade press tracking Amazon's expansion: CoStar, Bisnow,
CRE Daily, *Site Selection Magazine*.
→ **Useful negative result.** These track Amazon's expansion *after the fact*. No open,
auditable, forward-looking prediction of a competitor's next locations was found. This is why
cross-operator transferability (review §6.3) and the public-data explainability ceiling
(review §3.3) survive the commercial check intact.

### The framing rule that follows from L1–L4

| Never write | Always write |
|---|---|
| "first", "novel", "no prior work", "nobody has done this" | "not published in the open literature" |
| | "not available as a public, reproducible artifact" |
| | "to our knowledge, not reported for same-day delivery at ZCTA grain" |

The right-hand form stays true regardless of what Esri ships, Coupa sells, or Amazon runs
internally — because all of those are proprietary, licensed and unreproducible. **A product
datasheet cannot falsify it.**
