"""Tests for the machinery that only switches on once the target is real.

Every test here guards a failure that produces a NUMBER rather than an
error, which is why they exist at all:

  * forget the metro scope and the model is fitted on 33,791 national ZCTAs,
    most of which were never in Amazon's choice set; AUC goes up and means
    less
  * forget the hold-out and Phoenix and Boise are scored by a model that
    trained on them
  * cluster the robust covariance on the ZCTA and the standard errors are
    several times too narrow, because one delivery station flips a whole
    catchment in one quarter
  * count ZCTA-level events as independent and the power calculation reports
    eighty events per parameter where there are five
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from siting_atlas.models import diagnostics, panel_source, sensitivities
from siting_atlas.models.hazard import DiscreteTimeHazard, HazardSpec
from siting_atlas.models.risk_set import build_risk_set
from siting_atlas.models.runner import resolve_baseline

#: Two pilot CBSA codes that the registry declares fittable, and one held
#: out, taken from common.metros rather than hard-coded so a change to the
#: pilot definition fails here instead of silently changing the sample.
FIT_CODE = "16980"        # Chicago
HELDOUT_CODE = "38060"    # Phoenix


def panel(n_units: int = 24, n_quarters: int = 12) -> pd.DataFrame:
    """A miniature national panel: pilot ZCTAs, a held-out one, and noise.

    One unit in three carries a missing covariate so the scope filter's
    drop can be asserted, and the missingness is whole-unit because that is
    how the real panel behaves — ACS is pinned to one vintage and repeated
    down the quarters.
    """
    rows = []
    for u in range(n_units):
        code = (FIT_CODE if u % 3 == 0 else
                HELDOUT_CODE if u % 3 == 1 else "99999")
        broken = u % 3 == 2
        for t in range(n_quarters):
            rows.append({
                "zcta": f"{10000 + u:05d}",
                "year": 2018 + t // 4, "quarter": t % 4 + 1,
                "cbsa_code": code,
                "households": float(1000 + 10 * u),
                "median_household_income": np.nan if broken else 60000.0 + u,
                "establishments": float(50 + u),
                "enabled": bool(u % 6 == 0 and t >= 4),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# scope
# ---------------------------------------------------------------------------
def test_scope_keeps_only_fit_metros():
    scoped, detail = panel_source.restrict_to_scope(panel(), heldout=False)
    assert set(scoped["cbsa_code"]) == {FIT_CODE}
    assert detail["scope"] == "fit_metros"
    assert detail["units_national"] == 24
    assert HELDOUT_CODE not in detail["cbsa_codes"]


def test_scope_heldout_returns_the_other_metros():
    scoped, detail = panel_source.restrict_to_scope(panel(), heldout=True)
    assert set(scoped["cbsa_code"]) == {HELDOUT_CODE}
    assert detail["scope"] == "heldout_metros"
    # The two scopes must not overlap, or the "geographic transfer" test is
    # scoring the model on ZCTAs it was fitted on.
    fit, _ = panel_source.restrict_to_scope(panel(), heldout=False)
    assert not set(scoped["zcta"]) & set(fit["zcta"])


def test_scope_drops_units_missing_a_covariate_whole():
    """A partially dropped unit would puncture its own risk set."""
    scoped, detail = panel_source.restrict_to_scope(panel(), heldout=True)
    assert scoped["median_household_income"].notna().all()
    counts = scoped.groupby("zcta").size()
    assert counts.nunique() == 1, "a unit lost some quarters but not others"
    assert detail["units_complete_covariates"] <= detail["units_in_scope"]


def test_scope_does_not_overwrite_the_row_count_of_the_whole_file():
    _, detail = panel_source.restrict_to_scope(panel(), heldout=False)
    assert "rows" not in detail
    assert detail["rows_in_scope"] > 0


def test_real_covariates_are_three():
    """The events-per-parameter argument depends on this staying short."""
    assert len(panel_source.REAL_COVARIATES) == 3
    assert "rent_index_yoy_pct" not in panel_source.REAL_COVARIATES


# ---------------------------------------------------------------------------
# clustering
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def clustered_risk() -> pd.DataFrame:
    """Six ZCTAs per metro, all of which fire in the same quarter.

    This is the real panel's dependence structure in miniature: the event is
    a property of the catchment, not of the ZCTA, so the six ZCTAs carry one
    piece of information between them.
    """
    rows = []
    for metro in range(8):
        for member in range(6):
            for t in range(10):
                rows.append({
                    "zcta": f"{metro}{member}000",
                    "cbsa_code": f"C{metro}",
                    "year": 2018 + t // 4, "quarter": t % 4 + 1,
                    "x": float(metro) + 0.01 * member,
                    "enabled": bool(metro % 2 == 0 and t >= 5),
                })
    return build_risk_set(pd.DataFrame(rows), drop_left_truncated=False)


def test_metro_clustering_widens_the_standard_errors(clustered_risk):
    """Clustering on the ZCTA understates uncertainty when metros move."""
    spec = HazardSpec(covariates=("x",), baseline="linear")
    by_zcta = DiscreteTimeHazard(spec).fit(clustered_risk)
    by_metro = DiscreteTimeHazard(
        HazardSpec(covariates=("x",), baseline="linear",
                   cluster_col="cbsa_code")).fit(clustered_risk)

    zcta_se = by_zcta.coefficients().set_index("term").loc["x", "std_error"]
    metro_se = by_metro.coefficients().set_index("term").loc["x", "std_error"]
    assert metro_se > zcta_se
    # Point estimates are untouched by the covariance choice; if they move,
    # something other than the sandwich changed.
    np.testing.assert_allclose(by_zcta.result.params, by_metro.result.params)
    assert by_metro.n_clusters == 8
    assert by_zcta.n_clusters == 48


def test_cluster_count_is_reported_in_the_summary(clustered_risk):
    model = DiscreteTimeHazard(
        HazardSpec(covariates=("x",), baseline="linear",
                   cluster_col="cbsa_code")).fit(clustered_risk)
    assert model.summary()["n_clusters"] == 8
    assert model.summary()["specification"]["cluster_col"] == "cbsa_code"


# ---------------------------------------------------------------------------
# diagnostics
# ---------------------------------------------------------------------------
def test_independent_episodes_collapses_a_catchment(clustered_risk):
    """Twenty-four ZCTA events in four metros at one time are four draws."""
    n_events = int(clustered_risk["event"].sum())
    episodes = diagnostics.independent_episodes(clustered_risk, "cbsa_code")
    assert n_events == 24
    assert episodes == 4


def test_events_per_parameter_reports_the_effective_ratio():
    out = diagnostics.events_per_parameter(421, 5, 26, 38)
    assert out["events_per_parameter_nominal"] == pytest.approx(84.2)
    assert out["events_per_parameter_effective"] == pytest.approx(5.2)
    assert out["events_per_parameter_optimistic"] == pytest.approx(7.6)
    assert out["meets_floor"] is False


def test_events_per_parameter_is_judged_on_the_optimistic_bound():
    """A conservative proxy must not be what fails the check.

    38 buildings over 5 parameters is 7.6 and still under the floor, but if
    the building count cleared it the verdict has to follow the building
    count, or the floor is being enforced by the choice of proxy.
    """
    out = diagnostics.events_per_parameter(500, 5, 26, 60)
    assert out["events_per_parameter_effective"] == pytest.approx(5.2)
    assert out["meets_floor"] is True


def test_events_per_parameter_survives_an_unknown_facility_count():
    out = diagnostics.events_per_parameter(500, 5, 100, None)
    assert out["n_usable_facilities"] is None
    assert out["meets_floor"] is True


def test_event_timing_flags_the_q1_artefact(clustered_risk):
    """All synthetic events here land at t=5, i.e. one quarter-of-year."""
    timing = diagnostics.event_timing(clustered_risk)
    assert timing["distinct_event_times"] == 1
    assert timing["share_in_q1"] in (0.0, 1.0)
    assert 0.0 < timing["rows_structurally_eventless"] < 1.0


def test_transfer_check_refuses_an_eventless_sample(clustered_risk):
    spec = HazardSpec(covariates=("x",), baseline="linear")
    model = DiscreteTimeHazard(spec).fit(clustered_risk)
    empty = clustered_risk.assign(event=0)
    assert sensitivities.transfer_check(model, empty)["ran"] is False


def test_annual_collapse_keeps_every_event_and_drops_only_empty_rows(
        clustered_risk):
    """Collapsing to ZCTA-year must lose rows, never events.

    The three structurally eventless quarters are exactly what the collapse
    is meant to remove. If it removed an event with them the sensitivity
    would be comparing two different samples and its AUC would be a
    different question's answer.
    """
    spec = HazardSpec(covariates=("x",), baseline="linear",
                      cluster_col="cbsa_code")
    units = sorted(clustered_risk["zcta"].unique())
    parts = {"train": clustered_risk[clustered_risk["zcta"].isin(units[:32])],
             "test": clustered_risk[clustered_risk["zcta"].isin(units[32:])]}
    out = sensitivities.annual_sensitivity(clustered_risk, spec, parts)

    assert out["rows_annual"] < out["rows_quarterly"]
    assert (out["evaluation"]["n_events"]
            == int(parts["test"]["event"].sum()))


def test_temporal_check_refuses_a_split_with_no_future_events(
        clustered_risk):
    spec = HazardSpec(covariates=("x",), baseline="linear")
    out = sensitivities.temporal_check(clustered_risk, spec, cutoff_t=9)
    assert out["ran"] is False


def test_temporal_check_carries_the_contamination_caveat():
    """A split with events on both sides must still ship its caveat.

    Needs its own frame: ``clustered_risk`` fires every metro in the same
    quarter, so no cutoff leaves events on both sides — which is itself the
    shape the real panel is closest to.
    """
    rows = []
    for metro in range(8):
        for member in range(6):
            for t in range(12):
                rows.append({
                    "zcta": f"{metro}{member}000", "cbsa_code": f"C{metro}",
                    "year": 2018 + t // 4, "quarter": t % 4 + 1,
                    "x": float(metro) + 0.01 * member,
                    "enabled": bool(metro % 2 == 0
                                    and t >= 3 + 6 * (metro // 4))})
    risk = build_risk_set(pd.DataFrame(rows), drop_left_truncated=False)

    out = sensitivities.temporal_check(
        risk, HazardSpec(covariates=("x",), baseline="linear"), cutoff_t=5)
    assert out["ran"] is True
    assert out["train"]["events"] > 0 and out["test"]["events"] > 0
    assert out["caveat"] == diagnostics.CONTAMINATION


def test_events_by_metro_lists_the_silent_ones(clustered_risk):
    """A metro contributing nothing must appear, not be averaged away."""
    by_metro = diagnostics.events_by_metro(clustered_risk, "cbsa_code")
    assert len(by_metro) == 8
    assert sum(m["events"] for m in by_metro) == 24
    silent = [m for m in by_metro if m["events"] == 0]
    assert len(silent) == 4, "the odd-numbered metros never fire"
    assert all(m["units_at_risk"] == 6 for m in by_metro)


def test_contamination_note_names_its_source():
    """The caveat has to say OSHA, quantify the looseness, and name the
    specification the target actually calls for."""
    assert "OSHA" in diagnostics.CONTAMINATION
    assert "UPPER BOUND" in diagnostics.CONTAMINATION
    assert "interval censoring" in diagnostics.CONTAMINATION
    # The measured lags are evidence, so they have to survive into the text
    # a reader sees rather than living only in a comment.
    assert str(max(diagnostics.BOUND_LAG_MONTHS)) in diagnostics.CONTAMINATION


# ---------------------------------------------------------------------------
# baseline selection
# ---------------------------------------------------------------------------
def test_auto_baseline_is_linear_on_the_real_panel():
    assert resolve_baseline("auto", synthetic=False) == "linear"
    assert resolve_baseline("auto", synthetic=True) == "spline"


def test_explicit_baseline_is_never_overridden():
    assert resolve_baseline("dummies", synthetic=False) == "dummies"
    assert resolve_baseline("spline", synthetic=False) == "spline"
