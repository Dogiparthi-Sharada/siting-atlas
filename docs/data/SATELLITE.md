# Dating facility construction from Sentinel-2 — a negative result

*Attempted 2026-09-13/14. Script `data/collection/satellite/colab_date_from_satellite.py`.
Input `data/collection/satellite/SITES_TO_DATE.csv`, 133 rows. Operating
instructions `data/collection/satellite/RUN_THIS.txt`. Output
`satellite_dates.csv`, 107 rows, produced in Google Colab.*

**This failed. The estimates are not usable as dates and must not be presented
as dates.** This document exists so the next person does not spend an
afternoon rediscovering that, and so the failure is on the record rather than
quietly absent from it.

---

## 0. Where the artefact is

**RESOLVED 2026-09-14, and every figure below re-measured from disk.**

This section used to say the output was not in the repository, that the
figures were reproduced from a measurement taken when the file came back, and
that *"a negative result whose evidence is not archived is one step from an
anecdote"*. That was correct and it has been acted on. The file is now
tracked:

```
  data/external/satellite/satellite_dates.csv   107 rows, 20.9 KB
  data/external/satellite/geocoded.csv          the 107 of 133 that geocoded
```

Both are committed with a `.gitignore` exception, because they **cannot be
regenerated in this repository**: the run needs Microsoft Planetary
Computer's imagery host, which the university proxy blocks. They are
evidence, not derived output, and they are treated like the facility panel
and the NLRB export rather than like anything under `outputs/`.

Re-measured from the tracked file, all six figures reproduce exactly:

```
  rows                          107
  validation set (known year)    83
  within 1 year                 41%
  error standard deviation     3.42 years
  logically impossible        39/107 = 36%
  consistent survivors           68
  impossible rate at conf > 2   35%
```

So §3 and §4 are now VERIFIED rather than reported, and the last figure is
the one to read twice: filtering on high confidence does not reduce the
impossible rate. The score does not discriminate.

## 1. What it was for

Every facility in the panel has an **upper** bound on its opening date and no
lower bound. [`CBP_DETAIL.md`](CBP_DETAIL.md) §5.2 shows how hard that bites:
`open_year` equals the quarter of the earliest OSHA inspection for 104 of 104
national rows, so the panel can say "open by 2019" and never "opened in 2019".
That single gap blocks the lag guard on the warehousing covariate, blocks any
use of time in the choice model, and is what killed the hazard model's event
timing.

Satellite imagery was the cheapest available lower bound. When a delivery
station is built, bare ground becomes a large bright roof and a car park.
Sentinel-2 photographs every point on Earth every five days, free, back to
2015. Upper bound from OSHA plus lower bound from imagery is an **interval**,
and an interval is something the statistics can use.

The design was right. The execution did not work.

## 2. What was actually run

```
  input                 133 sites: 100 from the loaded national panel (all
                        with a known open_year) plus 33 from the first
                        unlabelled OSHA batch (no open_year)
  geocoding             US Census onelineaddress geocoder, free, no key.
                        107 of the 133 matched; industrial addresses geocode
                        badly and a shortfall of that order was expected.
  imagery               Microsoft Planetary Computer STAC, sentinel-2-l2a,
                        2016-01-01 to 2026-09-01, cloud cover < 20%, the least
                        cloudy scene per month
  patch                 240m x 240m around the geocoded point (PATCH_M = 120)
  bands                 B04 (red) and B08 (NIR), median reflectance in the patch
  signal                z(red) - z(ndvi): construction is brighter AND less green
  detector              largest mean shift over all splits in [6, n-6]
  confidence            shift / sd(first differences). A signal-to-noise ratio,
                        never a probability, and the script says so.
  coverage              107 of 107 geocoded sites returned an estimate,
                        median 106 cloud-free scenes each
```

