# collection/satellite — the sixth method, which failed

A negative result, kept on purpose. The parent
[`../README.md`](../README.md) explains why; `docs/data/SATELLITE.md` is the
full write-up.

```
  colab_date_from_satellite.py   a standalone Google Colab notebook -- no API
                                 key, no Earth Engine account, no payment --
                                 that dates construction from free Sentinel-2
                                 imagery
  RUN_THIS.txt                   how to run it
  SITES_TO_DATE.csv              the site list it was pointed at (133 rows)
```

It produced an estimate for **107 of 107** sites and then failed the
`E_operating_by` check on **36%** of them: 39 estimates date construction
*after* an inspector had already found the building operating, a median of 33
months after. A method that answers every question is not thereby a good
method — and the OCR extraction's 94.71% pass rate only means something
because this comparison exists.

Its output is in `data/external/satellite/`, which ships even though the rest
of `data/external/` does not: it cannot be regenerated from this host.
