# References

*Last reviewed 2026-09-14. `docs/README.md` noted that this was the only
top-level file carrying no date, so one is now stated — but state what the
review covered, which is narrow: the entries were checked for claims
invalidated by the 2026-09-14 work, and **none was found**. The confidence
marks themselves were NOT re-verified in that pass, and the [K] entries still
need checking against a source before submission.*

**One bibliography for the whole project: the methodological literature the
code implements, the sources behind the model's parameters, and a pointer to
the per-source data documentation.**

Parameter-by-parameter provenance is in
[`data/PARAMETERS.md`](data/PARAMETERS.md). Per-dataset provenance,
reachability and acquisition steps are in [`data/`](data/README.md), one file
per source; they are **not** restated here.

## How to read the confidence marks

This repository was built on a host with no external page access: search
returns titles and URLs, and WebFetch is proxy-blocked. Rather than pretend
otherwise, every entry carries its evidential status.

| Mark | Meaning |
|---|---|
| **[V]** | Verified against the full text, read in this repository or in `/tmp/res/`. Authors, title, venue, volume, pages and year are quoted from the document itself. |
| **[T]** | Title and venue verified against a publisher or repository URL returned by search. Contents not read. Author lists and page numbers may be incomplete. |
| **[K]** | Cited from the author's own knowledge. The work is real and standard, but no page was opened to confirm the details printed here. **Check before submission.** |

A fabricated reference is the worst outcome available to a document like this
one, and it has already happened once on this project with a hallucinated
dataset URL. Nothing below is listed unless it was seen in a search result, in
a reference list of a paper that was read, or is a standard text the author can
name precisely. Where a detail is uncertain it is marked uncertain rather than
smoothed over.

---

## 1. Economies of density and retail/logistics network siting

These are the direct ancestors of the cost model and the portfolio optimiser.
Both were read in full; both are quoted in `data/PARAMETERS.md` for specific
parameter comparisons.

