# Research papers

The sources behind the project's methods. Renamed 2026-09-16 from download
IDs (`168125.pdf`, `ecta7699.pdf`, `rr99-04.pdf`) to
`Author-Year_Title_Venue.pdf`, so the folder can be read rather than decoded.

**This folder is not published.** It sits outside the repository. Several of
these are paywalled and one is a scanned textbook.

---

## Facility location and economies of density

| Paper | Where it is used |
|---|---|
| **Hakimi 1964** — Optimum Locations of Switching Centers and Medians of a Graph | The result that an absolute median always lies at a vertex, which is what licenses solving the depot layer over a discrete candidate set. `NOTES_hakimi_1964.md` finds it does **not** license what the project first claimed, and defends the practice with a measured 0.45% instead |
| **Klose & Drexl 2005** — Facility Location Models for Distribution System Design | The p-median family the depot solver belongs to |
| **Holmes 2011** — The Diffusion of Wal-Mart and Economies of Density *(Econometrica)* | Methodological ancestor for density economies in retail expansion |
| **Houde, Newberry & Seim 2017** — Economies of Density in E-Commerce *(NBER w23361, two versions)* | The closest prior work on this operator. Several cost primitives are benchmarked against it |
| **Houde, Newberry & Seim 2023** — Nexus Tax Laws and Economies of Density *(Econometrica)* | The published version. Uses the same industry facility census this project OCR'd |

## Scoring, identification and inference

| Paper | Where it is used |
|---|---|
| **Gneiting & Raftery 2007** — Strictly Proper Scoring Rules *(JASA; two copies, JASA and a JSTOR scan)* | §2.3 p.362, why the project reports raw Brier and raw top-*k* and **never** a skill score |
| **Molinari 2019** — Econometrics with Partial Identification *(cemmap CWP25/19)* | Read while considering a partial-identification approach; not adopted |
| **Kaido, Molinari & Stoye 2019** — Confidence Intervals for Projections of Partially Identified Parameters *(Econometrica)* | Same line of enquiry. `docs/ALTERNATIVES.md` records why it was rejected |

## Data quality, editing and record linkage

| Paper | Where it is used |
|---|---|
| **Fellegi & Holt 1976** — A Systematic Approach to Automatic Edit and Imputation *(JASA)* | The edit-system design behind `E_operating_by` — the rule that falsifies a claimed opening date against an OSHA inspection. Localise the error, do not repair it |
| **Winkler 1999** — State of Record Linkage *(Census RR99-04)* | The linkage practice actually followed. Note `AUDIT_2026_09_14.md` records the Jaro–Winkler code being mis-cited to RR99-**01** when it is governed by RR99-**04** |
| **Winkler 1999** — State of Statistical Data Editing *(Census RR99-01)* | The editing half of the same pair |
| **Rahm & Do 2000** — Data Cleaning: Problems and Current Approaches *(IEEE Data Eng. Bulletin)* | The single- and multi-source taxonomy the cleaning stage is structured on |
| **Van den Broeck et al. 2005** — Data Cleaning: Detecting, Diagnosing and Editing Data Abnormalities *(PLoS Medicine)* | The detect / diagnose / edit discipline, and the requirement to report an uncorrected-vs-corrected cross-tab |
| **Ehrlinger & Wöß 2019** — A Survey of Data Quality Measurement and Monitoring Tools *(arXiv)* | Tooling survey |
| **Mohammed et al. 2024** — The Five Facets of Data Quality Assessment *(arXiv)* | Framing for the quality audit |

## `Train-2009_Discrete-Choice-Methods-with-Simulation_SCANNED-TEXTBOOK/`

Sixteen scanned PDFs — chapters 1–14 plus references and index — of Kenneth
Train, *Discrete Choice Methods with Simulation*, 2nd edition.

The chapters the project actually leans on:

```
  Ch02  Properties of Discrete Choice Models   §2.2, cited for BUILDING the
                                               successor choice set
  Ch03  Logit                                  §3.4 Example 2, the zone-merger
                                               argument for extensive counts
                                               §3.7.1 p.61, the independence
                                               assumption the hazard model broke
  Ch04  GEV                                    why logit's substitution
                                               pattern binds
  Ch08  Numerical Maximization                 the boundary behaviour
  Ch13  Endogeneity                            control function, and why not BLP
```

> **This is a scanned copy of a copyrighted book.** It is kept out of the
> repository for that reason and should not be redistributed. Train has made
> the book freely available on his own website — prefer that copy, and cite
> the book rather than these files.

---

## Two near-duplicates, deliberately kept

- **Gneiting & Raftery 2007** appears twice: the JASA typeset version and a
  JSTOR scan. Not byte-identical. The JASA copy is the one to read; the scan
  has different pagination, which matters because the project cites a page
  number (p.362).
- **Houde, Newberry & Seim** appears three times: NBER w23361, its revision,
  and the published Econometrica version under a different title. The
  published version is the one to cite.

## The one this folder does not contain

**Daganzo (1984)**, the continuous approximation the cost model implements, is
**not here and was never read.** It could not be obtained on the machine where
the project was built. `docs/research/NOTES_daganzo_1984.md` says so in its
first line, and the IEEE paper discloses it rather than citing a paper nobody
opened. The same note records that one of the two citations the code carried
for the central constant is by **Vaughan**, not Daganzo, and supports nothing
in the cost model.

That absence is the most important thing in this folder.
