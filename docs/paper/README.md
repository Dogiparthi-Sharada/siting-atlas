# `paper/` — IEEE conference paper

## STATUS: DRAFT. NOT SUBMITTED. NOT PEER REVIEWED.

This directory holds a working draft of a conference paper reporting the
Siting Atlas measurements. **It has not been submitted anywhere, it has not
been reviewed, and it is published here before submission as part of an open
repository.** Do not cite it as a publication. Do not quote a number from it
without checking that number against [`../docs/NUMBERS.md`](../docs/NUMBERS.md),
which is the project's tie-breaker and outranks this draft.

The author block is a placeholder (`[Author]`, `[Institution]`, `[email]`).
No funder is named because none is claimed.

---

## What the paper is

A **measurement paper**, not a paper claiming a successful predictor. Its
argument in one paragraph:

> A pre-registered attempt to predict a private operator's facility siting
> from free public data fails at both geographic grains tested — 0 of 7
> held-out years against a "rank metros by households" baseline. The failure
> has a diagnosis that generalises: most US public data is published at county
> grain or is population under another name, and a within-metro conditional
> choice model can use neither. Alongside the nulls sit a measured floor on
> public visibility (OSHA holds a record in 138 of the 488 cities where an
> independent census lists a delivery station), a recovered dataset of 1,904
> facilities OCR'd from an image-only industry document, and a parcel-level
> cost model that does work on an observed depot layer — the operator's 501
> real delivery stations rather than a solved network — and prices the
> difference: +5.2% on the median parcel and a doubling of line haul.

The methodological contribution is the pre-registration itself. The
hypothesis, sample, covariates, baselines, metrics and numeric success
criterion were fixed and hashed before any model was fitted; the MD5 is
recorded in the result artefact and can be re-verified.

---

## Files

| File | What it is |
|---|---|
| `siting_atlas_ieee.tex` | The paper. IEEEtran, `conference` option, two-column. The real deliverable. |
| `refs.bib` | BibTeX. The machine-readable twin of the paper's bibliography. |
| `README.md` | This file. |

There are no `.txt` twins and no generated PDFs in version control.

---

## How to compile

```bash
cd paper
pdflatex siting_atlas_ieee.tex
pdflatex siting_atlas_ieee.tex     # second pass for cross-references
```

**No `bibtex` pass is required.** The bibliography is inlined as a
`thebibliography` environment at the end of the `.tex`, so the paper compiles
on a minimal TeX installation that may not ship `IEEEtran.bst`.

### Requirements

* The `IEEEtran` document class. It is in `texlive-publishers` on Debian/Ubuntu
  (`apt install texlive-publishers`), in `collection-publishers` under `tlmgr`,
  and is bundled with MacTeX and MikTeX. If you cannot install it, the paper
  will compile with `\documentclass[twocolumn]{article}` after deleting the
  `\IEEEauthorblockN` / `\IEEEauthorblockA` / `\IEEEPARstart` / `IEEEkeywords`
  markup — the content is unaffected, only the layout is.
* Packages: `graphicx`, `url`, `amsmath`. All three are in
  `texlive-latex-base` / `texlive-latex-recommended`. **Nothing exotic is
  used**, deliberately.

### Figures and tables

The paper has **four figures and five numbered tables.**

All four figures live in `../docs/figures/` and are reached via
`\graphicspath`. Each is built by `tools/figures/fig_paper.py`, each reads
every value it draws from a repository artefact at build time, and each is
**drawn at 3.40in — the IEEE single-column width — so the document never
scales it.**

| Figure | File | What it shows | Read from |
|---|---|---|---|
| Fig. 1 | `fig_visibility_gap.png` | 138 of 488 cities: the public-visibility floor | `outputs/metrics/mwpvl_coverage.json` |
| Fig. 2 | `fig_metro_auc.png` | out-of-time AUC by held-out year, model vs households baseline | `outputs/metrics/metro_entry.json` |
| Fig. 3 | `fig_dispersion.png` | within-metro cv against interior/boundary, and the empty band | `experiments/gravity-network/artefacts/gravity_network.json` |
| Fig. 4 | `fig_cost_by_metro.png` | median and IQR cost per parcel by metro | `outputs/tables/cost_to_serve_2023q4_baseline.parquet` — **still the retired pilot table.** `tools/figures/fig_paper.py` has not been repointed at `cost_to_serve_station_2023q4_baseline.parquet`, and the caption now says so |

| Table | What it shows |
|---|---|
| I | the visibility gap, as counted (488 / 340 / 138 / 350 / 28.3%) |
| II | out-of-time AUC by held-out year, verdict arm |
| III | within-metro dispersion against coefficient state, 21 network terms |
| IV | the 2023 Q4 baseline cost model on the observed depot layer |
| V | what replacing the solved depot network with the observed one costs |

