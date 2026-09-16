# data/external/satellite — output of a method that failed

Two small CSVs, both tracked, both **evidence for a documented negative
result** rather than an input to any model.

```
  satellite_dates.csv   107 rows   construction dates estimated from free
                                   Sentinel-2 imagery
  geocoded.csv          133 rows   the coordinates those estimates were
                                   made at
```

## Why these ship when the rest of `external/` does not

They are **not reproducible from this repository**. They came from a Google
Colab run against the Microsoft Planetary Computer, whose imagery host the
university proxy blocks. Re-running the notebook here returns nothing, so the
output is the only surviving record of what the method did.

## What it did

Produced an estimate for **107 of 107** sites, and then failed the OSHA
`E_operating_by` check on **36%** of them: 39 estimates date construction
*after* an inspector had already found the building operating, a median of 33
months after. A method with 100% answer coverage and a 36% falsification rate
is the counter-example the OCR extraction's 94.71% pass rate is measured
against.

The notebook that produced them is
[`../../collection/satellite/`](../../collection/satellite/); the write-up is
[`../../../docs/data/SATELLITE.md`](../../../docs/data/SATELLITE.md).
