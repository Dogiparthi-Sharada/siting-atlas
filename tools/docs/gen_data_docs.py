"""Generate docs/data/ from the source registry and the last probe.

Hand-written source documentation drifts from the code within weeks. These
pages are generated instead, so the licence, endpoint, grain and measured
reachability in the docs are the same values the pipeline actually uses.

    python tools/docs/gen_data_docs.py

Writes docs/data/README.md plus one page per source. Re-run after editing
src/siting_atlas/ingest/sources.py or after a fresh probe.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from siting_atlas.ingest.sources import (  # noqa: E402
    ANALYTICAL, SOURCES, Availability, Source)

OUT = ROOT / "docs" / "data"
PROBE = ROOT / "outputs" / "metrics" / "source_probe.json"

STATUS_NOTE = {
    Availability.OPEN: (
        "Downloads with no credential. `make acquire` fetches it."),
    Availability.NEEDS_KEY: (
        "Reachable, but the provider requires a free API key. The pipeline "
        "skips it with a remediation message until the key is present."),
    Availability.BLOCKED: (
        "The host refuses requests from this network. Download manually and "
        "place the file in `data/external/`."),
    Availability.MANUAL: (
        "No stable machine-readable endpoint. The file is placed by hand."),
}

BADGE = {Availability.OPEN: "OPEN", Availability.NEEDS_KEY: "NEEDS KEY",
         Availability.BLOCKED: "BLOCKED", Availability.MANUAL: "MANUAL"}

#: The hand-written pages in docs/data/, indexed here so the index cannot rot
#: the way it did before 2026-09-15, when twelve of the folder's documents --
#: including the two largest -- were reachable only by listing the directory.
#: Grouped, ordered within a group by what a stranger should read first.
#:
#: This lives in the GENERATOR rather than in the output because the output is
#: overwritten by `main()`. A hand-edited index would survive exactly until the
#: next run. Adding a page here is the whole maintenance cost; `main()` prints
#: a warning naming any .md in docs/data/ that is neither generated nor listed.
HAND_WRITTEN: list[tuple[str, list[tuple[str, str]]]] = [
    ("The target variable, and how far to trust it", [
        ("FACILITY_PANEL_PROVENANCE.md",
         "**Read this before quoting any date.** How the panel was built "
         "from OSHA enforcement records, the four collection methods that "
         "failed first, and the central caveat: `open_date` is an upper "
         "bound, not an opening. Selection bias quantified, defects listed "
         "with their fix status. The longest document in the folder."),
        ("PANEL_EXPANSION.md",
         "Merging the MWPVL 2025 Q1 extraction into the panel: every "
         "decision, both duplicate screens, and what the 693-row file "
         "admits and rejects."),
        ("MWPVL_OCR_PIPELINE.md",
         "The OCR pipeline that turned thirteen table images into "
         "`mwpvl_facilities.csv`, with three validations attached before "
         "anything consumed it."),
        ("MWPVL_2025.md",
         "The source article itself: what it is, why it is unregistered, "
         "and why its publisher withdrawing it does not break provenance."),
        ("GEOCODING.md",
         "Geocoding the panel: 72.3% Match on 693 rows, and why the points "
         "are not yet joined into the panel."),
        ("FACILITY_PANEL_HOWTO.md",
         "The brief that started the panel. Superseded as status, still the "
         "fastest route for anyone adding a source."),
        ("SATELLITE.md",
         "The failed attempt at the same quantity: 36% of its own estimates "
         "date construction after OSHA proved the building was operating. "
         "A negative result, reported as one."),
        ("NLRB.md",
         "Case filings as a delivery-station-skewed second source, and the "
         "capture-recapture coverage ceiling they support."),
    ]),
    ("Data quality — the audit, the literature, and the log", [
        ("DATA_QUALITY.md",
         "The audit of this pipeline against the published cleaning "
         "literature. Findings F1-F5, each with the measurement behind it. "
         "The second-longest document in the folder and the one a reviewer "
         "will open."),
        ("CLEANING_LITERATURE.md",
         "The data-cleaning argument, written after the papers were "
         "actually read: Fellegi-Holt, Rahm & Do, Van den Broeck, Winkler. "
         "What each licenses and what it does not."),
        ("CLEANING_CHANGELOG.md",
         "Every cleaning decision, dated, with the uncorrected-against-"
         "corrected cross-tab Van den Broeck asks for."),
        ("UNCERTAINTY.md",
         "500 joint draws over every documented parameter. How far the "
         "answer moves when all of them move at once — and the three "
         "fields that were not sampled, with reasons."),
    ]),
    ("The cost and portfolio layer", [
        ("COST_MODEL.md",
         "The cost model explained from zero: why the answer turns on "
         "delivery density and depot distance, and how to read its table."),
        ("PARAMETERS.md",
         "Every free parameter, its source, and what it is worth. Names the "
         "constants that have no published source and measures how far the "
         "headline moves when each one is swept."),
        ("HIGHWAY_ACCESS.md",
         "Highway access built and measured on 14,767 ZCTAs. It does not "
         "move the model, and that is the finding."),
        ("CBP_DETAIL.md",
         "County Business Patterns detail — in use by the choice model, and "
         "its lag guard is nominal. Unregistered."),
        ("OSM_LANDUSE.md",
         "OpenStreetMap land use: built, verified on three metros, blocked "
         "on Overpass. Unregistered."),
    ]),
    ("Operating the data layer", [
        ("ACQUISITION_GUIDE.md",
         "What to download by hand, where to put it, and how to check it "
         "landed. Covers the six sources that do not fetch automatically, "
         "in priority order."),
        ("ARTEFACTS.md",
         "Every JSON file in `outputs/metrics/`, reconciled against disk: "
         "what wrote it, when, and whether anything still reads it."),
        ("FIGURES.md",
         "The figure layer — what draws what, and what each figure depends "
         "on, confirmed by following the imports."),
    ]),
]


def hand_written_section() -> list[str]:
    """Markdown for the index of the folder's hand-written pages."""
    lines = [
        "## The hand-written pages",
        "",
        "Everything above is generated from the registry. The pages below "
        "are written by hand, and they are where the reasoning lives.",
        "",
    ]
    for heading, entries in HAND_WRITTEN:
        lines += [f"### {heading}", ""]
        for name, note in entries:
            lines.append(f"- [`{name}`]({name}) — {note}")
        lines.append("")
    return lines


