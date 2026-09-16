"""What the NLRB ingest and the coverage estimate must get right.

Three groups of test, and they guard three different failure modes.

1. City normalisation. The only join key this source supports is city+state,
   so a spelling variant is not cosmetic: it invents a city that appears on
   one list and not the other, which inflates the estimated population and
   understates our coverage. Every case below is one this project measured
   against the real file, not an invented example.

2. The collapse to one record per place. The earliest filing is the bound;
   anything later adds nothing, and losing it would weaken a bound we have.

3. The estimators. Hand-computed against the textbook formulae, because an
   arithmetic slip in a capture-recapture estimate produces a number that
   looks perfectly reasonable and is wrong - there is no plausibility check
   available on "how many facilities did you miss".
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from siting_atlas.ingest.nlrb import (
    RawPlace,
    by_place,
    normalise_city,
    read_cases,
)
from siting_atlas.ingest.nlrb_estimators import (
    chao_lower_bound,
    chapman,
    lincoln_petersen,
    loglinear_three_list,
    lognormal_ci,
    odds_ratio,
)

HEADER = ('"Case Type",Region,"Case Number","Case Name",Status,'
          '"Date Filed","Date Closed","Reason Closed",City,'
          '"States & Territories","Employees on charge/petition",'
          'Allegations,Participants,Union,"Unit Sought",Voters\n')


def _csv(tmp_path, *rows):
    path = tmp_path / "cases.csv"
    path.write_text(HEADER + "".join(rows), encoding="utf-8")
    return path


def _row(case, city, state, filed, employees="1000", ctype="C",
         name="Amazon.com Services LLC"):
    return (f'{ctype},"Region 29, Brooklyn, New York",{case},"{name}",Open,'
            f'{filed},,,{city},{state},{employees},,,,,\n')


# --- 1. city normalisation -------------------------------------------

@pytest.mark.parametrize("a,b", [
    # Measured against the real extract on 2026-09-13. Each of these was a
    # false NON-match under the parent's plain upper-and-strip key, and each
    # one of them added a spurious city to the "NLRB never saw it" list.
    ("Castleton-on-Hudson", "CASTLETON ON HUDSON"),
    ("Robbinsville (Township)", "Robbinsville"),
    ("Brownstown Township", "Brownstown"),
    # Not observed in this extract, but the same class of defect and cheap
    # to guard, because the next download will contain some of them.
    ("St. Louis", "Saint Louis"),
    ("Mt. Juliet", "Mount Juliet"),
    ("Ft. Worth", "Fort Worth"),
    ("  new   york  ", "New York"),
])
def test_normalise_city_collapses_known_variants(a, b):
    assert normalise_city(a) == normalise_city(b)


@pytest.mark.parametrize("a,b", [
    # The over-collapse direction, which is the worse error: merging two
    # real cities deletes one from the frame and nothing downstream notices.
    ("Kansas City", "Kansas"),
    ("New Windsor", "New York"),
    ("North Las Vegas", "Las Vegas"),
    ("West Columbia", "Columbia"),
])
def test_normalise_city_keeps_different_places_apart(a, b):
    assert normalise_city(a) != normalise_city(b)


def test_normalise_city_tolerates_missing():
    assert normalise_city(None) == ""
    assert normalise_city("") == ""


# --- 2. parsing and the collapse to one record per place --------------

def test_read_cases_keeps_every_amazon_row(tmp_path):
    path = _csv(tmp_path,
                _row("29-CA-000001", "Staten Island", "NY", "06/24/2009"),
                _row("29-CA-000002", "Staten Island", "NY", "01/02/2020"))
    rows = read_cases(path)
    assert len(rows) == 2
    assert rows[0]["case_number"] == "29-CA-000001"
    assert rows[0]["date_filed"] == "2009-06-24"


def test_read_cases_rejects_a_non_amazon_employer(tmp_path):
    path = _csv(tmp_path,
                _row("29-CA-000001", "Staten Island", "NY", "06/24/2009"),
                _row("29-CA-000002", "Peoria", "IL", "01/02/2020",
                     name="Amazonia Tree Service"))
    assert len(read_cases(path)) == 1


@pytest.mark.parametrize("name", [
    # Verbatim from the real export. Every one of these was dropped by a
    # first implementation that anchored the match to the start of the
    # employer name, and every one is a DSP or joint-employer filing - the
    # exact rows HOWTO.md section 4 names as the source's worst blind spot.
    "MOLOCK Logistics and Amazon, as joint employers",
    "Silverstar Delivery LTD, Gold Standard Transportation and Amazon, "
    "Logistics, Inc., Joint Employers",
    "Elite Line Services at Amazon CLT2",
    "Security Industry Specialists, Inc., and Amazon, as joint employers",
    "WNY3 Amazon Warehouse",
    "Whole Foods/Amazon",
    "GOLDEN STATE, LLC - DBA AMAZON",
])
def test_joint_employer_and_dsp_filings_are_kept(name):
    from siting_atlas.ingest.nlrb import is_amazon_employer
    assert is_amazon_employer(name)


def test_a_namesake_trade_is_still_excluded():
    from siting_atlas.ingest.nlrb import is_amazon_employer
    # "Amazon Construction" is in the real export and we cannot tell whether
    # it is the retailer's building programme or a firm named after the
    # river. The shared exclusion list in ingest.osha drops it, and dropping
    # an ambiguous row is the conservative direction: a spurious city shows
    # up in a count, a wrong one does not.
    assert not is_amazon_employer("Amazon Construction")
    assert not is_amazon_employer("Amazonia Tree Service")


def test_by_place_takes_the_earliest_filing_as_the_bound(tmp_path):
    path = _csv(tmp_path,
                _row("29-CA-000002", "Staten Island", "NY", "01/02/2020"),
                _row("29-CA-000001", "Staten Island", "NY", "06/24/2009"),
                _row("29-CA-000003", "STATEN ISLAND", "ny", "03/05/2022"))
    places = by_place(read_cases(path))
    assert len(places) == 1
    assert places[0].operating_by == "2009-06-24"
    assert places[0].n_cases == 3


def test_by_place_carries_the_size_proxy_and_the_case_mix(tmp_path):
    path = _csv(tmp_path,
                _row("29-CA-000001", "Bessemer", "AL", "06/24/2020",
                     employees="5800"),
                _row("29-RC-000002", "Bessemer", "AL", "11/20/2020",
                     employees="1500", ctype="R"),
                _row("29-CA-000003", "Bessemer", "AL", "01/05/2021",
                     employees=""))
    place, = by_place(read_cases(path))
    assert place.employees_max == 5800
    assert place.employees_median == 3650      # median of 5800 and 1500
    assert place.n_unfair_labour == 2
    assert place.n_petition == 1
    # Two of three rows carry the proxy. Reporting a size without saying how
    # much of the group it rests on is the defect this field exists to stop.
    assert place.n_with_employees == 2
    assert place.n_employees_over_cutoff == 0


def test_a_company_wide_headcount_is_flagged_and_not_silently_edited(tmp_path):
    """Van den Broeck's soft cutoff: flag for diagnosis, never edit quietly.

    53 cases in the real export record 1,000,000 employees against a single
    city, because a national charge against the Teamsters names Amazon's
    whole workforce. Truncating it would invent a facility size; dropping it
    would lose the case; leaving it unmarked would let somebody average it.
    """
    path = _csv(tmp_path,
                _row("29-CB-000001", "Maspeth", "NY", "01/02/2025",
                     employees="1000000"),
                _row("29-CA-000002", "Maspeth", "NY", "01/02/2024",
                     employees="5000"))
    place, = by_place(read_cases(path))
    assert place.n_employees_over_cutoff == 1
    assert place.employees_max == 1_000_000     # carried, not truncated
    assert place.n_with_employees == 2


def test_by_place_merges_a_spelling_variant_into_one_place(tmp_path):
    path = _csv(tmp_path,
                _row("03-CA-000001", "Castleton-on-Hudson", "NY",
                     "01/02/2020"),
                _row("03-CA-000002", "Castleton On Hudson", "NY",
                     "01/02/2019"))
    place, = by_place(read_cases(path))
    assert place.n_cases == 2
    assert place.operating_by == "2019-01-02"


def test_by_place_keeps_the_same_city_name_in_two_states_apart(tmp_path):
    path = _csv(tmp_path,
                _row("07-CA-000001", "Columbus", "OH", "01/02/2020"),
                _row("10-CA-000002", "Columbus", "GA", "01/02/2020"))
    assert len(by_place(read_cases(path))) == 2


def test_place_is_a_value_type():
    a = RawPlace(city="STATEN ISLAND", state="NY")
    b = RawPlace(city="STATEN ISLAND", state="NY")
    assert a.key == b.key == ("STATEN ISLAND", "NY")


# --- 3. the estimators ------------------------------------------------

def test_lincoln_petersen_is_the_textbook_ratio():
    # The fish-in-a-lake example from data/external/nlrb/HOWTO.md section 3:
    # 100 tagged, 100 recaught, 20 of them tagged -> about 500 fish.
    assert lincoln_petersen(100, 100, 20) == pytest.approx(500.0)


def test_lincoln_petersen_is_undefined_with_no_overlap():
    # n1*n2/0. Returning inf rather than raising would let a nonsense
    # estimate propagate into a report.
    with pytest.raises(ValueError):
        lincoln_petersen(100, 100, 0)


def test_chapman_is_hand_computed():
    # (n1+1)(n2+1)/(m+1) - 1 with n1=n2=100, m=50.
    est, var = chapman(100, 100, 50)
    assert est == pytest.approx(101 * 101 / 51 - 1)
    # (n1+1)(n2+1)(n1-m)(n2-m) / ((m+1)^2 (m+2))
    assert var == pytest.approx(101 * 101 * 50 * 50 / (51 ** 2 * 52))


def test_chapman_is_less_than_lincoln_petersen_here():
    # Chapman's correction removes the small-sample upward bias of the
    # ratio estimator, so it must not sit above it on this data.
    assert chapman(208, 340, 112)[0] < lincoln_petersen(208, 340, 112)


def test_chao_lower_bound_is_hand_computed():
    # S_obs + f1(f1-1) / (2(f2+1)), the bias-corrected form.
    est, _ = chao_lower_bound(s_obs=150, f1=100, f2=50)
    assert est == pytest.approx(150 + 100 * 99 / (2 * 51))


def test_chao_never_falls_below_what_was_observed():
    est, _ = chao_lower_bound(s_obs=150, f1=0, f2=50)
    assert est == pytest.approx(150.0)


def test_chao_exceeds_chapman_when_catchability_is_heterogeneous():
    """The whole reason for reporting Chao alongside Lincoln-Petersen.

    On the real city counts (208 NLRB, 340 OSHA, 112 shared) the two
    estimators disagree by a factor of about 1.4. If they ever agreed
    closely, the heterogeneity argument in docs/data/NLRB.md would be
    decoration rather than a finding.
    """
    n1, n2, m = 208, 340, 112
    s_obs = n1 + n2 - m
    chao, _ = chao_lower_bound(s_obs=s_obs, f1=(n1 - m) + (n2 - m), f2=m)
    assert chao > chapman(n1, n2, m)[0] * 1.3


def test_lognormal_ci_brackets_the_estimate_and_never_goes_below_s_obs():
    lo, hi = lognormal_ci(est=630.0, s_obs=436, var=1071.0)
    assert 436 < lo < 630.0 < hi
    # Chao's own recommendation: the interval is built on the UNSEEN count,
    # so its lower limit cannot imply fewer places than we have in hand.
    assert lo > 436


def test_lognormal_ci_is_undefined_when_nothing_is_unseen():
    with pytest.raises(ValueError):
        lognormal_ci(est=436.0, s_obs=436, var=10.0)


def test_loglinear_recovers_an_exactly_independent_table():
    """Sanity floor for the three-list model.

    Build a table in which the three lists are independent by construction,
    N = 1000 with capture probabilities 0.5, 0.4 and 0.25. The independence
    model must return the cell that was withheld, 1000*0.5*0.6*0.75 = 225.
    """
    n, p = 1000.0, (0.5, 0.4, 0.25)
    cells = {}
    for a in (0, 1):
        for b in (0, 1):
            for c in (0, 1):
                if (a, b, c) == (0, 0, 0):
                    continue
                w = 1.0
                for flag, pk in zip((a, b, c), p, strict=True):
                    w *= pk if flag else (1 - pk)
                cells[(a, b, c)] = n * w
    fits = loglinear_three_list(cells)
    assert fits["[1][2][3]"].unseen == pytest.approx(225.0, rel=1e-6)
    # With no dependence to find, the saturated pairwise model must agree.
    assert fits["[12][13][23]"].unseen == pytest.approx(225.0, rel=1e-4)


def test_loglinear_detects_positive_pairwise_dependence():
    """Move mass into the all-three cell and the estimate must rise.

    This is the direction the brief asserts and the model has to reproduce:
    positive dependence between lists means the independence model
    understates the population.
    """
    base = {(1, 1, 1): 26, (1, 1, 0): 22, (1, 0, 1): 13, (1, 0, 0): 42,
            (0, 1, 1): 37, (0, 1, 0): 54, (0, 0, 1): 34}
    indep = loglinear_three_list(base)["[1][2][3]"].unseen
    pairwise = loglinear_three_list(base)["[12][13][23]"].unseen
    assert pairwise > indep


def test_loglinear_reports_degrees_of_freedom():
    base = {(1, 1, 1): 26, (1, 1, 0): 22, (1, 0, 1): 13, (1, 0, 0): 42,
            (0, 1, 1): 37, (0, 1, 0): 54, (0, 0, 1): 34}
    fits = loglinear_three_list(base)
    assert fits["[1][2][3]"].df == 3
    assert fits["[12][13][23]"].df == 0
    assert all(math.isfinite(f.aic) for f in fits.values())


def test_odds_ratio_is_one_under_independence():
    assert odds_ratio(10, 10, 10, 10) == pytest.approx(1.0)
    assert odds_ratio(20, 10, 10, 10) == pytest.approx(2.0)


# --- 4. the real artefacts, so the published figures cannot drift -----

REAL_NLRB = (Path(__file__).resolve().parents[2] / "data" / "external" /
             "nlrb" / "nlrb_cases_amazon.csv")
REAL_OSHA = (Path(__file__).resolve().parents[2] / "data" / "interim" /
             "osha_amazon.csv")

needs_real = pytest.mark.skipif(
    not (REAL_NLRB.exists() and REAL_OSHA.exists()),
    reason="the downloaded NLRB export or the OSHA extract is absent")


@needs_real
def test_the_published_city_counts_reproduce():
    """Every figure quoted in docs/data/NLRB.md, re-derived.

    The brief that commissioned this work quoted 209 / 340 / 108 / 101 from
    a plain upper-and-strip city key. Those are the numbers below the
    `naive` line, and they are reproduced too, so that the correction is
    auditable rather than a claim about somebody else's arithmetic.
    """
    from siting_atlas.ingest.nlrb_capture import load_lists, two_list
    osm = (Path(__file__).resolve().parents[2] / "data" / "raw" /
           "osm_amazon" / "_candidates_all.csv")
    lists = load_lists(REAL_NLRB, REAL_OSHA, osm)
    result = two_list(lists["nlrb"], lists["osha"])
    assert (result["n_nlrb"], result["n_osha"], result["overlap"]) == (
        208, 340, 112)
    assert result["nlrb_only"] == 96
    assert result["chapman"] == pytest.approx(629.7, abs=0.1)
    assert result["chao_lower_bound"] == pytest.approx(899.1, abs=0.1)
    # The headline, in the only direction the assumptions support.
    assert result["osha_coverage_upper_bound_chapman"] < 0.55
    assert result["osha_coverage_upper_bound_chao"] < 0.39


@needs_real
def test_the_dependence_that_invalidates_the_naive_estimate_is_positive():
    """Not an assumption once there is a third list. A measurement.

    If any of these fell below 1 the argument in docs/data/NLRB.md would
    have to be rewritten, because the naive estimate would no longer be a
    bound in the stated direction.
    """
    from siting_atlas.ingest.nlrb_capture import (
        OSM_FRAME,
        load_lists,
        three_list,
    )
    osm = (Path(__file__).resolve().parents[2] / "data" / "raw" /
           "osm_amazon" / "_candidates_all.csv")
    frame = three_list(load_lists(REAL_NLRB, REAL_OSHA, osm), OSM_FRAME)
    assert all(v > 1.0 for v in frame["measured_odds_ratios"].values())
    # And the consequence: allowing dependence raises the population.
    assert (frame["models"]["[12][13][23]"]["population"]
            > frame["models"]["[1][2][3]"]["population"])
