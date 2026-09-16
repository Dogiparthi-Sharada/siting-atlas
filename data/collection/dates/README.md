# collection/dates — the separate date-lookup pass

Part of the labelling effort described in [`../README.md`](../README.md). The
classification prompts asked for a date too; this folder is the follow-up pass
that went back over the rows still without one.

```
  GEMINI_PROMPT_DATES.txt    the prompt, verbatim
  HOW_TO_LOOK_UP_DATES.txt   the written procedure a human follows for the
                             rows the model returned UNKNOWN for
  dates_found.csv            what this pass produced
```

Note the near-namesake: `../results/DATES_FOUND.csv` is a different, earlier
file. Lowercase `dates_found.csv` is this pass.