def load_probe() -> dict:
    """Read the last source probe, or an empty dict if none has run.

    Empty rather than raising: the docs must still build on a machine
    that has never had network access, just without liveness columns.
    """
    if not PROBE.exists():
        return {}
    data = json.loads(PROBE.read_text())
    return {r["key"]: r for r in data.get("results", [])}, data.get(
        "probed_on", "not recorded")


def page(src: Source, probe: dict, probed_on: str) -> str:
    """Markdown for one source's data-dictionary page."""
    p = probe.get(src.key, {})
    lag = ("not applicable" if src.lag_months is None
           else f"{src.lag_months:g} months")

    lines = [
        f"# {src.title}",
        "",
        f"**Registry key:** `{src.key}`  ·  **Status:** {BADGE[src.availability]}",
        "",
        "> " + STATUS_NOTE[src.availability],
        "",
        "## At a glance",
        "",
        "| | |",
        "|---|---|",
        f"| Provider | {src.provider} |",
        f"| Grain | `{src.grain.value}` |",
        f"| Role in the model | {src.role} |",
        f"| Update cadence | {src.cadence or 'not recorded'} |",
        f"| Reporting lag | {lag} |",
        f"| Licence | {src.licence} |",
        f"| Credential | {'`$' + src.key_env + '`' if src.key_env else 'none'} |",
    ]
    if src.vintages:
        # A series published one file per year is a different thing to acquire
        # than a single current file, so say so rather than making the reader
        # infer it from a {yy} placeholder in the URL.
        lines.append(f"| Vintages fetched | {len(src.vintages)} "
                     f"(20{src.vintages[0]}–20{src.vintages[-1]}) |")
    lines.append("")
    if src.docs_url:
        lines += ["Provider documentation:", "", "```", src.docs_url, "```"]
    lines += ["", "## Endpoint", ""]
    if src.url:
        lines += ["```", src.url, "```", ""]
        lines.append("Placeholders such as `{year}` are substituted from the "
                     "pinned vintage map in `ingest/acquire.py`. Vintages are "
                     "pinned deliberately: a silent vintage change is the "
                     "failure mode that corrupts a panel without raising.")
    else:
        lines.append("No stable endpoint. See the acquisition note below.")

    lines += ["", "## Measured reachability", ""]
    if p:
        lines += [
            f"Probed **{probed_on}** from the build environment.",
            "",
            "| | |",
            "|---|---|",
            f"| Verdict | `{p.get('verdict', '?')}` |",
            f"| HTTP status | {p.get('status') or 'n/a'} |",
            f"| Content-Type | `{p.get('content_type') or 'n/a'}` |",
            f"| Round trip | {p.get('seconds', '?')}s |",
        ]
        if p.get("detail"):
            lines.append(f"| Detail | {p['detail']} |")
        lines += ["",
                  "Re-measure with `python -m siting_atlas.ingest.probe`. "
                  "The probe compares the live result against the declared "
                  "status and warns on drift."]
    else:
        lines.append("No probe on record. Run "
                     "`python -m siting_atlas.ingest.probe`.")

    if src.fields:
        lines += ["", "## Fields used", "",
                  "".join(f"- `{f}`\n" for f in src.fields).rstrip()]

    if src.notes:
        lines += ["", "## Notes", "", src.notes]

    if src.availability in (Availability.BLOCKED, Availability.MANUAL):
        lines += [
            "", "## Acquisition procedure", "",
            f"1. Open {src.docs_url or 'the provider site'} in a browser.",
            "2. Download the file described above.",
            f"3. Place it in `data/external/{src.key}/` keeping the original "
            "filename.",
            "4. Record the download date and the source URL in "
            "`data/raw/manifest.jsonl` so provenance stays complete.",
            "",
            "The pipeline treats a missing manual source as a skipped stage "
            "with a stated reason, not as a failure — the rest of the run "
            "still executes.",
        ]

    lines += ["", "---", "",
              "*Generated from `src/siting_atlas/ingest/sources.py`. Do not "
              "edit by hand — run `python tools/docs/gen_data_docs.py`.*", ""]
    return "\n".join(lines)


