# Errata — pre-registration of the metro-level entry model

**Corrections to [`PREREG_METRO_MODEL.md`](PREREG_METRO_MODEL.md), issued
2026-09-15 AFTER the model was fitted.**

---

## Why this is a separate file

Four of the figures and supporting claims the pre-registration quotes as
*motivation* were wrong or under-labelled. Three of them were briefly
corrected in the pre-registration itself and then reverted, because that edit
broke the file's seal:

```
  PREREG_METRO_MODEL.md          md5 946f7ef75db69e5278eea409a04c3823
  metro_entry.json  prereg_md5   md5 946f7ef75db69e5278eea409a04c3823
```

A pre-registration's entire value is that it can be shown not to have moved.
`outputs/metrics/metro_entry.json` records that hash, so anyone can re-hash
the file and confirm the hypothesis was fixed before the result was known. An
in-file correction — however honestly flagged — destroys that check, and a
reader then has only our word for what the document said beforehand.

So the pre-registration is byte-identical to the version that was sealed at
15:49 on 2026-09-15, and every correction lives here instead.

**None of these corrections touches a pre-registered clause.** The question
(§1), hypothesis (§2), sample (§3), covariates (§4), baselines (§5),
evaluation (§6), outcome texts (§7), invalidation conditions (§8) and success
criterion (§9) are exactly as registered. All four errors are in figures and
supporting claims quoted to *motivate* the design, not in the design itself.
The verdict — **H0** — is unaffected.

| | Correction | Where |
|---|---|---|
| 1 | "0.72 points worse" does not name its stratum, and is −0.62 on the completed run | preamble |
| 2 | the dispersion rule is asymmetric, not two-way | §2 |
| 3 | the densification range mixes two axes | §4 |
| 4 | the bootstrap-vs-re-split direction is problem-specific | §6 |

---

## Correction 1 — the "0.72 points worse" figure does not name its stratum

**Preamble, as registered:** *"an honest nested forward selection, choosing
covariates inside each training fold, came out **0.72 points WORSE** than
adding nothing"*.

**The problem.** The figure reproduces, but only for the **large-metro top-10
hit rate**. Pooled, the same comparison goes the *other way*.

From the completed re-run of `covariate_search.json` (687 facilities, `core`
frame of 477 decisions, 191 held out) → `core.arms["forward (nested, honest)"]`:

```
  large-metro top-10   30.473%  ->  29.852%   = -0.6201 pp
                       50 re-splits, 5 wins / 19 ties / 26 losses

  pooled               52.419%  ->  52.775%   = +0.3560 pp  BETTER
```

Unqualified, "0.72 points worse" is contradicted by a number in the same block
of the same artefact. **The motivating argument survives** — selection inside
the fold bought nothing and cost something in the stratum that matters — but
it is a stratum-specific result, not a global one.

**The magnitude has since settled — the correct figure is −0.62 pp, not
−0.72.** This note originally marked the number provisional because
`covariate_search.json` was being regenerated as it was written, and quoted
the superseded copy's 31.172% → 30.452% (−0.7203 pp, 3/17/30) with a pooled
contrast of +0.08 pp. That re-run has completed on the current 687-facility
frame and the block above is read from it:

```
  large-metro top-10   -0.6201 pp
  run_id               20260915-235210-ff92
```

The sign, the stratum-specificity and the pooled contradiction all survive —
the pooled gap in fact widened, from +0.08 pp to +0.36 pp. The large-metro
magnitude moved by a tenth of a point.

**Two things the re-run also settled.** It removed an internal contradiction —
the previous artefact reported 694 facilities in some stages and 687 in
others; the file now reads 687 throughout, with no occurrence of 694. And it
exposed a live defect: **this emitter reuses the same `run_id` across
successive writes**, and stamps `written_at` at first write rather than last,
so two materially different versions of the file carried an identical stamp.
The figure above is from the completed run. Anything quoting this artefact
should check `facilities: 687` is present before trusting it.

---

## Correction 2 — the dispersion rule is asymmetric, not two-way

**As registered, in §2:**

```
  cv below 0.6   ->  coefficient lands on the boundary   21 of 21
  cv above 1.3   ->  coefficient is interior             21 of 21
  nothing in between
```

**The problem.** That is a symmetric two-way rule, and it is not what the
artefact shows. It also reads as 42 observations when there are 21.

Re-derived from `gravity_network.json` (`run_id 20260915-210603-b780`,
`terms.dispersion` at vintage 2030, 41 large metros, 8,271 candidate ZCTAs),
checked against `arms.<arm>.verdicts.<col>.state` for all 21 terms:

```
  cv < 0.6      7 terms (0.2975 - 0.5918)    0 of 7 interior
  0.6 - 1.3     0 terms                      the band is empty
  cv > 1.3     14 terms (1.3993 - 8.5046)    9 of 14 interior
```