**Holmes, T. J. (2011). The diffusion of Wal-Mart and economies of density.
*Econometrica*, 79(1), 253-302. DOI: 10.3982/ECTA7699.** **[V]**
> Read in full. The methodological ancestor of `optimize/`: a network of
> facilities chosen against a distance-to-distribution-centre cost, estimated
> by moment inequalities rather than by solving the dynamic program. Used in
> `data/PARAMETERS.md` §7.3 for the discount factor (beta = 0.95) and §7.4 for
> cannibalisation (stand-alone $41.4m vs incremental $36.3m for a new store,
> "approximately a 10 percent difference", Table VIII; ~1% chain-wide from
> Wal-Mart's 2004 annual report). His distance coefficient is
> tau = $3,500 per store-mile-year in 2005 dollars, four times the $1.20 per
> truck-mile he was quoted by industry for trucking alone.

**Houde, J.-F., Newberry, P., & Seim, K. (2023). Nexus tax laws and economies
of density in e-commerce: A study of Amazon's fulfillment center network.
*Econometrica*, 91(1), 147-190.** **[V]**
> Read in full. Journal line, volume, issue, pages and author affiliations
> quoted from the document. The article DOI is not printed in the text; the
> supplement cites `https://doi.org/10.3982/ECTA15265`, which by Econometrica's
> convention is the article DOI, **but that is an inference**. Manuscript
> received 18 April 2017; accepted 13 April 2022; online 23 June 2022. Open
> access, CC BY-NC-ND.
>
> Used in `data/PARAMETERS.md` §6.11 (household order frequency), §6.12
> (income and online spending), §6.16 (fixed cost of a facility), §6.21
> (catchment radii from MWPVL) and §7.3 (discount factor). Their headline
> shipping cost is $0.34 per 100 miles per order; every core cost primitive in
> the paper is their own structural estimate, not a borrowed industry figure.

**Houde, J.-F., Newberry, P., & Seim, K. (2017, revised May 2021). Economies of
density in e-commerce: A study of Amazon's fulfillment center network. NBER
Working Paper 23361.** **[V]**
> Read in full, both the April 2017 original and the May 2021 revision. Cite
> the published version above unless you specifically need (a) the 2017
> parameterisation of shipping cost per dollar per mile, or (b) the external
> cost per ton-mile analysis, which was **cut from the Econometrica version**
> and survives only in the May 2021 working paper.

**Nishida, M. (2012). Estimating a model of strategic network choice: The
convenience-store industry in Okinawa / Empirical investigation of retail
expansion and cannibalization in a dynamic environment. *Management Science*,
58(11), 2001-2018.** **[T, author and exact title UNCONFIRMED]**
> A copy of the *Management Science* article is at
> `marketing.business.uconn.edu/wp-content/uploads/sites/724/2014/08/
> empirical-investigation-of-retail-expansion.pdf`. The volume, issue and pages
> are carried from `REFERENCES_to_add_v4.md`, which itself marks the author
> attribution unconfirmed. **Resolve on Google Scholar before citing.** It is
> the closest structural treatment of cannibalisation under expansion and is
> the right comparator for `cannibalisation_peak`.

---

## 2. Continuous approximation and vehicle routing

The mathematics in `cost/daganzo.py`.

**Daganzo, C. F. (1984). The distance traveled to visit N points with a maximum
of C stops per vehicle: An analytic model and an application. *Transportation
Science*, 18(4), 331-350. DOI: 10.1287/trsc.18.4.331.** **[T]**
> Title, volume, issue, pages and DOI confirmed against the INFORMS URL. **This
> is the direct source of the model's structure**: the split between line haul
> shared across a tour of C stops and local travel scaling as
> `k / sqrt(density)`.

**Daganzo, C. F. (1984). Approximate formulas for average distances associated
with zones. *Transportation Science*, 18(3), 231-253. DOI:
10.1287/trsc.18.3.231.** **[T]**
> Confirmed against the INFORMS URL. The companion paper, and the source of the
> zone-geometry constants of which `bhh_constant = 0.57` is one.

**Beardwood, J., Halton, J. H., & Hammersley, J. M. (1959). The shortest path
through many points. *Mathematical Proceedings of the Cambridge Philosophical
Society*, 55(4), 299-327.** **[K]**
> The underlying theorem: a tour through n random points in area A has length
> asymptotically `k * sqrt(n * A)`. Standard and certainly real; the volume,
> issue and page range are from memory and should be checked.

**Larson, R. C., & Odoni, A. R. (1981). *Urban Operations Research*.
Prentice-Hall.** **[T]**
> Section 6.4.8 gives the TSP tour-length approximation in textbook form and is
> freely readable at
> `web.mit.edu/urban_or_book/www/book/chapter6/6.4.8.html`. The most accessible
> statement of the constant for a reader who does not want to buy a 1984
> journal issue.

**Daganzo, C. F., & Smilowitz, K. R. (2004).** Working paper on continuous
approximation for transportation-logistics problems, Northwestern IEMS,
`users.iems.northwestern.edu/~smilo/DaganzoSmilowitz2004.pdf`. **[T, title
UNCONFIRMED]**
> Listed as a lead for extending the approximation to multi-echelon networks.
> Do not cite without resolving the title and publication venue.

---

## 3. Partial identification and inference under set-valued parameters

Read in full for the methodology of `agent/gates_inference.py` and the
optimality-gap reporting in `optimize/select.py`.

**Manski, C. F. (2003). *Partial Identification of Probability Distributions*.
Springer Series in Statistics. Springer-Verlag.** **[V]**
> Series and title confirmed from Molinari's reference list.

**Molinari, F. (2019). Econometrics with partial identification. cemmap working
paper CWP25/19. Institute for Fiscal Studies / Department of Economics, UCL.
30 May 2019.** **[V]**
> Read in full (`/tmp/res/CWP2519.txt`). Author affiliation printed as Cornell
> University, Department of Economics. Published in revised form as a chapter
> of the *Handbook of Econometrics*; cite the cemmap version unless you have
> the handbook pagination.

**Kaido, H., Molinari, F., & Stoye, J. (2019). Confidence intervals for
projections of partially identified parameters. *Econometrica*, 87(4),
1397-1432.** **[V]**
> Read in full. Journal line, volume, issue, pages and year quoted from the
> document.

**Pakes, A., Porter, J., Ho, K., & Ishii, J. (2006). Moment inequalities and
their application. Working paper, Harvard University.** **[V]**
> Citation taken verbatim from Holmes (2011)'s reference list, where it is
> cited at pages 257 and 277 as the inference method for his moment
> inequalities. It later appeared as Pakes, Porter, Ho & Ishii (2015),
> *Econometrica* 83(1), 315-334 **[K -- the published version's details are
> from memory]**. Cite whichever version you actually use.

**Politis, D. N., Romano, J. P., & Wolf, M. (1999). *Subsampling*. New York:
Springer-Verlag.** **[V]**
> Citation taken verbatim from Holmes (2011)'s reference list (cited at his
> page 290, for the store-location subsampling procedure).

