# Acquisition screenshots

Evidence of **which option was selected** on a download page, for sources
whose URL does not identify the file. Kept because
[`../../DATA_SOURCES.md`](../../DATA_SOURCES.md) marks both Zillow entries
`UNVERIFIED` — the registry URL does not match the file that ended up on disk,
and a screenshot of the dropdown is the only record of what was actually
clicked.

These were taken on 2026-09-12 and sat unlabelled in the career folder until
2026-09-16.

---

## `zillow-ZORI_smoothed-all-homes-plus-multifamily_metro-and-US.jpeg`

Zillow Research download page. Visible in the selector at the bottom:

```
  series      ZORI (Smoothed): All Homes Plus Multifamily Time [Series ($)]
  geography   Metro & U.S.
```

## `zillow-ZHVI_all-homes-SFR-condo-coop_raw-mid-tier_metro-and-US.jpeg`

Same page, the ZHVI selector:

```
  series      ZHVI All Homes (SFR, Condo/Co-op) Time Series, [truncated]
  geography   Metro & U.S.
  highlighted ZHVI All Homes (SFR, Condo/Co-op) Time Series, Raw, Mid-Tier ($)
```

Note the highlighted row is the one under the cursor, which is **not**
necessarily the one selected. The committed selection is whatever the closed
box shows, and it is truncated in the capture.

---

## What these do and do not settle

**They confirm the geography.** Both are `Metro & U.S.`, which was not
recorded anywhere else.

**They leave a discrepancy on the ZORI file, and it should not be waved away.**
The files on disk are:

```
  Zip_zori_uc_sfrcondomfr_sm_sa_month.csv
  Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv
```

`sm_sa` means **smoothed AND seasonally adjusted**. The ZORI screenshot shows
`ZORI (Smoothed)` selected — not `ZORI (Smoothed, Seasonally Adjusted)`, which
is a separate row in the same dropdown, visible directly beneath it. Either
the capture was taken before the final selection, or the downloaded file is
not the one the screenshot shows.

Both files are also **ZIP-level** (`Zip_`) while the geography selector reads
`Metro & U.S.`, which points the same way: the capture does not correspond
exactly to the file that was kept.

**So these narrow the ambiguity rather than closing it.** The honest status is
unchanged: `DATA_SOURCES.md`'s `UNVERIFIED` marks on both Zillow entries stay
until someone re-downloads from the page and diffs against the committed file.

It is worth saying that neither Zillow series carries any result in this
project — `rent_index` is 94.3% missing and was dropped, and no headline
figure depends on it. The uncertainty is recorded because it is real, not
because it is load-bearing.

---

## If you are adding a screenshot here

Name it `<source>_<what-was-selected>_<geography>.<ext>` and add a section
above saying what is visible in it and what it does *not* establish. A
screenshot with no caption is a screenshot nobody can use.
