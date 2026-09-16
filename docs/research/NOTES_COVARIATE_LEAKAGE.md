# The warehousing covariate probably contains its own outcome

*Measured 2026-09-14, after MWPVL's opening dates made the test possible for
the first time. `src/siting_atlas/models/leakage_test.py`,
`outputs/metrics/leakage_test.json`.*

This is the most serious finding about the prediction model to date, and it
was not findable before today. It does not say the model is wrong. It says the
headline result cannot be defended until one specific test is run, and that
test only became possible this morning.

---

## 1. The claim, in one line

The choice model's one working covariate counts warehouses in a ZCTA. An
Amazon delivery station **is** a warehouse. The guard that was supposed to
stop a facility being counted in its own predictor is calibrated against a
date that is, measurably, about three years too late.

## 2. The covariate is load-bearing, so this matters

An ablation over 50 re-splits, refitting inside each repeat. **The two arms
are not the same decisions**, and that has to travel with the numbers:

```
                       decisions   top-10 hits   of    Brier      uniform null
  with warehousing            94         20.60   38   0.007550        5.60
  without warehousing        100         12.90   40   0.008018        6.32

  difference  +7.70 hits (sd 3.20)
  with-covariate wins 50, loses 0, ties 0
```

`leakage_test.json` (`20260915-195832-4275`) records `n_decisions` 94 and
**100**. The gap is the CBP lag guard: the `with_warehousing` arm needs a CBP
vintage strictly earlier than each facility's `open_year` and drops the 6
facilities that have none, while `without_warehousing` is built with `cbp =
None` and so keeps all 100. *This section said "50 paired re-splits of the
same 94 decisions" until 2026-09-16. The re-splits share a seed but not a
frame, so "+7.70 of 38" is a difference between two arms scored on different
test sets, not a paired difference on one.* As rates the comparison is
20.60/38 = **54.2%** against 12.90/40 = **32.3%**, over uniform nulls of 14.7%
and 15.8% — which is the same conclusion, and the right way to state it.

Removing `warehousing_establishments` costs roughly **22 points of top-10 hit
rate** and wins every split. For comparison, the entire spread between the
conditional logit, a
zero-parameter warehouse count and a 200-tree GBM is 1.7 hits
([`NOTES_GBM_BENCHMARK.md`](NOTES_GBM_BENCHMARK.md)). The choice of model is
worth a fifth of what this one column is worth.

Two things follow. The residual 12.90 against a uniform null of 6.32 says the
other covariates are not empty — roughly twice the null. And the model is
nevertheless mostly this column, so if this column is contaminated, so is the
result.

## 3. The guard, and the measurement that defeats it

`cbp_detail.py` refuses any CBP vintage not strictly earlier than a facility's
`open_year`, and drops the facility when none exists — 6 of 104 on the last
run. That is a real guard, not a nominal one, and the earlier description of
it as "nominal" in `CBP_DETAIL.md` §5 understated it.

The problem is what `open_year` is. It is the quarter of the **earliest OSHA
inspection**, for 104 of 104 national rows. An inspection proves the building
was already operating, so the date is an **upper bound** and the true opening
is earlier by an unknown amount.

Until today the amount was unknown. MWPVL's tables state opening months
outright, and 42 of them link to a building with an OSHA inspection:

```
  months between the true opening and the first OSHA inspection, n = 42

     median  34        mean  38        p25  19    p75  54    max  89

     gap >  0 months    41 of 42   98%
     gap > 12 months    37 of 42   88%
     gap > 24 months    26 of 42   62%
     gap > 36 months    20 of 42   48%
```

**The bound is about three years late, at the median.** So a guard that
demands a CBP vintage earlier than `open_year` typically selects a vintage
one or two years before the inspection — which is still one or two years
*after* the building opened. The facility is in its own covariate, and the
guard reports success.

This is not a bug in the guard. The guard enforces exactly what it was asked
to enforce. It was asked the wrong question, because the right one needed a
date nobody had.

## 4. What this does NOT establish

**An ablation cannot prove contamination.** Warehouses cluster near
warehouses. A ZCTA with many warehouses in 2018 is a ZCTA where the eleventh
warehouse arrives in 2020, whether or not the eleventh was counted in the
2018 figure. Genuine agglomeration and self-counting make the same prediction,
and no amount of removing the column separates them.