Two further in-column displays — the OCR extraction counts and the assembled
panel's composition — are deliberately left as unnumbered `center` blocks.
They are dataset inventories the surrounding prose walks through line by line,
not results a reviewer needs to refer back to by number.

Rebuild the figures from the repository root with:

```bash
python tools/figures/fig_paper.py
```

If you compile from a directory where the relative paths do not resolve, copy
the four PNGs into `paper/` — `\graphicspath` already includes `./`.

**Two figures the paper does not use, and why.**
`../docs/figures/fig_cost_per_parcel_by_metro.png` shows the same data as Fig. 4 but
is drawn 8.97in wide for the repository README; in a 3.40in column it would be
shown at 37% and its labels would reach the page at about 3pt.
`../outputs/figures/cost_vs_density_2023q4_baseline.png` is drawn 7.41in wide
and would be shown at 46%, putting its tick labels near 4.6pt — below the
6.5pt floor that `tools/figures/figbase.py` enforces on everything else here.
Its point, that cost falls as 1/√δ onto a fixed-cost floor, is stated
algebraically in the text. Both were drawn from the retired pilot table and
would need regenerating before reuse.

**No figure in this paper contains a hand-typed value.** That rule exists
because this project previously shipped a decay curve with nine hand-entered
numbers and a fabricated 95% confidence band; it was caught in self-audit and
is disclosed in the paper's Threats to Validity section.

---

## Numbers policy

Every figure in the paper is traceable to one of:

* an artefact under `outputs/metrics/`, `outputs/tables/` or
  `experiments/*/artefacts/`, named in the text with its `run_id` where the
  artefact carries one; or
* a re-derivation from a committed data file, stated as such at the point of
  use.

Two quantities in the paper are re-derived rather than read from a JSON
artefact, and the paper says so both times:

1. The stops-per-square-mile densities used to defend the 15-mile catchment
   (350 for the costed set against 475 for the retired pilot) are recomputed
   from `outputs/tables/cost_to_serve_station_2023q4_baseline.parquet` and
   `outputs/tables/cost_to_serve_2023q4_baseline.parquet`. Every other density
   in the paper comes from `cost_by_station.json` directly.
2. The pilot column of the depot-swap table is read from
   `cost_by_station.json`'s `pilot_comparison` block, which re-reads the
   retired pilot parquet at run time; `cost_report.json`
   (`20260916-064133-4d65`) holds the same figures independently and the two
   agree.

**Withdrawn, and the withdrawal is deliberate.** The paper used to carry a
test reading *"zero of 43 pilot facilities sit in the cheapest decile of their
own metro"*, re-derived by joining `facilities.csv` to the pilot cost parquet
on ZIP. **That statistic is gone from the paper and must not be reinstated.**
Once the cost model's depots became the operator's real stations, the test
stopped being identified — a ZCTA containing a station has a line haul of ~0
because the station is inside it — and the leave-one-out repair gives 6.9% on
the 501 stations against 16.3% on the original 43, straddling the 10% chance
rate in opposite directions. The paper now argues *feasibility binds before
economics* from the `1/√δ` form of the cost function instead. `docs/NUMBERS.md`
§10.4 records the withdrawal; the paper's Threats section carries it as a
limitation in its own right.

If the paper and `docs/NUMBERS.md` ever disagree, **`docs/NUMBERS.md` is
right and the paper is wrong.**

---

## Things a reader should know before relying on this draft

* **`refs.bib` and the inlined bibliography must be kept in sync by hand.**
  There is no check for this. If you edit one, edit the other.
* **Two references are marked `[K]`** — cited from knowledge, with
  bibliographic details not confirmed against a source: Beardwood, Halton &
  Hammersley (1959) and Fellegi & Sunter (1969). These must be checked before
  submission; the marks appear in both the `.tex` and `refs.bib`.
* **Three references are marked `[T]`** — title and venue verified against a
  publisher or repository record, contents not read: both Daganzo 1984 papers
  and Vaughan (1984).
* **One cited paper was not read.** Daganzo (1984), *Transportation Science*
  18(4), is the source of the cost model's structure and could not be obtained
  on the host this project was built on. The paper says so explicitly in
  Related Work and in `refs.bib`, cites it only for the structure the code
  implements, and quotes no page number or section from it. See
  `../docs/research/NOTES_daganzo_1984.md`, whose first line is the warning.
* **`../docs/PREREG_METRO_MODEL.md` must never be edited.** Its MD5
  (`946f7ef75db69e5278eea409a04c3823`) is checked by CI and recorded inside
  `outputs/metrics/metro_entry.json`. Corrections go in
  `../docs/PREREG_METRO_MODEL_ERRATA.md`, and the paper reflects all three of
  them — including the one that runs *against* the registered hypothesis.

---

## Licence

Same as the repository: MIT. See `../LICENSE`. `../TRADEMARKS.md` applies to
the naming of any third party discussed in the text.
