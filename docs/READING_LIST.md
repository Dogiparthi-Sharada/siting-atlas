# Reading list — what to download, and what each one decides

*Created 2026-09-13, reviewed 2026-09-14 and nothing in it was invalidated by
that day's work. The rule agreed with the user: **read first, then change the
plan.** Nothing in `docs/METHODS_RESEARCH.md` or `docs/ROADMAP.md` moves on the
strength of a guess about what one of these says.*

Save into `../Research/`. A filename prefix makes them findable:
`clean_`, `loc_`, `metrics_`, `econ_`.

---

## 0. Already in Research/ — do NOT download again

```
  Train, Discrete Choice Methods with Simulation   Ch03-14 + refs + index
  Holmes (2011), Diffusion of Wal-Mart              ecta7699.pdf
  Houde, Newberry & Seim (2023) Econometrica        ECTA15265.pdf
  Houde, Newberry & Seim, NBER WP 23361             w23361.rev1.pdf
  Kaido, Molinari & Stoye (2019) Econometrica       ECTA14075.pdf
  Molinari, Econometrics with Partial Identification (Handbook)  CWP2519.pdf
  Winkler (1999), State of RECORD LINKAGE, RR99-04  rr99-04.pdf
```

Partial identification is fully covered. Discrete choice is fully covered.
The two Amazon papers are covered. Do not spend money or time there.

---

## 1. MUST HAVE — each one gates a specific decision

### Data quality (4) — fixes a bias that is in our results today

```
  1  Rahm & Do (2000), "Data Cleaning: Problems and Current Approaches"
     IEEE Data Engineering Bulletin 23(4):3-13
     https://dbs.uni-leipzig.de/file/aktuelles_DataCleaning.pdf
     DECIDES: the audit frame. Whether docs/data/DATA_QUALITY.md is a
     checklist against a published taxonomy or a list of things we
     happened to notice.
     GATES: the open-defect register, STATUS.md §6.

  2  Winkler (1999), "State of Statistical Data Editing and Current
     Research Problems", US Census Bureau RR99-01
     Search: census.gov srd papers rr99-01   (also on CiteSeerX)
     NOTE: this is the COMPANION to rr99-04 we already have. Same author,
     same series. rr99-04 is record linkage; -01 is edit and imputation.
     DECIDES: whether we build a formal edit system (declared constraints,
     consistency-checked, minimum-change) or keep ad-hoc filters.
     GATES: the size of the cleaning task — my guess is 2 days vs 1 week
     and I want the paper before I commit to either.

  3  Van den Broeck, Cucu, Mehta & Cunningham (2005), "Data Cleaning:
     Detecting, Diagnosing, and Editing Data Abnormalities"
     PLoS Medicine 2(10):e267.  PMC1198040  (open access)
     DECIDES: the procedure for the screen -> diagnose -> treat loop, and
     what a cleaning log has to record to be defensible.
     Short. Read this one first if time is tight.

  4  Little & Rubin, Statistical Analysis with Missing Data, 3rd ed (2019)
     Wiley. CHAPTERS 1-3 ONLY.
     DECIDES: the biggest open question in the project right now. Rent is
     missing for 94.3% of ZCTAs and the ZCTAs where it IS observed are 64x
     denser. We currently delete those rows. Ch. 1-3 settle whether this is
     MAR (imputation valid) or MNAR (bounds only). I have a view; I do not
     want to act on it unread.
     GATES: STATUS.md §5 item 8 — a missingness treatment of any kind.
```

### Facility location (3) — upgrades a component that already works