Every one of those choices is defensible in isolation. The script is careful:
it caches per site to Drive so a Colab disconnect costs nothing, it declines to
estimate below 12 scenes, it runs a preflight before anything expensive, and
it builds in its own validation block rather than waiting to be asked for one.
The validation is what caught the failure, which is the system working.

## 3. Validation against the dates we already knew

83 of the 107 have a known opening year. The script estimates them anyway and
compares.

```
  within 1 year of the known year            41%
  standard deviation of the error            3.42 years
```

For a quantity whose whole purpose is to date an event to within a year or so,
a 3.4-year error standard deviation is not a noisy measurement. It is no
measurement. Two out of five inside a year is close to what a uniform guess
over the plausible build-out window would achieve.

`RUN_THIS.txt` anticipated "within 1 year: 71%" as the shape of a successful
run and stated the stopping rule in advance: *"If it cannot recover the dates
we already know, the method is wrong and we throw it away, having lost only
machine time."* The rule was declared before the result and is being honoured.

## 4. The logical test, which is the decisive one

The validation above could be argued with — the "known" opening years are
themselves OSHA-derived upper bounds (§1), so disagreement is not proof of
error on our side.

The logical test cannot be argued with.

> **39 of 107 estimates (36%) date construction AFTER the day OSHA inspected
> the building and found it operating. Median 33 months after.**

These are not imprecise. They are impossible. A building cannot be
photographed under construction three years after a federal inspector stood
inside it. Thirty-six per cent of the output is not merely wrong, it is
incoherent, and it is incoherent against a bound the script was given in its
own input file (`osha_operating_by` is a column of `SITES_TO_DATE.csv`).

**And the confidence score does not separate the impossible from the rest:**

```
  confidence band     share of estimates that are logically impossible
  ---------------     ------------------------------------------------
  > 2                 35%
  1 - 2               30%
```

Higher confidence is very slightly *worse*. Filtering on it changes nothing.
The score is not a bad discriminator; it is not a discriminator.

## 5. Why — the detector, not the imagery

The imagery is fine. A median of 106 cloud-free scenes per site over a decade
is a good series, and 107 of 107 sites produced one. The failure is in
`detect_construction()`, and reading it explains all three symptoms.

```python
    best, best_i = -np.inf, None
    for i in range(6, len(signal) - 6):
        shift = np.nanmean(signal[i:]) - np.nanmean(signal[:i])
        if shift > best:
            best, best_i = shift, i
    resid = np.nanstd(np.diff(signal)) or 1.0
    return {"est_date": d.loc[best_i, "date"],
            "confidence": float(best / resid), ...}
```

Three properties follow directly, and they are consequences of the code rather
than measurements of the output — stated that way so the distinction is clear.

**It cannot return "no change".** Any series of 12 or more points returns a
date. There is no null outcome, no threshold the shift must clear, no test
against the hypothesis that nothing happened. Given a site that was already
built in 2015, the loop returns the argmax of a decade of noise and seasonal
drift, and that argmax is uniform-ish over the interior of the window. Thirty-
six per cent landing after the OSHA date is what that produces.

**The confidence score rewards the failure mode.** `resid` is the standard
deviation of the *first differences* of the signal. A smooth, slowly drifting
series — vegetation growth, a gradual change in the sensor's view angle mix,
a car park that fills over years — has tiny first differences and therefore a
tiny `resid`, so a modest drift divided by a tiny denominator scores **high**.
A genuine step, by contrast, contributes one large first difference and
inflates its own denominator. The score is closer to "how smooth is this
series" than to "how step-like is this series", which is why §4's two bands
are indistinguishable.

**Two channels that move together are one channel.** `z(red) - z(ndvi)` looks
like two pieces of evidence. Red reflectance and NDVI are both dominated by
the same vegetation signal with opposite sign, so subtracting the z-scores
roughly doubles one measurement rather than combining two. Whatever seasonal
or phenological drift is in NDVI is in the combined signal at full strength.

