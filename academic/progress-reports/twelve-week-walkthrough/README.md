# Siting Atlas — a twelve-week walkthrough

Twelve weeks, one question each, in the order the project actually has to be understood: data and its provenance first, then what the public record cannot see, then the three models, then why one of them failed, then what does work.

The project is **complete**. These pages pace how it is presented — they are not a claim about when the work happened. Every page prints the real `run_id` and build date of the artefact behind it.

| Week | Question | Mode |
|---|---|---|
| [01](weeks/WEEK-01.md) **Where every number comes from** | Can a stranger fetch every ingredient of this project themselves, and is each one licensed for that? | `INSPECT` |
| [02](weeks/WEEK-02.md) **A facility network read out of an image-only PDF** | The best public census of this operator's buildings is a PDF whose tables are pictures. Can it be recovered, and can the result be trusted? | `INSPECT` |
| [03](weeks/WEEK-03.md) **Typed layers and a star schema** | How do fourteen differently-shaped public files become one thing a model can query? | `INSPECT` |
| [04](weeks/WEEK-04.md) **The panel every model reads** | What is the unit of analysis, and how much of the country does it actually cover? | `INSPECT` |
| [05](weeks/WEEK-05.md) **What the public record cannot see** | Before modelling anything — how much of this network is visible in free public data at all? | `INSPECT` |
| [06](weeks/WEEK-06.md) **Which ZIP, given that one opening happens** | Conditional on a facility opening somewhere in a metro, can public data say which ZIP code it lands in? | `RECOMPUTE` |
| [07](weeks/WEEK-07.md) **A pre-registered test that was allowed to fail** | Which metro gets the next delivery station? And — committed in writing beforehand — what would count as getting that right? | `RECOMPUTE` |
| [08](weeks/WEEK-08.md) **Why it failed — a screening rule you can run first** | Was the failure about this model, or about what free public data can carry? And can you tell in advance? | `INSPECT` |
| [09](weeks/WEEK-09.md) **What it costs to put a parcel on a doorstep** | Forget prediction. Can free public data price the operation itself? | `RECOMPUTE` |
| [10](weeks/WEEK-10.md) **Replacing the model's depots with real buildings** | What changes when the depot layer stops being a solve and becomes the buildings the operator actually runs? | `RECOMPUTE` |
| [11](weeks/WEEK-11.md) **Five programmes that were retired** | What was built, run, and then taken out — and why is it still in the repository? | `INSPECT` |
| [12](weeks/WEEK-12.md) **The artefact itself** | Can a stranger clone this, run it, and get the same numbers — and can they tell when they have not? | `RECOMPUTE` |

`RECOMPUTE` weeks re-derive their result offline from a clone. `INSPECT` weeks read a shipped artefact, because that stage needs the raw source cache, three API keys, ~4 GB of downloads or ninety minutes of CPU.

## Running a week

```bash
bash run_week.sh 07        # run week 7 and print its summary
bash build.sh              # regenerate all twelve pages
```

The repository is found by walking up to `MSBA_Project/` and looking for `siting-atlas/`. Set `SITING_ATLAS=/path/to/clone` if yours lives elsewhere.

Nothing here writes to the repository except the artefacts a `RECOMPUTE` week legitimately rebuilds, so revising this narrative never touches the code it describes.