---

## 4. Discrete choice and simulation

**Train, K. E. (2009). *Discrete Choice Methods with Simulation* (2nd ed.).
Cambridge University Press.** **[V]**
> Read in full (chapters 1-14, references and index). The second edition is
> confirmed from the typesetting marks in the extracted text
> (`CB495/Train`, March 2009). The full text is freely available from the
> author at `eml.berkeley.edu/books/choice2.html` **[K -- URL from memory]**.

---

## 5. Record linkage

Behind `common/` address matching and the facility-panel join.

**Winkler, W. E. (1999). The state of record linkage and current research
problems. Statistical Research Report Series RR99/04. Statistical Research
Division, U.S. Bureau of the Census.** **[V]**
> Read in full. The title as printed is *"The State of Record Linkage and
> Current Research Problems"*; note this is **not** the same paper as Winkler's
> better-known string-comparator papers, and the report number in the brief
> (RR99-04) and on the document (RR99/04) differ only in punctuation. Builds on
> Fellegi and Sunter's model and Newcombe's earlier work.

**Fellegi, I. P., & Sunter, A. B. (1969). A theory for record linkage.
*Journal of the American Statistical Association*, 64(328), 1183-1210.** **[K]**
> The formal model Winkler's report rests on. Details from memory; verify.

---

## 6. Parameter sources: statistics and industry

These support specific constants. What each one does and does not establish is
set out in `data/PARAMETERS.md`; the marks here refer only to the reference
itself.

**U.S. Bureau of Labor Statistics. *Occupational Employment and Wage
Statistics* (OEWS).** `bls.gov/oes/tables.htm`; Handbook of Methods, OEWS,
"Calculation", `bls.gov/opub/hom/oews/calculation.htm`. **[T]**
> The wage input to the cost model. See `data/bls_oes.md` for the acquisition
> procedure (the host returns HTTP 403; download manually). The Handbook's
> statement that annual wages are hourly mean x 2,080 hours is the basis of
> `PARAMETERS.md` §7.1 and is marked **[K]** there because the page was not
> opened.

**U.S. Bureau of Labor Statistics. *Employer Costs for Employee Compensation*
(ECEC).** News releases archived at `bls.gov/news.release/archives/ecec_*.htm`;
historical supplemental tables at `bls.gov/web/ecec/ecsuphst.pdf`. **[T]**
> The benchmark for `wage_loading`. See `PARAMETERS.md` §7.2.

**American Transportation Research Institute. *An Analysis of the Operational
Costs of Trucking* (annual).** 2023 update:
`connect.ncdot.gov/resources/BIP2026-I40Planning/Documents/
ATRI-Operational-Cost-of-Trucking-06-2023.pdf`; July 2025 update:
`truckingresearch.org/wp-content/uploads/2025/07/
ATRI-Operational-Costs-of-Trucking-07-2025.pdf`. **[T]**
> The benchmark for `maintenance_usd_per_mile`. Measures Class 8 combination
> tractor-trailers, **not** delivery vans -- see `PARAMETERS.md` §6.5.

**U.S. Energy Information Administration.** Diesel and fuel price series. See
`data/eia_prices.md`. **[T]**

**U.S. Census Bureau.** American Community Survey 1-year and 5-year estimates,
County Business Patterns, TIGER/Line and Gazetteer geographies, CBSA
delineation files, ZCTA-county crosswalk. See `data/acs1.md`, `data/acs5.md`,
`data/cbp_zip.md`, `data/tiger_zcta.md`, `data/gaz_zcta.md`,
`data/cbsa_county.md`, `data/zcta_county_xwalk.md`, `data/bps_county.md`.
**[T]**

**Pitney Bowes. *Parcel Shipping Index* (annual).**
`pitneybowes.com/content/dam/pitneybowes/us/en/newsroom/
us-parcelshippingindex-infographic-final.pdf`. **[T]**
> National parcel volume, one half of the derivation of
> `parcels_per_household_per_week = 3.2`.

**MWPVL International.** `mwpvl.com`. **[T]**
> Amazon facility network inventory: counts, types, square footage and
> catchment conventions. Not peer-reviewed, but it is the facility-network
> source used by Houde, Newberry and Seim (2023), which is the best
> availability argument there is for it.