def index(probe: dict, probed_on: str) -> str:
    """Markdown for the index that links every source page."""
    rows = []
    for s in SOURCES:
        v = probe.get(s.key, {}).get("verdict", "-")
        rows.append(
            f"| [{s.key}]({s.key}.md) | {s.title} | `{s.grain.value}` | "
            f"{BADGE[s.availability]} | `{v}` | "
            f"{'—' if s.lag_months is None else f'{s.lag_months:g} mo'} |")

    counts = {a: sum(1 for s in SOURCES if s.availability is a)
              for a in Availability}

    return "\n".join([
        "# Data sources",
        "",
        f"{len(SOURCES)} registered sources; {len(ANALYTICAL)} feed the "
        "analytical panel. OpenStreetMap is infrastructure rather than an "
        "analytical source — it is consumed once, offline, to produce the "
        "drive-time matrix, after which every artefact is deleted (ADR-0002).",
        "",
        "## Status summary",
        "",
        "| Status | Count | Meaning |",
        "|---|---|---|",
        f"| OPEN | {counts[Availability.OPEN]} | Acquired automatically |",
        f"| NEEDS KEY | {counts[Availability.NEEDS_KEY]} | Free credential "
        "required |",
        f"| BLOCKED | {counts[Availability.BLOCKED]} | Refused by this "
        "network; manual download |",
        f"| MANUAL | {counts[Availability.MANUAL]} | No stable endpoint |",
        "",
        "## Registry",
        "",
        "| Key | Source | Grain | Declared | Probed | Lag |",
        "|---|---|---|---|---|---|",
        *rows,
        "",
        f"Reachability last measured **{probed_on}**.",
        "",
        *hand_written_section(),
        "## The rule these sources obey",
        "",
        "> Every source must be free, public, and re-downloadable by a "
        "stranger.",
        "",
        "This is the contribution, not a budget constraint. A model built on "
        "licensed data produces conclusions nobody can check, which is "
        "precisely the situation the project exists to fix. Where a better "
        "paid source exists we take the public one and report the cost of "
        "that choice.",
        "",
        "## Provenance",
        "",
        "Every download is written once into "
        "`data/raw/<source>/<hash>.<ext>` and appended to "
        "`data/raw/manifest.jsonl` with its SHA-256, byte count, "
        "Content-Type and the run that fetched it. A reviewer can "
        "re-download from the recorded URLs and verify the hashes.",
        "",
        "## Commands",
        "",
        "```bash",
        "python -m siting_atlas.ingest.acquire --list      # show registry",
        "python -m siting_atlas.ingest.probe               # measure "
        "reachability",
        "python -m siting_atlas.ingest.acquire             # fetch what is "
        "reachable",
        "python -m siting_atlas.ingest.acquire --include-large",
        "```",
        "",
        "---",
        "",
        "*Generated from the registry. Run "
        "`python tools/docs/gen_data_docs.py` after changing sources.*",
        "",
    ])


def unindexed() -> list[str]:
    """Pages in docs/data/ that are neither generated nor in HAND_WRITTEN.

    The index rotted once by growing quietly. This is the check that would
    have caught it: it is a report, not a failure, because adding a document
    should not break the docs build.
    """
    generated = {"README.md"} | {f"{s.key}.md" for s in SOURCES}
    listed = {n for _, entries in HAND_WRITTEN for n, _ in entries}
    return sorted(p.name for p in OUT.glob("*.md")
                  if p.name not in generated and p.name not in listed)


def main() -> int:
    """Regenerate docs/data/ from the source registry. Returns 0."""
    OUT.mkdir(parents=True, exist_ok=True)
    loaded = load_probe()
    probe, probed_on = loaded if loaded else ({}, "not recorded")

    (OUT / "README.md").write_text(index(probe, probed_on), encoding="utf-8")
    for src in SOURCES:
        (OUT / f"{src.key}.md").write_text(page(src, probe, probed_on),
                                           encoding="utf-8")
    print(f"  wrote {len(SOURCES) + 1} pages to docs/data/")

    missing = unindexed()
    if missing:
        print(f"  WARNING: {len(missing)} page(s) in docs/data/ are in no "
              "index. Add them to HAND_WRITTEN in this file:")
        for name in missing:
            print(f"    {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
