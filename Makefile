# One target per pipeline stage, so anyone can rebuild anything
# without reading the code.
#
# Every target below has been run. A target that names a module which does
# not exist is worse than no target: it tells a newcomer the stage is built
# when it is not, and they lose an afternoon finding out. If a stage is not
# written yet it does not get a line here.

PY ?= python
.DEFAULT_GOAL := help

help:  ## show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN{FS=":.*?## "};{printf "  \033[36m%-18s\033[0m %s\n",$$1,$$2}'

install:  ## editable install + dev tooling (do this first)
	$(PY) -m pip install -e ".[dev,viz,docs]"

probe:  ## L0 - check every source is still reachable (network, no keys)
	$(PY) -m siting_atlas.ingest.probe

acquire:  ## L0 - fetch sources into the cache (needs CENSUS/EIA keys)
	$(PY) -m siting_atlas.ingest.acquire

normalise:  ## L1 - one typed parquet per keyless source
	$(PY) -m siting_atlas.ingest.normalise

normalise-external:  ## L1 - the same for hand-placed files in data/external
	$(PY) -m siting_atlas.ingest.normalise_external

warehouse:  ## L2 - parquet -> the DuckDB star schema
	$(PY) -m siting_atlas.warehouse.schema

panel:  ## L3 - the ZCTA-quarter panel every model reads
	$(PY) -m siting_atlas.warehouse.panel

# --all-scenarios matters and its absence here was a real bug. Without it the
# runner writes a baseline-only cost_report.json, silently dropping the depot
# count, the cost decomposition and the five sensitivity scenarios that the
# README, STATUS and the paper all cite. CI always passed the flag; this
# target did not, so `make cost` quietly produced a thinner artefact than CI.
cost:  ## L4 - cost to serve, per pilot ZCTA, all five scenarios
	$(PY) -m siting_atlas.cost.runner --all-scenarios

model:  ## L4 - fit the conditional choice model (which ZIP, given one opening)
	$(PY) -m siting_atlas.models.choice_runner

metro:  ## L4 - the pre-registered metro-level entry test (which metro, next year)
	$(PY) -m siting_atlas.models.metro_entry

refit:  ## L4 - refit the choice model on the full expanded panel
	$(PY) -m siting_atlas.models.refit_expanded

covariates:  ## L4 - the covariate search. SLOW: ~90 min on 2 workers
	$(PY) -m siting_atlas.models.covariate_search --workers 2

scope:  ## L5 - measure study scope into outputs/metrics/scope.json
	$(PY) -m siting_atlas.report.scope

figures:  ## L5 - result figures from the cost tables into outputs/figures
	$(PY) -m siting_atlas.viz.build

app:  ## serve the cost-to-serve dashboard (needs `make cost` first)
	bash scripts/run_dashboard.sh

# Four stages are deliberately out of `all`. `acquire` needs credentials and
# hits the network, and everything downstream reads the cache it already
# filled. `app` blocks on a server. `covariates` runs for about ninety
# minutes. `metro` is a one-off pre-registered test, not a pipeline stage.
all: normalise normalise-external warehouse panel cost model scope \
     figures  ## offline pipeline, L1 through L5

# THE ONE THAT MATTERS TO A NEWCOMER. These four stages run from a fresh
# clone with no network access and no API keys, because data/processed/
# panel.parquet and data/interim/cbp_detail.parquet ship with the repository.
reproduce: cost model scope figures  ## headline results, offline, no keys

docs:  ## regenerate figures, proposal, deck and text docs
	bash scripts/build_all.sh

lint:  ## ruff over the package and its tests
	ruff check src tests

lint-tools:  ## ruff over the document builders (not a merge gate - see pyproject)
	ruff check --no-cache --config 'extend-exclude = []' tools

fmt:  ## apply ruff's safe fixes
	ruff check --fix src tests

test:  ## run the test suite with coverage
	pytest --cov=siting_atlas --cov-report=term-missing

clean:  ## remove build and cache artifacts
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache .mypy_cache dist build

.PHONY: help install probe acquire normalise normalise-external warehouse \
        panel cost model metro refit covariates scope figures app all \
        reproduce docs lint lint-tools fmt test clean

# Retired work lives in experiments/ and has no targets here on purpose. The
# hazard model, the gravity/network arms, the per-capita and log-relative
# searches, the portfolio optimiser and the agent demo were all removed from
# src/ on 2026-09-15. Their code, artefacts and notes are archived with an
# index at experiments/README.md. Nothing in src/ imports any of it.