**Damodaran, A. Cost of capital by industry (annual dataset), NYU Stern.**
`pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/wacc.html`. **[T]**
> The comparator for `discount_rate`. Also used by Houde, Newberry and Seim
> (2023) for retail net margins.

---

## 7. Leads not yet read

Listed because `data/PARAMETERS.md` names them as the places to look for the
parameters that currently have no source. **None of them has been read, and
none of them currently supports any number in this repository.**

For `service_minutes_per_stop` and `parcels_per_stop`:

- *Vehicle stop time estimation during last mile deliveries: A statistical
  analysis to increase the accuracy of ...* TU Delft repository; CORE record
  130234459. **[T, authors unconfirmed]**
- Urban Freight Lab, University of Washington. *Do parcel lockers reduce
  delivery times? Evidence from the field.* Also OSTI 2418036.
  `urbanfreightlab.com/publications/
  do-parcel-lockers-reduce-delivery-times-evidence-from-the-field/` **[T]**
- U.S. Postal Service Office of Inspector General. *City Delivery Efficiency
  Review -- New York District.* Report DR-AR-11-002. **[T]**
- METRANS / Rodrigue, J.-P. *Residential parcel deliveries: Evidence from a
  large apartment complex.* Report MF 5.1d. **[T]**

For `circuity`:

- Boeing, G. *The relative circuity of walkable and drivable urban street
  networks.* arXiv:1708.00836. **[T]** Measures edge-level network circuity,
  which is a different quantity from an origin-destination ratio.
- Liu, Xie, Lin, & Jin. *Empirical estimation of shortest route length along
  U.S. interstate highways based on great circle distance.* OSTI 1813132.
  **[T]**

For `van_mpg` and `avg_speed_mph`:

- National Renewable Energy Laboratory. *Development of 80- and 100-mile work
  day cycles representative of commercial pickup and delivery operation.*
  NREL/TP-5400-70943, `nrel.gov/docs/fy18osti/70943.pdf`. **[T]**

---

## 8. Cross-references, not restated here

- **Per-dataset provenance, licence, endpoint, measured reachability and
  manual-acquisition steps:** [`data/`](data/README.md), one Markdown file per
  source, generated from `ingest/sources.py`.
- **What every model parameter is worth, and which are unsourced:**
  [`data/PARAMETERS.md`](data/PARAMETERS.md).
- **How the cost model works and why:** [`data/COST_MODEL.md`](data/COST_MODEL.md).
- **The continuous-approximation literature behind §2, and what of it has
  actually been read:**
  [`research/NOTES_daganzo_1984.md`](research/NOTES_daganzo_1984.md). Added
  2026-09-14. **§2 above needs three corrections and that file documents
  them.** (1) The entry for *"Daganzo, C. F. (1984). Approximate formulas for
  average distances associated with zones. Transportation Science 18(3),
  231-253"* is wrong: DOI `10.1287/trsc.18.3.231` is **R. J. Vaughan**,
  pp. **231-244**, and its subject is average distances between random points
  in zones — not tour lengths — so it is not a companion paper and not a
  source for `bhh_constant`. (2) A third Daganzo 1984 paper, *The length of
  tours in zones of different shapes*, Transportation Research Part B 18(2),
  135-145, DOI `10.1016/0191-2615(84)90027-4`, 274 citations, exists, is the
  likely source of the constant, and is **not cited above**. (3) Larson &
  Odoni §6.4.8 was retrieved and read in full; it gives **K ≈ 0.765, not
  0.57**, and does not mention Daganzo. Read the notes file before defending
  `bhh_constant`. It also documents two working retrieval recipes
  (`api.openalex.org` for bibliographic records and abstracts,
  `core.ac.uk/reader/<id>` for open full text) that would let several of the
  **[K]** and **[T]** marks above be upgraded or corrected — the header's
  "no external page access" is too pessimistic.
- **Facility panel provenance, row by row:**
  [`data/FACILITY_PANEL_PROVENANCE.md`](data/FACILITY_PANEL_PROVENANCE.md).
- **Architecture decisions, including the offline-routing decision that makes
  the continuous approximation necessary:** [`adr/`](adr/0002-routing-offline.md).
- **Wider proposal bibliography still being merged in:**
  `../REFERENCES_to_add_v4.md`, outside this repository. That file covers the
  spatial-causal, LLM-agent and public-interest literature and carries its own
  verification checklist; it has **not** been audited here and its warnings
  apply.
