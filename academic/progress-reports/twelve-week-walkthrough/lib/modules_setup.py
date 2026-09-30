"""Weeks 1-3: choose the question, choose the method, get the data.

The part of a semester that produces no results and decides whether the
rest of it is possible.
"""

from __future__ import annotations

import docstats as ds
from modmeta import INSPECT

ALT = "docs/ALTERNATIVES.md"
REF = "docs/REFERENCES.md"
LOG = "docs/DECISION_LOG.md"

WEEKS = [
    dict(
        n=1, title="Scope and feasibility", mode=INSPECT,
        question="Is this answerable at all from free public data — and at "
                 "what geographic grain?",
        artefacts=["scope"],
        why_inspect=(
            "scoping is a decision, not a computation; its record is "
            "ROADMAP.md and ALTERNATIVES.md"),
        runs="reads the study-scope artefact and the options document",
        status="Question fixed, and feasibility proven before we wrote "
               "modelling code.",
        risk="That the target variable — where a firm opens a building — "
             "simply does not exist in public form. We checked first "
             "rather than discovering it in week 8.",
        body="""
Before anything is modelled, two questions have to be settled: what exactly
is being predicted, and is the evidence for it obtainable by someone with no
special access.

We fixed the unit as the ZIP-code area (ZCTA) because it is the finest grain
most free US data publishes at — not because it is the natural unit of a
siting decision, which is a parcel. That gap is a limitation we carried all
semester and stated every time it mattered.

The scope artefact is the honest size of the thing: how many metros, how
many counties, how many ZCTAs, and how big the decision space is if you
treat every ZCTA as a yes/no. That last number is why an exhaustive search
was never on the table.
""",
        nums=lambda L: [
            ("Pilot metros", L("scope")["pilot"]["metros"],
             "scope.pilot.metros"),
            ("Pilot counties", L("scope")["pilot"]["counties"],
             "scope.pilot.counties"),
            ("Pilot ZCTAs", f"{L('scope')['pilot']['zctas']:,}",
             "scope.pilot.zctas"),
            ("ZCTAs nationally", f"{L('scope')['national_zctas']:,}",
             "scope.national_zctas"),
            ("Decision space", L("scope")["compute"]["search_space_label"],
             "scope.compute.search_space_label"),
            ("Options written up before choosing",
             ds.count(ALT, r"^## Option "), f"{ALT} '## Option'"),
        ],
        limits=[
            "A ZCTA is a postal-delivery construct, not a polygon, and it "
            "is coarser than the parcel a siting decision is actually made "
            "over. Chosen for data availability, not for fit.",
            "The pilot scope is ten metros. The national panel came later, "
            "and several early results are pilot-only — week 11 says which.",
        ],
        nxt=[("docs/ROADMAP.md", "what we set out to do, written first"),
             ("docs/ALTERNATIVES.md",
              "the five directions considered and why four were dropped")],
    ),
    dict(
        n=2, title="Literature and method selection", mode=INSPECT,
        question="Which methods, chosen against what alternatives — and how "
                 "much of the literature did we actually read?",
        artefacts=[],
        docs_only=True,
        why_inspect=(
            "a literature review produces documents, not artefacts; the "
            "counts below are read out of those documents"),
        runs="counts options, references and logged decisions in the docs",
        status="Conditional logit for the choice model, Daganzo continuous "
               "approximation for cost. Both chosen in writing, against "
               "alternatives we recorded rather than forgot.",
        risk="Picking a method because it is familiar rather than because "
             "it fits the data. The defence is that the rejected options "
             "are written down and can be argued with.",
        body="""
Two methods carry the project.

**Conditional logit** for "which ZIP, given an opening" — because the
decision is a choice among alternatives in a set, which is exactly what the
model is for. Utility is `V = ln(beta' a)` with `beta = exp(theta)`, so
weights stay positive, and households act as numeraire so every other
coefficient reads as "worth this many households".

**Daganzo's continuous approximation** for cost — because it prices a
delivery tour from density and geometry rather than from a route solver,
which means it needs no proprietary routing data. Its regime of validity is
stated and tested rather than assumed.

The reference table is marked by how far each citation was verified, and
that marking is the number worth showing: **[V]** read in full, **[T]**
title and venue confirmed against a publisher page, **[K]** cited from
knowledge and explicitly flagged to check before submission. Most
bibliographies do not tell you which is which.
""",
        nums=lambda L: [
            ("Options considered", ds.count(ALT, r"^## Option "),
             f"{ALT} '## Option'"),
            ("References, read in full [V]",
             ds.count(REF, r"\[V\]"), f"{REF} '[V]' markers"),
            ("References, title-verified [T]",
             ds.count(REF, r"\[T\]"), f"{REF} '[T]' markers"),
            ("References, cited from knowledge [K]",
             ds.count(REF, r"\[K\]"), f"{REF} '[K]' markers"),
            ("Method notes written",
             f"{ds.lines('docs/METHODS_RESEARCH.md'):,} lines",
             "docs/METHODS_RESEARCH.md"),
            ("Decisions logged with evidence",
             ds.count(LOG, r"^### [0-9]+\.[0-9]+ "), f"{LOG} numbered"),
        ],
        limits=[
            "The [K] references are cited from knowledge, not checked "
            "against a page. They are real and standard works, but the "
            "details printed here are unconfirmed and marked as such.",
            "Choosing a method in advance is not the same as validating it. "
            "Whether Daganzo's approximation holds in this regime is "
            "tested in week 11, not here.",
        ],
        nxt=[("docs/METHODS_RESEARCH.md", "the methods survey in full"),
             ("docs/REFERENCES.md",
              "every citation, with how far it was verified"),
             ("docs/ALGORITHMS.md",
              "each method in plain language, then precisely")],
    ),
    dict(
        n=3, title="Data acquisition and provenance", mode=INSPECT,
        question="Can a stranger fetch every ingredient themselves, and is "
                 "each one licensed for that?",
        artefacts=["source_probe", "acquire_report"],
        why_inspect=(
            "re-fetching needs three free API keys and about 4 GB of "
            "downloads"),
        runs="reads the reachability probe and the acquisition manifest",
        status="Fourteen sources in a content-addressed cache, one SHA-256 "
               "per file. Licences audited; two paid sources will not be "
               "redistributed.",
        risk="A source moves, changes vintage, or turns out to forbid "
             "redistribution after we have built on it. `make probe` "
             "checks reachability BEFORE any download, so a dead URL is "
             "never confused with a broken parser.",
        body="""
Fourteen public sources, each hashed on the way in, so a later run can prove
it read the same bytes rather than hoping so.

The ordering matters more than it sounds. `make probe` tests every endpoint
before `make acquire` fetches anything. A project that discovers a dead URL
only after four gigabytes cannot tell a moved source from a parser bug, and
will spend a day on the wrong one.

Six sources cannot be fetched automatically and must be placed by hand. Two
of those are licensed — a paid CSV and two industry PDFs — and are
deliberately excluded from the public repository. The tables derived from
them ship; the originals do not. That is the licence being respected, not a
gap in the method.
""",
        nums=lambda L: [
            ("Sources probed", len(L("source_probe")["results"]),
             "source_probe.results"),
            ("Probed on", L("source_probe")["probed_on"],
             "source_probe.probed_on"),
            ("Sources acquired", len(L("acquire_report")["results"]),
             "acquire_report.results"),
        ],
        limits=[
            "Some sources are single-vintage snapshots that will not "
            "reproduce byte-for-byte if re-fetched later. "
            "`docs/DATA_SOURCES.md` names which ones.",
            "Hashing proves we read the same bytes. It does not prove the "
            "publisher was right.",
        ],
        nxt=[("docs/DATA_SOURCES.md",
              "every source, its licence, and how to fetch it")],
    ),
]