So §2 and §3 together say: the covariate carries the result, and the
mechanism protecting it from circularity does not work at the measured lag.
They do not say the number is wrong. They say it is **unaudited**, which for
a headline result is a different kind of problem from being wrong and not
obviously a smaller one.

## 5. The decisive test, now possible

> **Corrected 2026-09-14, evening — the figures in this section moved, and the
> test has since been run.**
>
> This section was written in the morning and cited *"446 [dates] arrived
> 2026-09-14 from MWPVL, validated at 97.2% against the OSHA bound and 99.8%
> against the network's 2013 start date"*. Both figures were correct for the
> OCR run that existed when it was written — two of MWPVL's thirteen table
> images, 591 facilities. **All thirteen were parsed the same afternoon.**
> From `outputs/metrics/mwpvl_validation.json`:
>
> ```
>                                    WAS            IS
>   dates recovered                  446          1,420
>   linked to an OSHA building        36            208
>   pass rate vs the OSHA bound     97.2%         94.71%
>   plausible (all checks)             -           99.5%   (1,413 of 1,420)
>   at or after the 2013 start      99.8%          99.7%   (788 of 790 DS rows)
> ```
>
> *(IS column refreshed 2026-09-15 from `mwpvl_validation.json` run
> `20260915-195247-dbb5`. It read 157 linked / 93.6% when this block was
> written; the linked denominator has grown again since.)*
>
> **The pass rate fell because the denominator grew, not because the dates got
> worse.** 97.2% of 36 linked rows is 35 rows surviving the bound; 94.71% of 208
> is 197. Nearly six times as many dates are now tested and nearly six times as
> many survive. Reading 97.2% -> 94.71% as a decline is the error this block
> exists to prevent.
>
> **And the test below has been run.** `outputs/metrics/leakage_decisive.json`
> exists, on 29 facilities carrying both an OSHA bound and an MWPVL-vouched
> true date. Its result is written up in
> [`NOTES_LEAKAGE_DECISIVE.md`](NOTES_LEAKAGE_DECISIVE.md) and is not restated
> here — that document owns it. The sentence at the end of this section,
> *"do not quote the prediction results as settled until this is run"*, is left
> standing as the condition it was, now met.

Refit using, for each facility, a CBP vintage strictly earlier than its **true**
opening date rather than its OSHA bound.

```
  needs      real opening dates        1,420 arrived 2026-09-14 from MWPVL,
                                         validated at 94.71% against the OSHA
                                         bound (208 rows link to a building)
                                         and 99.7% against the network's
                                         2013 start date (2 of 790 dated
                                         delivery-station rows precede it);
                                         99.5% of all 1,420 are chronologically
                                         plausible
  costs      the facilities whose true opening precedes the earliest usable
             CBP vintage (2017) are dropped; at a 38-month median lag that is
             a real sample loss and must be reported, not absorbed
  decides    if the covariate still predicts on strictly pre-opening vintages,
             it is agglomeration and the result stands
             if it collapses toward the 12.90 of the ablation, it was
             substantially self-counting
```

Either outcome is worth having. A confirmed result gains an audit it currently
lacks; a collapsed one is a finding about method that is more interesting than
the prediction was.

**Do not quote the prediction results as settled until this is run.**

## 6. Why this was worth finding

The GBM benchmark was commissioned to answer a different question — data
ceiling or model ceiling — and answered it (data ceiling, with a ~1-decision
model term). The leakage risk was a caveat in its report that it explicitly
did not test. Chasing the caveat rather than the headline is what produced
this.

It also changes what the MWPVL extraction is *for*. It was pursued to unblock
before-and-after designs and the thirteen undated facilities. Its first real
use is auditing a covariate that has been in the model for months.

## 7. Related

- [`NOTES_GBM_BENCHMARK.md`](NOTES_GBM_BENCHMARK.md) — the caveat this came from; 53.5% of GBM split gain sits on this column.
- [`../data/CBP_DETAIL.md`](../data/CBP_DETAIL.md) §5 — the lag guard, and the `open_year` provenance that defeats it.
- [`../data/MWPVL_2025.md`](../data/MWPVL_2025.md) — where the true dates came from.
- [`../data/SATELLITE.md`](../data/SATELLITE.md) — the failed earlier attempt at those dates, and why this one is tested to the same standard.
