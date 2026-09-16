# agent-demo/artefacts

The audit trail the gate pipeline wrote, from the programme described in
[`../../README.md`](../../README.md#agent-demo).

`demo-plano-0001.json` is the per-mutation record a human opens;
`mutations.jsonl` is the append-only log an analysis reads. Both were written
on **every** invocation including the rejections — deliberately, because "it
never let a bad write through" is only a claim if the attempts were logged.
