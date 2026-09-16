"""Turn pairwise verdicts into groups of records, without inventing merges.

The trap this module exists to avoid
------------------------------------
A pairwise matcher plus a transitive closure is not a matcher. Consider the
three real Tracy CA records:

    A  1555 CHRISMAN RD        (no directional)
    B  1555 N CHRISMAN ROAD
    C  1555 S CHRISMAN RD

A-B agree on everything they both state, so the pair matches. A-C likewise.
B-C is a flat contradiction, N against S, and is a non-match. Connected
components over the matching edges give {A, B, C}: one building. The truth is
at least two, and the merge would silently delete one from the panel - the
exact failure mode that matters here, because a building that vanishes is
never noticed, whereas a building that appears twice eventually is.

So the closure is CHECKED rather than trusted. Any component that contains a
pair the comparison explicitly rejected is inconsistent, and an inconsistent
component is rebuilt from its strong edges only - the ones that did not rely
on a field being absent on one side. Records left stranded by that rebuild
are reported for clerical review instead of being attached to a guess.

This is the small, honest version of Winkler RR99-04 §2.2, where Jaro's
linear sum assignment procedure exists because "greedy algorithms often made
erroneous assignments" and only a global view over the household gets the
assignment right. We have the same problem one level down: the right answer
for A is not decidable from the A-B pair alone, only from the whole group.
"""

from __future__ import annotations

from dataclasses import dataclass

from .linkage import MATCH, NONMATCH, LinkRecord, Verdict, candidate_pairs
from .linkage import compare as compare_pair


@dataclass
class Grouping:
    """The result of linking one list of records to itself.

    `groups` maps a group id to the record indices in it. `review` holds the
    pairs a human has to look at, and `ambiguous` the records that were
    pulled out of an inconsistent component - both are outputs, not errors.
    """

    groups: list[list[int]]
    review: list[tuple[int, int, Verdict]]
    ambiguous: list[int]
    verdicts: dict[tuple[int, int], Verdict]

    @property
    def n_groups(self) -> int:
        return len(self.groups)


def _components(n: int, edges: list[tuple[int, int]]) -> list[list[int]]:
    """Connected components by union-find, returned as sorted index lists."""
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    out: dict[int, list[int]] = {}
    for i in range(n):
        out.setdefault(find(i), []).append(i)
    return [sorted(v) for v in out.values()]


def link(records: list[LinkRecord]) -> Grouping:
    """Group records that describe the same building.

    Every pair a blocking key put together is compared; nothing else is.
    That is deliberate and its cost is measured rather than assumed - see
    `ingest.address_audit`, which re-runs the comparison over every
    within-state pair and reports how many matches blocking would have lost.
    """
    n = len(records)
    verdicts: dict[tuple[int, int], Verdict] = {}
    for i, j in sorted(candidate_pairs(records)):
        verdicts[(i, j)] = compare_pair(records[i], records[j])

    strong = [(i, j) for (i, j), v in verdicts.items()
              if v.call == MATCH and not v.weak]
    weak = [(i, j) for (i, j), v in verdicts.items()
            if v.call == MATCH and v.weak]

    groups = _components(n, strong + weak)
    ambiguous: list[int] = []
    repaired: list[list[int]] = []
    for g in groups:
        if len(g) < 3 or _is_consistent(g, verdicts):
            repaired.append(g)
            continue
        # Inconsistent: something in this component contradicts something
        # else. Rebuild from strong edges alone. Anything that only reached
        # the group through a missing-field agreement is set loose, because
        # that is precisely the evidence that could not distinguish which
        # side of the contradiction it belonged on.
        inner = [(a, b) for a, b in strong if a in g and b in g]
        for sub in _components(n, inner):
            part = [x for x in sub if x in g]
            if not part:
                continue
            repaired.append(part)
            if len(part) == 1:
                ambiguous.append(part[0])
    review = [(i, j, v) for (i, j), v in sorted(verdicts.items())
              if v.call not in (MATCH, NONMATCH)]
    return Grouping(groups=sorted(repaired), review=review,
                    ambiguous=sorted(set(ambiguous)), verdicts=verdicts)


def _is_consistent(group: list[int],
                   verdicts: dict[tuple[int, int], Verdict]) -> bool:
    """Whether any pair inside a group was explicitly rejected.

    Only pairs that were actually compared count. A pair that blocking never
    generated is unknown, not rejected, and treating silence as a
    contradiction would dissolve perfectly good groups.
    """
    for x in range(len(group)):
        for y in range(x + 1, len(group)):
            v = verdicts.get((group[x], group[y]))
            if v is not None and v.call == NONMATCH:
                return False
    return True