**One hypothesis not tested, and it is not the leading one.** `PATCH_M = 120`
samples 240m on a side around a point from the Census geocoder, which
interpolates along street centrelines. On a rural industrial parcel that point
can sit hundreds of metres from the building, so some patches may not contain
the roof at all. This would produce noise rather than the specific
after-the-inspection bias in §4, so it is a secondary suspect. It could be
checked cheaply by plotting the patch against imagery for ten sites.

## 6. What must not be done with the output

**The 68 estimates that survive the logical test must not be presented as
dates.** This is the single most important sentence in this document.

Selecting them is **selecting on the outcome**. The test that keeps them is
"the estimate is earlier than the OSHA inspection", and the OSHA inspection is
the upper bound we were trying to complement. So the surviving set is, by
construction, the set that agrees with the bound we already had — which means
it carries no independent information about the opening date and is guaranteed
to look consistent with OSHA no matter how bad the underlying estimator is.

Concretely, a reader shown "68 facilities dated by satellite, all consistent
with the OSHA record" would reasonably conclude the method works. It is the
same 36%-broken estimator with the visibly broken third deleted. The remaining
64% has a 3.42-year error standard deviation and no reason to be better than
the part that was removed.

The same argument rules out the two obvious softenings:

```
  "report only the high-confidence ones"        sec.4: the score does not
                                                discriminate. 35% impossible
                                                above conf 2 against 30%
                                                between 1 and 2.
  "report them as a lower bound with a wide     a lower bound that is wrong
   interval"                                    in the wrong direction 36% of
                                                the time is not a bound.
```

The honest use of this output is as evidence that the method as implemented
does not work. That is what it is used for here.

## 7. What would make a second attempt worth running

Not a longer run. The imagery is not the constraint and 107 sites is enough to
show a working method working.

```
  1  A NULL OUTCOME.  The detector must be allowed to say "no change in this
     window".  Test the best split against a permutation null on the same
     series and return None when it does not clear it.  This alone should
     remove most of the 36%, because most of those sites were already built
     before Sentinel-2 began.
  2  USE THE BOUND AS A CONSTRAINT, NOT AS A MARKER.  osha_operating_by is
     already in the input.  Restrict the candidate splits to dates before it.
     The estimator then cannot produce an impossible answer, and the
     validation in sec.3 becomes the only test -- which is the correct
     situation, because sec.4 currently absorbs all the attention that
     sec.3's 41% deserves.
  3  A CONFIDENCE SCORE THAT MEASURES STEPNESS.  Compare the fitted step
     against a linear trend on the same series, not against the smoothness
     of the series.  Any score whose denominator falls as the series gets
     smoother will keep making this mistake.
  4  SEPARATE THE TWO BANDS.  Report red and NDVI shifts independently and
     require them to agree in sign and roughly in date.  Two channels that
     must corroborate is a real test; two channels summed is one channel.
  5  CHECK THE PATCHES.  Ten sites, plotted, before anything else is run.
```

If (1) and (2) are done and the validation in §3 still shows 41% within a
year, the method should be abandoned rather than tuned further. The
alternatives — industrial REIT property schedules, county building permits —
are named in [`ACQUISITION_GUIDE.md`](ACQUISITION_GUIDE.md) and are slower but
give an actual date.

## 8. What it cost, for the record

Four hours of Colab time and an afternoon of code. No money, no credentials,
no data licence. It returned a clear negative with a declared stopping rule,
an internal validation that caught its own failure, and a logical test that
made the failure undeniable. That is a cheap experiment that worked as an
experiment and failed as a measurement, and those are different things.

## 9. Related

- [`CBP_DETAIL.md`](CBP_DETAIL.md) §5 — the lag guard this was meant to repair.
- [`FACILITY_PANEL_PROVENANCE.md`](FACILITY_PANEL_PROVENANCE.md) — where `open_year` comes from and why it is an upper bound.
- [`ACQUISITION_GUIDE.md`](ACQUISITION_GUIDE.md) — the remaining routes to a real opening date.
