"""Render the twelve week pages, and print one week's summary on demand.

    python lib/build_weeks.py build        write weeks/WEEK-01..12.md + index
    python lib/build_weeks.py show 7       print week 7's summary to stdout

Reads the siting-atlas repository read-only. Nothing in this directory
writes to the repository, which is why the walkthrough can be revised
without touching the code it describes or enlarging the upload delta.

The repository is located by walking up from this file to MSBA_Project and
looking for ``siting-atlas``; ``SITING_ATLAS`` in the environment overrides
that, for a clone kept somewhere else.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import spec  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(ROOT, "weeks")

_default_repo = os.path.abspath(
    os.path.join(ROOT, "..", "..", "..", "siting-atlas"))
REPO = os.environ.get("SITING_ATLAS", _default_repo)

_LEAD = ("> **Week {n} of 12.** The project is finished; these twelve pages "
         "pace how it is walked through, one week at a time. ")

_TAIL = ("Nothing below is typed in. ")

# Two banners, because one of them was false on one page. Week 11 owns no
# artefact -- its table is a listing of experiments/ -- so the original
# "read out of the artefact named beside it" was simply untrue there.
BANNER_ARTEFACT = (
    _LEAD + _TAIL +
    "Every number is read out of the artefact named beside it at build "
    "time, and each artefact carries the real `run_id` and build date of "
    "the run that produced it, so the actual chronology is on the page.")

BANNER_DIRS = (
    _LEAD + _TAIL +
    "This week has no metrics artefact: its table is the archive "
    "directory, read at build time, so adding or removing a programme "
    "changes the page with nobody editing it.")

# Why a week is INSPECT differs per week, so each states its own reason.
# A single shared sentence claimed "needs the raw cache, API keys or ~90
# minutes" on all seven, which was true of some and false of others --
# listing a directory needs none of those.
MODE_NOTE = {
    "RECOMPUTE": "the command below re-derives this result offline from the "
                 "clone, so the number is demonstrated, not quoted",
    # "what already exists" rather than "a shipped artefact": week 11
    # reads a directory, so naming an artefact was wrong there too.
    "INSPECT": "the command below reads what already ships and recomputes "
               "nothing, so the number is reported rather than demonstrated",
}


class Missing(dict):
    """A stand-in so one absent artefact cannot take the whole build down."""


def loader(entry: dict):
    """``L(name)`` -> artefact dict, from metrics or an explicit path."""
    cache: dict[str, dict] = {}
    paths = {a: f"outputs/metrics/{a}.json"
             for a in entry.get("artefacts", [])}
    paths.update(entry.get("extra_json", {}))

    # Any metrics file is loadable, not just this week's: week 10 divides
    # its median by week 9's, so it must reach an artefact it does not own.
    def L(name: str) -> dict:
        if name in cache:
            return cache[name]
        rel = paths.get(name, f"outputs/metrics/{name}.json")
        full = os.path.join(REPO, rel)
        try:
            with open(full, encoding="utf-8") as fh:
                cache[name] = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"  ! cannot read {rel}: {exc}", file=sys.stderr)
            cache[name] = Missing()
        return cache[name]
    return L, paths


def stamp(rel: str) -> str:
    """``run_id`` and build date for an artefact, or a plain 'not found'."""
    full = os.path.join(REPO, rel)
    if not os.path.exists(full):
        return "not found"
    try:
        with open(full, encoding="utf-8") as fh:
            d = json.load(fh)
        rid = d.get("run_id", "unstamped")
        when = str(d.get("written_at", ""))[:10]
    except (OSError, json.JSONDecodeError):
        rid, when = "unreadable", ""
    if not when:
        # Fallback only, for an artefact with no written_at. Local date is
        # what a reader wants here; the UTC instant is not the point.
        when = dt.datetime.fromtimestamp(
            os.path.getmtime(full), tz=dt.UTC).date().isoformat()
    return f"run `{rid}` · built {when}"


def listing(rel: str):
    """One row per sub-directory, so a ``dirs`` week has something to show.

    Week 11 is the archive of retired programmes. It owns no metrics
    artefact, so it rendered and printed an EMPTY table while its own page
    claimed it "lists experiments/" — a week that describes itself doing
    something and then does nothing. This makes the claim true: the
    directory is read at build time, so a programme added to or removed
    from the archive changes the page without anyone editing it.
    """
    full = os.path.join(REPO, rel)
    if not os.path.isdir(full):
        return [], f"no such directory: {rel}"
    names = sorted(d for d in os.listdir(full)
                   if os.path.isdir(os.path.join(full, d)))
    rows = []
    for d in names:
        n = sum(len(fs) for _, _, fs in os.walk(os.path.join(full, d)))
        rows.append((d, f"{n} files", f"{rel}/{d}/"))
    # "Directories", not "programmes". Five of these are retired research
    # programmes; `retired-tests` and `superseded-artefacts` are archives of
    # other things entirely. Labelling the count "programmes archived" made
    # the page report 7 directly under a title saying five, which is the
    # kind of small contradiction a reader is right to stop at.
    rows.append(("Directories in the archive", len(names), f"{rel}/"))
    return rows, None


def numbers(entry: dict):
    """``nums`` evaluated, with a failure reported rather than swallowed."""
    if entry.get("dirs"):
        return listing(entry["dirs"])
    L, _ = loader(entry)
    try:
        return list(entry["nums"](L)), None
    except Exception as exc:
        return [], f"{type(exc).__name__}: {exc}"


def render(entry: dict) -> str:
    n = entry["n"]
    _, paths = loader(entry)
    rows, err = numbers(entry)

    banner = BANNER_DIRS if entry.get("dirs") else BANNER_ARTEFACT
    mode = f"**{entry['mode']}** — {MODE_NOTE[entry['mode']]}"
    if entry.get("why_inspect"):
        mode += f". Why not recomputed here: {entry['why_inspect']}"
    out = [f"# Week {n} of 12 — {entry['title']}", "",
           banner.format(n=n), "",
           "| | |", "|---|---|",
           f"| **Question** | {entry['question']} |",
           f"| **Run it** | `bash run_week.sh {n:02d}` |",
           f"| **Mode** | {mode} |",
           f"| **What runs** | {entry['runs']} |"]
    if entry.get("secs"):
        # Measured, not estimated -- the week was actually run and timed.
        # Stated with the machine caveat because a wall time without one is
        # a promise the reader's laptop may not keep.
        note = entry.get("measured_note")
        out.append(f"| **Measured** | {entry['secs']}s on the author's "
                   f"machine, offline, no API keys"
                   + (f" — {note}" if note else "") + " |")
    out.extend(f"| **Artefact** | `{rel}` · {stamp(rel)} |"
               for rel in paths.values())
    if entry.get("dirs"):
        out.append(f"| **Directory** | `{entry['dirs']}/` |")
    out += ["", "## What this stage does", entry["body"].strip(), ""]

    if err:
        out += ["## What came back", "",
                f"> Could not read the artefact: `{err}`. Rebuild it in the "
                f"repository, then re-run `bash build.sh`.", ""]
    elif rows:
        out += ["## What came back", "",
                "| Measure | Value | Read from |", "|---|---|---|"]
        out += [f"| {a} | **{b}** | `{c}` |" for a, b, c in rows]
        out.append("")

    out += ["## What this week does *not* establish", ""]
    out += [f"- {x}" for x in entry["limits"]]
    out += ["", "## Read next", ""]
    out += [f"- [`{p}`](../../../../siting-atlas/{p}) — {why}"
            for p, why in entry["nxt"]]
    prev = f"[← Week {n - 1}](WEEK-{n - 1:02d}.md)" if n > 1 else ""
    nxt = f"[Week {n + 1} →](WEEK-{n + 1:02d}.md)" if n < 12 else ""
    out += ["", "---", "",
            " · ".join(x for x in (prev, "[Index](../README.md)", nxt) if x),
            ""]
    return "\n".join(out)


def index() -> str:
    out = ["# Siting Atlas — a twelve-week walkthrough", "",
           "Twelve weeks, one question each, in the order the project "
           "actually has to be understood: data and its provenance first, "
           "then what the public record cannot see, then the three models, "
           "then why one of them failed, then what does work.", "",
           "The project is **complete**. These pages pace how it is "
           "presented — they are not a claim about when the work happened. "
           "Every page prints the real `run_id` and build date of the "
           "artefact behind it.", "",
           "| Week | Question | Mode |", "|---|---|---|"]
    out.extend(f"| [{w['n']:02d}](weeks/WEEK-{w['n']:02d}.md) "
               f"**{w['title']}** | {w['question']} | `{w['mode']}` |"
               for w in spec.WEEKS)
    out += ["",
            "`RECOMPUTE` weeks re-derive their result offline from a clone. "
            "`INSPECT` weeks read a shipped artefact, because that stage "
            "needs the raw source cache, three API keys, ~4 GB of downloads "
            "or ninety minutes of CPU.", "",
            "## Running a week", "", "```bash",
            "bash run_week.sh 07        # run week 7 and print its summary",
            "bash build.sh              # regenerate all twelve pages",
            "```", "",
            "The repository is found by walking up to `MSBA_Project/` and "
            "looking for `siting-atlas/`. Set "
            "`SITING_ATLAS=/path/to/clone` if yours lives elsewhere.", "",
            "Nothing here writes to the repository except the artefacts a "
            "`RECOMPUTE` week legitimately rebuilds, so revising this "
            "narrative never touches the code it describes.", ""]
    return "\n".join(out)


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "show":
        e = spec.week(int(sys.argv[2]))
        rows, err = numbers(e)
        print(f"\n  Week {e['n']} of 12 — {e['title']}")
        print(f"  {e['question']}")
        print(f"  mode {e['mode']} · {e['runs']}\n")
        for a, b, c in rows:
            print(f"    {a:34s} {b!s:>28s}   {c}")
        if err:
            print(f"    ! {err}")
        print()
        return 1 if err else 0

    os.makedirs(OUT, exist_ok=True)
    bad = 0
    for e in spec.WEEKS:
        p = os.path.join(OUT, f"WEEK-{e['n']:02d}.md")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(render(e))
        rows, err = numbers(e)
        bad += bool(err)
        print(f"  WEEK-{e['n']:02d}.md  {len(rows):2d} numbers  "
              f"{'ERROR: ' + err if err else e['title']}")
    with open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8") as fh:
        fh.write(index())
    print("  README.md   index of 12")
    print(f"\n  repository: {REPO}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