The five high-cv terms that are *not* interior are all sortation-side
(`sortation_proximity`, `sortation_gravity_sqft_a2`,
`sortation_gravity_count_sqft_subset_a2`, `sortation_gravity_sqft_a3`,
`sortation_gravity_count_sqft_subset_a3`), four of them carrying square
footage.

**The corrected rule is asymmetric:**

> Low within-metro dispersion is **sufficient for failure**.
> High dispersion is **necessary but not sufficient for success**.

And it is **descriptive, not estimated**. n = 21 terms that are not
independent — each is one of two columns in one of 13 arms fitted over the
same 483 decisions — from one run at one vintage. Nothing was observed between
cv 0.6 and 1.3, so the finding is silent about intermediate dispersion.

**Effect on H1.** It weakens the motivating mechanism without reversing it.
The claim that county-grain covariates cannot rank ZIPs within a metro is
unaffected; what weakens is the inference that high-dispersion columns would
therefore work at metro grain. As it turned out, they did not — so this
correction runs *against* the registered hypothesis, not in its favour.

---

## Correction 3 — the densification range mixes two axes

**As registered, in §4:** *"67-77% of 2024-25 openings landed inside coverage
that already existed"*.

**The problem.** That range combines figures from different radii *and*
different coordinate sets. At the headline radius of 45.0 miles the correct
range is **68.7% – 75.9%**, varying across coordinate sets:

```
  75.9%  =  60 of  79 openings with real Census coordinates
  68.7%  =  90 of 131 openings including ZCTA-centroid fallbacks
```

67.1% is the real-coordinate figure at **15** miles — a different radius.
Across the full radius × coordinate-set grid the value runs from 45.0%
(fallback, 8.3 mi) to 75.9% (real, 45 mi).

The regularity is unchanged. The range was being quoted wider and looser than
the artefact supports.

---

## Correction 4 — the bootstrap-vs-re-split direction is problem-specific

**As registered, in §6:** *"a metro-clustered bootstrap came out 24-28% WIDER
than the re-split spread on more data (`outputs/metrics/network_inference.json`)."*

**The problem.** That measurement was taken on the **ZIP-level** problem. On
the **metro-level** problem this pre-registration is actually about,
[`research/NOTES_METRO_ENTRY.md`](research/NOTES_METRO_ENTRY.md) §7 measures
the clustered bootstrap as roughly **31% narrower**, not wider.

So the *direction* does not transfer between the two problems, and the
pre-registration generalised from one to the other without saying so.

**The rule it was invoked to support is unaffected**, and it is the part worth
keeping:

> A percentile spread across re-splits is not a standard error.

Re-splits resample the same fixed set of decisions; a clustered bootstrap
resamples the clusters. They answer different questions, so there is no reason
for them to agree in magnitude *or* in which is wider — which is exactly what
these two measurements demonstrate between them. Quote whichever you actually
computed, on the problem you computed it on, and never substitute one for the
other.

**Effect on H1.** None. §6 uses this only to justify reporting a clustered
bootstrap alongside the re-split spread, which is what the run did.

---

## Note — three artefact paths inside the sealed file are now stale

The pre-registration cites three artefacts at paths that have since moved:

```
  outputs/metrics/gravity_network.json    -> experiments/gravity-network/artefacts/
  outputs/metrics/network_inference.json  -> experiments/gravity-network/artefacts/
  outputs/metrics/hazard_revival.json     -> experiments/hazard-model/artefacts/
```

They were relocated on 2026-09-15 when the hazard and gravity lines of work
were retired to `experiments/`. **The paths in the sealed file were
deliberately left wrong**, because correcting them would change the file and
break the hash — which is exactly what happened once already, when a
repo-wide path sweep caught this document and had to be reverted.

A pre-registration records what was true when it was written. Stale paths in
it are a feature of that, not a defect. The files themselves are unchanged;
only their location moved, and the `run_id` in each is unaltered.

**If you are running an automated edit across `docs/`, exclude
`PREREG_METRO_MODEL.md`.** A sealed copy and its hash are kept at
`reproducibility/seals/` so a break can be reverted in one command, and CI
checks the seal on every push.

---

## What did not change

For the avoidance of doubt, and because this is the part that matters:

| Section | Status |
|---|---|
| §1 The question | unchanged |
| §2 Hypothesis H1 / H0 | unchanged (only a motivating figure was wrong) |
| §3 Sample | unchanged |
| §4 Covariates | unchanged (only a motivating figure was wrong) |
| §5 Model and baselines | unchanged |
| §6 Evaluation | unchanged |
| §7 Both outcome texts | unchanged |
| §8 Invalidation conditions | unchanged |
| §9 Success criterion | unchanged |

The result stands as reported: **H0**. The metro model lost to "rank by
households" in 0 of 7 held-out years.

See [`research/NOTES_METRO_ENTRY.md`](research/NOTES_METRO_ENTRY.md) for the
run itself, including its own §12, *"Where I think the prereg is wrong"*,
written after the result.
