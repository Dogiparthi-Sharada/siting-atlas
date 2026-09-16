# reproducibility/seals — the pre-registration, kept byte-exact

```
  PREREG_METRO_MODEL.946f7ef7.md   a byte-identical copy of
                                   docs/PREREG_METRO_MODEL.md
  SHA.md5                          its md5, in md5sum format
```

## Why a second copy of a file that is already in the repository

`docs/PREREG_METRO_MODEL.md` fixed the hypothesis, the arms and the success
criterion of the metro entry model **before** it was fitted. Its md5 is
recorded inside the result (`outputs/metrics/metro_entry.json:prereg_md5`) and
CI fails if the two ever disagree — see
[`../../.github/README.md`](../../.github/README.md).

That gate is the right shape but it has one bad failure mode: when it goes
red, the obvious repairs are both wrong. Re-running `make metro` re-stamps
`prereg_md5` from whatever is on disk, which makes a broken seal invisible.
Editing the pre-registration to match is worse. **The only honest repair is to
put the original bytes back**, and that requires having them.

An extra 9 KB buys that.

## Restoring a broken seal

```bash
cp reproducibility/seals/PREREG_METRO_MODEL.946f7ef7.md docs/PREREG_METRO_MODEL.md
```

Then verify — both lines must print the same hash:

```bash
md5sum -c reproducibility/seals/SHA.md5        # checks docs/PREREG_METRO_MODEL.md
python -c "import json;print(json.load(open('outputs/metrics/metro_entry.json'))['prereg_md5'])"
```

Both currently read `946f7ef75db69e5278eea409a04c3823`, which is also the
suffix in the sealed copy's filename — so the file names its own hash and a
silent swap is visible from an `ls`.

## What does not belong here

Corrections. Anything found wrong with the pre-registration after the fact
goes in `docs/PREREG_METRO_MODEL_ERRATA.md`, which is deliberately outside the
hash. A sealed document that can be quietly amended is not sealed.