```
  5  Hakimi (1964), "Optimum Locations of Switching Centers and the
     Absolute Centers and Medians of a Graph"
     Operations Research 12(3):450-459
     *** READ 2026-09-13. THE CLAIM BELOW WAS WRONG. ***
     I said this licenses restricting depot candidates to real buildings,
     and called it "close to the whole argument". It does not, for two
     reasons found by reading it:
       (a) It proves ONE thing — "An absolute median of a graph is always
           at a vertex of a graph" (p.456). The letter p appears nowhere
           in the paper. We place 334 depots. The p-facility result is
           HAKIMI (1965), a DIFFERENT paper, and we do not have it.
           Klose & Drexl are careful and cite "(1964, 1965)"; so must we.
       (b) It is a result about GRAPHS. The proof turns on eq. (16): any
           point lies on a branch and exits through one of two endpoints.
           We use haversine distance in the plane, where there are no
           branches. The plane analogue is the Weber point, which is
           generally NOT at a demand node.
     So restricting depots to ZCTA centroids is a real restriction, not a
     free lunch. Measured cost of that restriction: 0.45% against letting
     depots move freely (Weiszfeld refinement), and that is a LOWER bound
     since the continuous figure is itself a local optimum.
     The defensible write-up line: not licensed by Hakimi in our metric,
     but nearly free, and it buys the guarantee that every depot stands on
     inhabited ground — which is now enforced by a test.
     Notes: docs/research/NOTES_hakimi_1964.md
     SHORT — about 10 pages.

  6  Klose & Drexl (2005), "Facility location models for distribution
     system design", European Journal of Operational Research 162(1):4-29
     DECIDES: which formulation replaces k-means in cost/depots.py:108.
     p-median, capacitated p-median, or fixed-charge. We charge a LINEAR
     line-haul cost and k-means minimises SQUARED distance, so we are
     currently optimising a different objective from the one we bill.
     VERIFY the volume/page numbers on Scholar; I am confident of the
     title and authors, less so of the exact pagination.

  7  Daganzo, Logistics Systems Analysis, 4th ed. (2005), Springer
     *** DOWNGRADED 2026-09-13 — see section 1b. Get it if convenient,
     do not chase it. ***
     The original reason was to source the BHH constant `k`. That reason
     collapsed: the measured sensitivity says `bhh_constant` moves the
     median 1.9% when wrong by HALF. It is the most robust number in the
     model, and it already has a citation (Daganzo 1984, Transportation
     Science 18(3) and 18(4), both DOIs confirmed by the parameters
     agent). The book would add the textbook treatment of the CA method,
     which is nice for the literature review and changes no number.
     If only one edition is available, any of 2nd-4th is fine.
```

### Method and metrics (2)

```
  8  Wooldridge, Econometric Analysis of Cross Section and Panel Data,
     2nd ed. (2010), MIT Press. CHAPTER 15 (discrete response), and
     Ch. 13 if it comes with it.
     DECIDES: the estimation and inference details for the conditional
     choice model. Train covers the theory; Wooldridge covers what to
     actually do with 43 decisions (38 usable) and clustered errors —
     which is genuinely few, and the reason inference matters more here
     than estimation.
     GATES: STATUS.md §5 item 2 — re-running the inference.

  9  Gneiting & Raftery (2007), "Strictly Proper Scoring Rules,
     Prediction, and Estimation", JASA 102(477):359-378
     DECIDES: the defence of our headline-metric change. We dropped AUC
     for Brier skill + calibration. Right now the honest reason is "AUC
     could not see the calibration failure", which sounds like we changed
     the metric after seeing the result. This paper is the principled
     justification, written before we had a result. Your professor will
     ask this question.
```

**Nine items. Four are open-access PDFs, three are journal articles your
library will have, two are textbook chapters.**

---

## 1b. Not papers — and this is where the headline actually lives

*Added 2026-09-13, after the parameter sensitivity sweep came back.*

The sweep produced a result that should change how we spend reading time.
Ranked by how much each constant moves the median $/parcel across its
plausible range:

```
  service_minutes_per_stop  1.5-4.0 min      -25.0%  /  +44.3%
  parcels_per_stop          1.0-2.0          +39.3%  /  -29.5%
  van_lease_usd_per_day     $25-70            -8.8%  /  +15.9%
  delivery_days_per_week    5-7              +13.5%  /   -9.6%
  ...
  circuity                  1.15-1.45         -1.2%  /   +1.2%
  bhh_constant              0.45-0.71         -0.7%  /   +0.9%
  default_linehaul_miles    15-40             0.00%  /   0.00%
```

**The routing mathematics is decoration.** `bhh_constant` is the ONLY
constant that already had a proper citation, and it is the second-least
influential thing in the model. A reviewer attacking Daganzo is attacking
our strongest wall. The numbers that carry the headline — service time per
stop, parcels per stop, van lease, labour hours — are operational
quantities that appear in **no academic paper**. Downloading more OR theory
does not touch them.

So the correct sources for the top of that list are free reference
documents, not literature:

