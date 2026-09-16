"""The covariate search over the panel's unused columns.

Its verdict — that no unused panel column moves held-out accuracy, for two
structural reasons — rests on four mechanics that would be wrong silently.

1. Every arm must be a COLUMN SUBSET OF ONE FRAME. If `columns_only`
   reordered rows, or let a non-numeraire column lead, the arms would be
   scored on different data or fitted with the wrong coefficient pinned,
   and the paired difference would stop being about the column.
2. The positive transforms must actually be positive and must be strictly
   monotone in their source. `beta'a` must be positive for every
   alternative or the probability is undefined, and a transform that is
   not monotone would be a different variable rather than a re-expression.
3. Selection must not see the test fold. `forward_select` is handed the
   training decisions only; a bug that let it see more would manufacture
   the gain the whole file exists to measure honestly.
4. The grain audit must detect a county-grain column, because that
   detection IS the headline finding.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from siting_atlas.models import covariate_audit as audit
from siting_atlas.models import covariate_frame as cf
from siting_atlas.models import covariate_harness as harness
from siting_atlas.models.choice import ChoiceData


def _data(n_decisions: int = 12, seed: int = 7) -> ChoiceData:
    rng = np.random.default_rng(seed)
    names = ("households", "land_area_sqmi", "establishments",
             "warehousing_establishments", "median_home_value")
    blocks, groups, chosen, offset = [], [], [], 0
    for g in range(n_decisions):
        n = int(rng.integers(10, 20))
        blocks.append(rng.lognormal(0.0, 1.0, size=(n, len(names))))
        groups.append(np.full(n, g))
        chosen.append(offset + int(rng.integers(n)))
        offset += n
    return ChoiceData(np.vstack(blocks), np.concatenate(groups),
                      np.array(chosen),
                      [str(i) for i in range(n_decisions)], names)


# ---------------------------------------------------------------------------
# columns_only


def test_columns_only_selects_the_named_columns_and_keeps_row_order():
    d = _data()
    keep = ("households", "establishments")
    out = cf.columns_only(d, keep)
    assert out.names == keep
    assert np.array_equal(out.a[:, 0], d.a[:, 0])
    assert np.array_equal(out.a[:, 1], d.a[:, 2])
    # Same decisions, same alternatives, same chosen rows: an arm is a view
    # of one frame, never a re-built frame.
    assert np.array_equal(out.group, d.group)
    assert np.array_equal(out.chosen, d.chosen)


def test_columns_only_rejects_a_list_not_led_by_the_numeraire():
    # `choice._probabilities` pins beta[0] = 1 BY POSITION. A column list
    # that does not lead with households would silently fix the wrong
    # coefficient and every reported ratio would be to the wrong thing.
    with pytest.raises(ValueError, match="households"):
        cf.columns_only(_data(), ("establishments", "households"))


# ---------------------------------------------------------------------------
# the positive transforms


def test_permits_growth_ratio_is_positive_and_monotone_in_the_percentage():
    pct = np.array([-90.0, -50.0, -1.0, 0.0, 1.0, 50.0, 900.0])
    frame = pd.DataFrame({"zcta": [f"{i:05d}" for i in range(len(pct))],
                          "permits_yoy_pct": pct})
    out = cf._derive_varying(frame, ("permits_yoy_ratio",))
    ratio = out["permits_yoy_ratio"].to_numpy()
    assert (ratio > 0).all()
    assert np.all(np.diff(ratio) > 0)          # strictly increasing in pct
    assert ratio[3] == pytest.approx(1.0)      # 0% growth is a ratio of 1


def test_permits_ratio_of_exactly_minus_one_hundred_percent_is_dropped():
    # Permits went to zero, so the ratio is 0 and neither it nor its
    # reciprocal exists. The row must LEAVE, not be floored at some small
    # number, because a floor is an imputation.
    frame = pd.DataFrame({"zcta": ["00001", "00002"],
                          "permits_yoy_pct": [-100.0, 25.0]})
    out = cf._derive_varying(frame, ("permits_yoy_ratio",
                                     "inv_permits_yoy_ratio"))
    assert out["zcta"].tolist() == ["00002"]


def test_reciprocal_is_decreasing_in_its_source():
    # The reciprocal exists so a REPELLENT column can be expressed under
    # `choice.py`'s beta = exp(theta) > 0. It must therefore rank the
    # alternatives in the opposite order to the level.
    panel = pd.DataFrame({
        "zcta": ["00001", "00002", "00003"],
        "cbsa_code": ["10000"] * 3,
        "households": [10.0, 20.0, 30.0],
        "land_area_sqmi": [1.0, 2.0, 3.0],
        "establishments": [5.0, 6.0, 7.0],
        "median_home_value": [100.0, 200.0, 400.0]})
    out = cf.static_frame(panel, ("median_home_value",),
                          ("median_home_value",))
    level = out["median_home_value"].to_numpy()
    inv = out[cf.INV + "median_home_value"].to_numpy()
    assert np.array_equal(np.argsort(level), np.argsort(inv)[::-1])
    assert (inv > 0).all()


# ---------------------------------------------------------------------------
# the grain audit, which is the headline finding


def _grain_panel(per_county: int, n_counties: int = 30) -> pd.DataFrame:
    """One metro of `per_county * n_counties` ZCTAs with two columns: one
    that varies per ZCTA and one that is a single county value."""
    rows = []
    for c in range(n_counties):
        for z in range(per_county):
            rows.append({"zcta": f"{c:03d}{z:02d}", "cbsa_code": "10000",
                         "county_geoid": f"{c:05d}", "year": 2018,
                         "households": 100.0 + z, "land_area_sqmi": 1.0 + z,
                         "establishments": 10.0 + z,
                         "zcta_grain": 1.0 + z + 100 * c,
                         "county_grain": 1.0 + c})
    return pd.DataFrame(rows)


def test_audit_flags_a_county_grain_column_and_counts_its_distinct_values():
    panel = _grain_panel(per_county=7)       # 210 ZCTAs, 30 counties
    out = audit.audit(panel, ("zcta_grain", "county_grain"))
    assert out["county_grain"]["county_grain_share"] == 1.0
    assert out["zcta_grain"]["county_grain_share"] == 0.0
    # The number the write-up leads on: how few values a big choice set
    # actually sees. 30 counties -> 30 distinct values for 210 alternatives.
    assert out["county_grain"]["mean_distinct_values_per_large_metro"] == 30
    assert out["zcta_grain"]["mean_distinct_values_per_large_metro"] == 210


def test_audit_reports_within_metro_correlation_not_national_correlation():
    # Two metros, each with households and a column that is households
    # PLUS a big per-metro offset. Nationally the offset dominates and the
    # raw correlation is near 1 for the wrong reason; demeaned by metro the
    # two are perfectly correlated for the RIGHT reason. The test pins that
    # the audit demeans, because the collinearity finding depends on it.
    rows = []
    for m, offset in (("10000", 0.0), ("20000", 1e6)):
        for z in range(150):
            rows.append({"zcta": f"{m[:1]}{z:04d}", "cbsa_code": m,
                         "county_geoid": f"{m}{z:03d}", "year": 2018,
                         "households": 10.0 + z,
                         "land_area_sqmi": 1.0 + 0.5 * z,
                         "establishments": 2.0 + z,
                         "twin": 10.0 + z + offset})
    out = audit.audit(pd.DataFrame(rows), ("twin",))
    corr = out["twin"]["within_metro_corr_with_baseline"]["households"]
    assert corr == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# the stage ledger


def test_stage_ledger_distinguishes_ran_from_carried_forward_from_absent():
    # An unexplained missing field is not an honest artefact state, so the
    # ledger has to tell the three cases apart rather than just recording
    # which keys exist.
    report = {"column_audit": {}, "anchor": {}}
    led = harness.ledger(report, ("audit",))
    assert led["audit"] == "ran_this_invocation"
    assert led["anchor"] == "carried_forward"
    assert led["core"] == "absent"
    # A stage that ran once stays "ran" only for that invocation; on a
    # later invocation that does not run it, it becomes carried_forward.
    report["stage_ledger"] = led
    assert harness.ledger(report, ())["audit"] == "carried_forward"
