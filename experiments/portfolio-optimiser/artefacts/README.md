# portfolio-optimiser/artefacts

The output of the programme described in
[`../../README.md`](../../README.md#portfolio-optimiser).

`portfolio_report.json` is the $2 bn selection; `montecarlo_report.json`
summarises 500 draws over the documented cost and portfolio parameters. The
per-draw rows are still in `outputs/tables/montecarlo_draws.parquet` and the
selection in `outputs/tables/portfolio_2023q4.parquet`.

**The Monte Carlo is not a confidence interval.** Every range comes from
`docs/data/PARAMETERS.md` and was chosen by this project, so it propagates our
priors and not the world's — and one parameter was never sampled, so every
band is a floor.