```
  A  BLS Occupational Employment and Wage Statistics (OEWS) TECHNICAL NOTES
     bls.gov/oes/current/oes_tec.htm  (or the methodology page)
     SETTLES: the 2,080-hours-per-year convention behind the annual mean
     wage. This is the denominator defect — hours = 9 x 6 x 52 = 2,808 in
     cost/params.py:265 against a wage BLS built on 2,080. Worth +26% on
     the headline. The agent could not open the page (proxy); we need the
     convention confirmed in BLS's own words before changing a number
     that large.

  B  BLS Employer Costs for Employee Compensation (ECEC), latest release
     bls.gov/news.release/ecec.toc.htm
     SETTLES: `wage_loading`. We use 1.32; ECEC implies nearer 1.42 for
     private industry, higher for transportation and material moving.
     Alone +5.6%; combined with (A), +33.6%.

  C  ATRI, An Analysis of the Operational Costs of Trucking (latest)
     truckingresearch.org
     SETTLES: the $0.196/mile maintenance figure we cite. CAVEAT ALREADY
     KNOWN: ATRI measures Class 8 tractor-trailers, not delivery vans.
     We may need to discard it rather than cite it.
```

These three are free, are web pages rather than PDFs, and between them
settle more of the headline than items 5-7 combined.

**Already local, no download needed:** `cannibalisation_peak` is set to
0.18 against Holmes's measured ~0.10 (ecta7699.pdf, Table VIII: stand-alone
$41.4M vs incremental $36.3M). We have that file. Checking it is a reading
task, not an acquisition task — and it matters more than any item in
section 1, because at 0.35 the cannibalisation parameter leaves only 38% of
the funded ZIPs unchanged. The portfolio is far less robust than the cost
ranking.

---

## 2. IF YOU CAN — useful, not blocking

```
 10  Fellegi & Holt (1976), "A Systematic Approach to Automatic Edit and
     Imputation", JASA 71(353):17-35
     The original. Winkler RR99-01 (#2) summarises it, so skip if #2
     arrives. Get it if you want the primary citation in the proposal.

 11  "The Five Facets of Data Quality Assessment"      arXiv:2403.00526
 12  "A Survey of Data Quality Measurement and
      Monitoring Tools"                                arXiv:1907.08138
     Both free. Useful only for the "how would you know the data is good"
     question in the viva. Low priority.

 13  Conley (1999), "GMM estimation with cross sectional dependence",
     Journal of Econometrics 92(1):1-45
     Only needed if we go with spatial HAC standard errors. Bootstrapped
     SEs (Train 8.6) are probably sufficient at n=43, so this is a
     contingency.

 14  Simchi-Levi, Kaminsky & Simchi-Levi, Designing and Managing the
     Supply Chain
     Practitioner framing for the network-design chapter. Nice for
     motivation and the literature review; #5 and #6 do the actual work.
```

---

## 3. Explicitly NOT requested, and why

The curriculum the user supplied recommends the BLP demand lineage — Berry
(1994), BLP (1995), Nevo (2000/2001), Berry & Haile (2021), pyblp. **Do not
download these.**

BLP estimates demand from observed market shares and prices. This project has
neither. Our data is households, income, wages, rents, permits and energy
prices; there is not a single transaction in it, and parcels-per-household is
an assumed parameter rather than an estimated quantity. There is nothing for
BLP to be fitted to.

That is roughly half the reading in the supplied curriculum, and skipping it
is not a shortcut — it is the correct call for this project's data.

Likewise the scanner-data price-index material: we have no scanner data. The
useful part of that thread is the statistical-agency *data editing* lineage,
which is item #2 above.

---

## 4. The commitment

Until these arrive, the plan does not change on my say-so. Specifically:

```
  NOT changing cost/depots.py from k-means to p-median until #5 and #6
     are read. I believe the objective mismatch is real and I showed the
     arithmetic, but which formulation replaces it is a choice I should
     make from the survey, not from memory.

  NOT implementing any missingness treatment until #4 is read. Imputing
     under an assumption that turns out to be wrong is worse than the
     listwise deletion we have now, because it would be invisible.

  NOT writing the metrics defence until #9 is read.

  CONTINUING meanwhile: the read-only data-quality audit (measuring is
     not deciding), the conditional choice model from Train which we
     already have, and the documentation backlog.
```

When a paper lands, the changes it licenses get written into
`docs/METHODS_RESEARCH.md` §15, the implemented-versus-documented ledger, with
a citation to the section that licensed them — not before.
