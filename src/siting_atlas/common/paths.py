"""Canonical filesystem layout.

Every module resolves paths through here rather than composing them locally,
so the pipeline can be relocated (CI runner, notebook, another machine)
by changing one environment variable.

Layer names follow docs/defense/HANDBOOK_07_ENGINEERING.md:

    L0  data/raw        immutable, content-addressed, write-once
    L1  data/interim    one typed parquet per source
    L2  data/processed  warehouse + marts
    L3  data/processed  the single feature panel every model reads
    L4  outputs         model artefacts, metrics, figures
"""

from __future__ import annotations

import os
from pathlib import Path

# Repo root is four levels up from this file:
#   src/siting_atlas/common/paths.py -> siting_atlas -> src -> <root>
_DEFAULT_ROOT = Path(__file__).resolve().parents[3]

# Resolved, not taken verbatim. `rel()` compares against `path.resolve()`, so
# a root given relatively (SITING_ATLAS_ROOT=.) or through a symlink would
# never match and every log line would print an absolute path instead of a
# repo-relative one — quietly, since rel() falls back rather than raising.
ROOT = Path(os.environ.get("SITING_ATLAS_ROOT", _DEFAULT_ROOT)).resolve()

DATA = ROOT / "data"
RAW = DATA / "raw"            # L0  never edited in place
INTERIM = DATA / "interim"    # L1  typed parquet
PROCESSED = DATA / "processed"  # L2/L3 warehouse and feature panel
EXTERNAL = DATA / "external"  # manually placed files (keyed sources)

OUTPUTS = ROOT / "outputs"
MODELS = OUTPUTS / "models"
METRICS = OUTPUTS / "metrics"
TABLES = OUTPUTS / "tables"
RUN_FIGURES = OUTPUTS / "figures"   # figures generated FROM results
AUDIT = OUTPUTS / "audit"           # one record per gated mutation
#: Resume state, NOT results. `outputs/metrics` is the citable set -- under
#: the project's "cite the artefact, not the figure" rule, anything in it is
#: quotable, and a per-split checkpoint dump is not a thing to quote. Two of
#: them (percapita_repeats.json 2.3 MB, logrel_repeats.json 6.9 MB) were
#: sitting there as 9.2 MB of intermediate fits beside 41 deliverables.
#: Nothing is ever cited from here and nothing here needs a run stamp.
SCRATCH = OUTPUTS / "scratch"

DOCS = ROOT / "docs"
DOC_FIGURES = DOCS / "figures"      # figures embedded in the proposal
REPRO = ROOT / "reproducibility"

MANIFEST = RAW / "manifest.jsonl"
WAREHOUSE = PROCESSED / "siting_atlas.duckdb"
PANEL = PROCESSED / "panel.parquet"

# Directories the pipeline is allowed to create on demand. data/raw is
# included because the cache writes into per-source subdirectories.
_WRITABLE = (RAW, INTERIM, PROCESSED, EXTERNAL, OUTPUTS, MODELS, METRICS,
             TABLES, RUN_FIGURES, AUDIT, SCRATCH)


def ensure_dirs() -> None:
    """Create every writable directory. Idempotent; safe to call anywhere."""
    for d in _WRITABLE:
        d.mkdir(parents=True, exist_ok=True)


def checkpoint(name: str) -> Path:
    """Where a resumable run's per-split dump lives.

    New checkpoints go to ``outputs/scratch``. An EXISTING one under
    ``outputs/metrics`` still wins, so relocating the directory can never
    silently discard a half-finished search and restart a run that takes
    hours. Delete the legacy file once its search artefact is written and
    the next run moves itself.
    """
    legacy = METRICS / name
    return legacy if legacy.exists() else SCRATCH / name


def rel(path: Path | str) -> str:
    """Path relative to the repo root, for logs that stay readable."""
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except ValueError:
        return str(path)
