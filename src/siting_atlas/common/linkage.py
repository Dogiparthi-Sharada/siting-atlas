"""Decide whether two facility records describe the same building.

What Winkler's paper asks for, and what we are actually doing
------------------------------------------------------------
Fellegi-Sunter (Winkler RR99-04 §2) scores a pair by the likelihood ratio

    R = P(agreement pattern | M) / P(agreement pattern | U)

and applies a THREE-way rule (his eq. 4): above UPPER declare a match, below
LOWER declare a non-match, and in between "hold for clerical review". We
implement that decision rule. We do NOT implement the likelihood ratio, and
the reason is in the paper rather than in our convenience.

Estimating the m- and u-probabilities needs the EM machinery of §3.2, and
§3.1 is explicit about when that pays off: frequency- and likelihood-based
weighting is "seriously compromised" for lists that have "moderate to large
proportions of records that fail standardization, have excessively high
typographical error rates, and have only moderate overlap." A free-text
address field typed by OSHA inspectors is precisely that list. §3.1 also
gives the positive reason to skip it: "If there is a substantial number of
fields available for matching, then the redundancy provided by the extra
fields can reduce matching error... If redundancy is sufficient, then it
seems likely that frequency-based matching is not needed." House number,
street name, suffix, two directionals, ZIP, city and an Amazon building code
are seven redundant fields for one building.

And §3.4 removes the last argument for it. The only automatic error-rate
estimator the paper knows of is Belin and Rubin (1995), which needs
calibration data and "substantial separation of the curves of log frequency
versus matching weight". We have 516 records, no calibration data, and
therefore no way to turn a likelihood score into an error rate. Fitting EM
here would produce a number that LOOKS like a probability and is not one.
A deterministic rule whose review band we actually read is more honest at
this size, and it is the same decision rule either way.

The one thing we take literally is the string comparator (§2.1). Jaro-
Winkler is implemented below from the paper's own description, because
§2.1 reports that without approximate comparison "more than 25% of matches
would not have been found via exact character-by-character matching", and
our OSHA extract contains BABBITT/BABBIT, LOGISTIC/LOGISTICS and
WENDALL/WENDELL.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .address import Address, parse_address

#: Where the street comparator's two decision boundaries sit. These are
#: MEASURED, not borrowed. `ingest.address_audit --sweep` scores every
#: within-state pair that shares a house number and prints the distribution;
#: on the 516-address extract it is sharply bimodal with an empty gap:
#:
#:      JW ~1.00   64 pairs   ZEUBER/ZEUBER, GOODMAN/GOODMAN      same street
#:      JW  0.905   1 pair    ROSWELL/POSWELL                     typo
#:      JW  0.849   1 pair    MANDINA/NANDINA                     typo
#:      ---------------------- nothing at all between here -------------
#:      JW  0.722   2 pairs   NEWCANTON/CANTON                    different
#:      JW  0.679   1 pair    CENTRAL/CANTON                      different
#:      JW <0.63    6 pairs   BOONE/CROCKER, FOOTHILLS/METROAIR   different
#:
#: So STREET_REVIEW sits in the middle of the observed gap rather than on
#: either edge of it, which is the most defensible place for a cut that no
#: labelled data pinned down. Winkler's Table 1 quotes Mn >= 0.6 as its
#: partial-agreement bucket, but that is for PERSON names - short, high
#: entropy, and nothing like a street. At 0.6 this dataset would admit
#: CENTRAL/CANTON and merge two real New Jersey facilities.
STREET_MATCH = 0.92
STREET_REVIEW = 0.78

#: Winkler's prefix bonus, from Pollock and Zamora's finding (cited in §2.1)
#: that keypunch errors get more likely further right in a string. So an
#: agreeing prefix is worth more than an agreeing tail.
PREFIX_WEIGHT = 0.1
PREFIX_MAX = 4

AGREE, MISSING, CONFLICT = "agree", "missing", "conflict"
MATCH, REVIEW, NONMATCH = "match", "review", "nonmatch"


def jaro(s1: str, s2: str) -> float:
    """Jaro's 1976 comparator, as described in Winkler RR99-04 §2.1.

    Three components, in the paper's words: string lengths, the number of
    common characters, and the number of transpositions, where "common"
    means the agreeing character sits within half the length of the shorter
    string.

    One correction to the paper. Its printed formula ends
    "+ 0.5 #transpositions/#common", which would make a pair score HIGHER
    the more transposed it is. That is a transcription error in RR99-04;
    the term is subtractive, (#common - 0.5*#transpositions)/#common, as in
    Jaro (1989) and every implementation since. We implement the correct
    one, because the printed one is not a similarity measure.
    """
    if not s1 or not s2:
        return 0.0
    if s1 == s2:
        return 1.0
    window = max(len(s1), len(s2)) // 2 - 1
    if window < 0:
        window = 0
    used2 = [False] * len(s2)
    common1: list[str] = []
    for i, ch in enumerate(s1):
        lo, hi = max(0, i - window), min(i + window + 1, len(s2))
        for j in range(lo, hi):
            if not used2[j] and s2[j] == ch:
                used2[j] = True
                common1.append(ch)
                break
    if not common1:
        return 0.0
    common2 = [s2[j] for j in range(len(s2)) if used2[j]]
    half = sum(1 for a, b in zip(common1, common2, strict=True) if a != b)
    c = len(common1)
    return (c / len(s1) + c / len(s2) + (c - half / 2) / c) / 3


def jaro_winkler(s1: str, s2: str) -> float:
    """Jaro with Winkler's prefix bonus. §2.1 rates this the best of twenty.

    Budzinsky's review, cited in the paper, "concluded that the methods of
    Jaro and Winkler worked second best and best, respectively".
    """
    j = jaro(s1, s2)
    if j == 0.0:
        return 0.0
    n = 0
    for a, b in zip(s1, s2, strict=False):
        if a != b or n >= PREFIX_MAX:
            break
        n += 1
    return j + n * PREFIX_WEIGHT * (1 - j)


def slot(a: str, b: str) -> str:
    """Compare one component, distinguishing ABSENT from CONTRADICTED.

    This three-valued return is the entire reason the addresses are parsed.
    Two records that both omit a directional agree about it. One that omits
    what the other states is Winkler §2.3 case 3, a missing matching
    variable, and is weak evidence either way. Two that state DIFFERENT
    directionals are describing different streets, and no amount of
    agreement elsewhere should overturn that - it is what keeps 1555 N
    CHRISMAN RD and 1555 S CHRISMAN RD apart.
    """
    if a == b:
        return AGREE
    if not a or not b:
        return MISSING
    return CONFLICT


@dataclass(frozen=True)
class LinkRecord:
    """One row from any source, reduced to what matching can use.

    Sources differ in what they carry: OSHA has free-text street and no
    building code, the OpenStreetMap export has a building code and NO
    STREET AT ALL. Both become this, and the comparison below decides what
    can be concluded from whichever fields are populated, rather than each
    caller inventing its own join.
    """

    rid: str
    state: str = ""
    city: str = ""
    zip: str = ""
    code: str = ""
    addr: Address = field(default_factory=Address)

    @classmethod
    def build(cls, rid, street, city, state, zipcode, code="") -> LinkRecord:
        parsed = parse_address(street or "")
        return cls(rid=rid, state=(state or "").strip().upper(),
                   city=(city or "").strip().upper(),
                   zip=(zipcode or "").strip()[:5],
                   code=(code or parsed.code).strip().upper(), addr=parsed)


@dataclass(frozen=True)
class Verdict:
    """The outcome for one pair, with the reason kept for clerical review."""

    call: str
    why: str
    weak: bool = False
    score: float = 0.0


def compare(a: LinkRecord, b: LinkRecord) -> Verdict:
    """Fellegi-Sunter's three-way rule, eq. (4), on parsed components."""
    if a.state and b.state and a.state != b.state:
        return Verdict(NONMATCH, "different state")

    # The building code is Amazon's own identifier for the site. When both
    # sides carry one it settles the question in either direction, and it is
    # the ONLY field shared with the OpenStreetMap export, which has no
    # street. Checked first so that a code can rescue a pair that has no
    # comparable address at all.
    if a.code and b.code:
        if a.code == b.code:
            return Verdict(MATCH, f"building code {a.code}", score=1.0)
        return Verdict(NONMATCH, f"codes {a.code} vs {b.code} differ")

    if not a.addr.street or not b.addr.street:
        # One side did not standardise, or is an OSM row with no street.
        # Winkler §2.3: such a record "may be impossible" to match
        # automatically. City and ZIP alone are not enough - 32 of the 148
        # (state, ZIP) cells in the OSM export hold more than one station -
        # so this is surfaced for review, never auto-merged.
        if a.zip and a.zip == b.zip and a.city == b.city:
            return Verdict(REVIEW, "no street on one side; city+ZIP only")
        return Verdict(NONMATCH, "no comparable street")

    if a.addr.number != b.addr.number:
        return Verdict(NONMATCH, "different house number")

    pre = slot(a.addr.predir, b.addr.predir)
    post = slot(a.addr.postdir, b.addr.postdir)
    if pre == CONFLICT or post == CONFLICT:
        return Verdict(NONMATCH, "directional conflict")

    sim = jaro_winkler(a.addr.core, b.addr.core)
    if a.addr.core == b.addr.core:
        street, sim = "exact", 1.0
    elif sim >= STREET_MATCH:
        street = "close"
    elif sim >= STREET_REVIEW:
        street = "weak"
    else:
        return Verdict(NONMATCH, f"street {sim:.2f}", score=sim)

    suf = slot(a.addr.suffix, b.addr.suffix)
    geo = bool(a.zip and a.zip == b.zip) or bool(a.city and a.city == b.city)
    weak = street != "exact" or MISSING in (pre, post, suf)

    if suf == CONFLICT:
        # Same number, same street name, different street TYPE. Usually one
        # record is mistyped, occasionally two streets really do share a
        # name. We cannot tell, so we say so rather than pick.
        return Verdict(REVIEW, f"suffix {a.addr.suffix}/{b.addr.suffix}",
                       True, sim)
    if street == "weak":
        return Verdict(REVIEW, f"street similarity {sim:.2f}", True, sim)
    if not geo:
        # Neither ZIP nor city corroborates. OSHA ZIPs are demonstrably
        # unreliable, so this is not a non-match - but an uncorroborated
        # merge is exactly the "wrong merge silently deletes a facility"
        # failure, so it goes to a human.
        return Verdict(REVIEW, "no ZIP or city corroboration", True, sim)
    return Verdict(MATCH, f"street {street}, geo agrees", weak, sim)


def blocking_keys(r: LinkRecord) -> list[str]:
    """Cheap keys that a true pair is very likely to share.

    Winkler's paper does not cover blocking at all - it is an overview of
    the model, not of the plumbing - so these are ours, and they are
    measured rather than asserted: `ingest.address_audit` reports what
    fraction of the pairs found by an exhaustive within-state comparison
    survive blocking. A pair that is never GENERATED is a false non-match
    that no threshold can recover, which is why there are two keys and not
    one.

    Key 1 catches everything except a mistyped house number; key 2 catches
    a mistyped house number on a street we can still recognise. The union
    of the two is the candidate set.
    """
    keys = []
    if r.addr.number:
        keys.append(f"N|{r.state}|{r.addr.number}")
    if r.addr.core:
        keys.append(f"S|{r.state}|{r.addr.core[:5]}")
    if r.code:
        keys.append(f"C|{r.code}")
    return keys


def candidate_pairs(records: list[LinkRecord]) -> set[tuple[int, int]]:
    """Index pairs worth comparing, from the union of the blocking keys."""
    buckets: dict[str, list[int]] = {}
    for i, r in enumerate(records):
        for k in blocking_keys(r):
            buckets.setdefault(k, []).append(i)
    pairs: set[tuple[int, int]] = set()
    for members in buckets.values():
        # A pathologically large block would be quadratic. None occurs here
        # (the biggest is 5), but the guard states the assumption instead of
        # leaving a future dataset to discover it as a hang.
        if len(members) > 200:
            continue
        for x in range(len(members)):
            for y in range(x + 1, len(members)):
                pairs.add((members[x], members[y]))
    return pairs
