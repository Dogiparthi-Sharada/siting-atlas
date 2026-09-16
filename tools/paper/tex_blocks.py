"""Parse the narrow LaTeX subset this paper actually uses into blocks.

Not a LaTeX implementation and not trying to be. The paper uses eleven
environments and about a dozen inline commands, all of them counted before
this was written, so the parser handles exactly those and raises on anything
it does not recognise rather than silently dropping it. A converter that
quietly swallows a table is worse than one that stops.

Blocks are ``(kind, payload)`` tuples. Inline markup is resolved separately by
:func:`runs`, which returns ``(text, style)`` pairs so the renderer can stay
ignorant of LaTeX.
"""

from __future__ import annotations

import re

# ----------------------------------------------------------------- inline

_ESCAPES = [
    (r"\\%", "%"), (r"\\&", "&"), (r"\\\$", "$"), (r"\\_", "_"),
    (r"\\#", "#"), (r"\{,\}", ","), (r"\\,", "\u2009"),
    (r"---", "\u2014"), (r"--", "\u2013"),
    (r"``", "\u201c"), (r"''", "\u201d"), (r"`", "\u2018"),
    (r"\\times", "\u00d7"), (r"\\approx", "\u2248"), (r"\\leq", "\u2264"),
    (r"\\geq", "\u2265"), (r"\\pm", "\u00b1"), (r"\\alpha", "\u03b1"),
    (r"\\beta", "\u03b2"), (r"\\theta", "\u03b8"), (r"\\sim", "~"),
    (r"\\ldots", "\u2026"), (r"\\dots", "\u2026"),
    (r"\\S", "\u00a7"), (r"\\delta", "\u03b4"), (r"\\Delta", "\u0394"),
    (r"\\lambda", "\u03bb"), (r"\\mu", "\u03bc"), (r"\\sigma", "\u03c3"),
    (r"\\rho", "\u03c1"), (r"\\to", "\u2192"), (r"\\cdot", "\u00b7"),
    (r"~", "\u00a0"), (r"\\sum", "\u03a3"), (r"\\prod", "\u03a0"),
    (r"\\in\b", "\u2208"), (r"\\infty", "\u221e"), (r"\\neq", "\u2260"),
    (r"\\le\b", "\u2264"), (r"\\ge\b", "\u2265"), (r"\\equiv", "\u2261"),
]

_CMD = re.compile(r"\\(emph|textbf|texttt|textit|underline|text|mathrm)\{")


def _matching(s: str, start: int) -> int:
    """Index just past the brace group opened at ``start``."""
    depth = 0
    for i in range(start, len(s)):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    raise ValueError(f"unbalanced brace near: {s[start:start + 60]!r}")


def _plain(s: str) -> str:
    # Structured math first: these carry braces that the generic cleanup at
    # the end would otherwise leave stranded in the output.
    s = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"\1/\2", s)
    # Not a raw string: re reads r"\u221a" in a replacement as a bad escape.
    s = re.sub(r"\\sqrt\{([^{}]*)\}", "\u221a(\\1)", s)
    s = re.sub(r"\\underbrace\{([^{}]*)\}(_\{[^{}]*\})?", r"\1", s)
    s = re.sub(r"\\(mathrm|text|mathbf|mathit)\{([^{}]*)\}", r"\2", s)
    s = re.sub(r"\\(label|vspace|hfill|noindent|centering|small|footnotesize)"
               r"\{?[^}\n]*\}?", "", s)
    for pat, rep in _ESCAPES:
        s = re.sub(pat, rep, s)
    s = re.sub(r"\$([^$]*)\$", r"\1", s)          # inline math delimiters
    s = s.replace("$", "")
    s = re.sub(r"\\\\(\[[^]]*\])?", " ", s)
    s = re.sub(r"\^\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"_\{([^{}]*)\}", r"\1", s)
    # Anything still holding a brace group is an unhandled command; keep the
    # argument, drop the command, and let the residual check flag it.
    s = re.sub(r"\\[a-zA-Z]+\{([^{}]*)\}", r"\1", s)
    # No \b here: "_" is a word character, so \sum_c has no boundary after
    # "sum" and the command survived into the output.
    s = re.sub(r"\\[a-zA-Z]+", "", s)
    s = s.replace("{", "").replace("}", "")
    s = re.sub(r"[ \t]+", " ", s)
    return s


def runs(s: str, cites: dict[str, int] | None = None,
         refs: dict[str, str] | None = None) -> list[tuple[str, str]]:
    """Resolve inline markup to ``(text, style)`` pairs.

    Style is one of ``""``, ``"i"``, ``"b"``, ``"tt"``.
    """
    cites = cites or {}
    refs = refs or {}

    def cite_sub(m: re.Match) -> str:
        keys = [k.strip() for k in m.group(1).split(",")]
        return "[" + ", ".join(str(cites.get(k, "?")) for k in keys) + "]"

    s = re.sub(r"\\cite\{([^}]*)\}", cite_sub, s)
    # LaTeX resolves \ref at compile time; this converter has to do it itself.
    # Emitting a literal "X" -- as this did until 2026-09-16 -- turns every
    # cross-reference into "Table X counts it and Fig. X draws it".
    s = re.sub(r"\\ref\{([^}]*)\}",
               lambda m: refs.get(m.group(1).strip(), "?"), s)

    out: list[tuple[str, str]] = []
    style_of = {"emph": "i", "textit": "i", "textbf": "b", "texttt": "tt",
                "underline": "", "text": "", "mathrm": ""}
    pos = 0
    while True:
        m = _CMD.search(s, pos)
        if not m:
            break
        if m.start() > pos:
            out.append((_plain(s[pos:m.start()]), ""))
        close = _matching(s, m.end() - 1)
        inner = s[m.end():close]
        out.append((_plain(inner), style_of[m.group(1)]))
        pos = close + 1
    if pos < len(s):
        out.append((_plain(s[pos:]), ""))
    return [(t, st) for t, st in out if t]


# ----------------------------------------------------------------- blocks

_KNOWN_ENVS = {
    "abstract", "IEEEkeywords", "center", "tabular", "enumerate", "itemize",
    "figure", "table", "quote", "equation", "thebibliography", "document",
}


def _bib_keys(src: str) -> dict[str, int]:
    return {m.group(1): i + 1
            for i, m in enumerate(re.finditer(r"\\bibitem\{([^}]*)\}", src))}


def ref_map(src: str) -> dict[str, str]:
    """Label -> the number LaTeX would print for it.

    Figures are arabic and tables are roman, numbered in source order, which
    is what IEEEtran does and what build_docx's caption numbering already
    assumes. Sections are numbered the same way :func:`parse` numbers them.
    """
    out: dict[str, str] = {}
    fig = tab = sec = sub = 0
    # One linear pass, because a label's number depends on how many numbered
    # things precede it. Subsections matter: IEEE prints them "V-C", and
    # handling only \section left two references rendering as "?".
    token = re.compile(
        r"\\begin\{(?P<env>figure|table)\*?\}(?P<body>.*?)\\end\{(?P=env)\*?\}"
        r"|\\(?P<lvl>sub)?section\{[^}]*\}"
        r"|\\label\{(?P<lab>[^}]*)\}", re.S)
    pending = None          # number the next bare \label should take
    for m in token.finditer(src):
        if m.group("env"):
            if m.group("env") == "figure":
                fig += 1
                num = str(fig)
            else:
                tab += 1
                num = _roman(tab)
            body = m.group("body") or ""
            for lm in re.finditer(r"\\label\{([^}]*)\}", body):
                out[lm.group(1).strip()] = num
            continue
        if m.group(0).startswith("\\section") or m.group(0).startswith(
                "\\subsection"):
            if m.group("lvl"):
                sub += 1
                pending = f"{_roman(sec)}-{chr(64 + sub)}"
            else:
                sec += 1
                sub = 0
                pending = _roman(sec)
            continue
        if m.group("lab") is not None and pending:
            out[m.group("lab").strip()] = pending
            pending = None
    return out


def parse(src: str):
    """Return ``(blocks, cite_numbers, ref_numbers)``."""
    cites = _bib_keys(src)
    refs = ref_map(src)
    body = src[src.index(r"\begin{document}") + len(r"\begin{document}"):]
    body = body[:body.index(r"\end{document}")]
    body = re.sub(r"(?m)^\s*%.*$", "", body)

    blocks: list[tuple[str, object]] = []
    sec_n, sub_n = 0, 0
    i = 0
    lines = body.split("\n")
    buf: list[str] = []

    def flush() -> None:
        nonlocal buf
        text = " ".join(x.strip() for x in buf).strip()
        if text:
            blocks.append(("para", text))
        buf = []

    while i < len(lines):
        ln = lines[i]
        st = ln.strip()

        m = re.match(r"\\title\{(.*)", st)
        if m:
            chunk, i = _gather(lines, i, r"\title{")
            flush()
            blocks.append(("title", _plain(chunk).strip()))
            continue
        if st.startswith(r"\author"):
            chunk, i = _gather(lines, i, r"\author")
            flush()
            names = re.findall(r"\\IEEEauthorblock[NA]\{(.*?)\}", chunk, re.S)
            blocks.append(("author", [_plain(n).strip() for n in names]))
            continue
        if st.startswith(r"\maketitle"):
            flush()
            i += 1
            continue

        m = re.match(r"\\section\{(.*)\}", st)
        if m:
            flush()
            sec_n += 1
            sub_n = 0
            blocks.append(("section", (_roman(sec_n), _plain(m.group(1)))))
            i += 1
            continue
        m = re.match(r"\\subsection\{(.*)\}", st)
        if m:
            flush()
            sub_n += 1
            blocks.append(
                ("subsection", (chr(64 + sub_n), _plain(m.group(1)))))
            i += 1
            continue

        m = re.match(r"\\begin\{([A-Za-z*]+)\}", st)
        if m:
            env = m.group(1)
            if env not in _KNOWN_ENVS:
                raise ValueError(f"unhandled environment: {env}")
            flush()
            chunk, i = _env(lines, i, env)
            blocks.extend(_render_env(env, chunk))
            continue

        # A blank line is a paragraph break in LaTeX. Without this the whole
        # of a section collapses into one paragraph, which looked like it had
        # worked until the block count was compared against the word count.
        if not st:
            flush()
        else:
            buf.append(ln)
        i += 1

    flush()
    return blocks, cites, refs


def _gather(lines: list[str], i: int, opener: str) -> tuple[str, int]:
    """Collect a brace group that may span lines."""
    acc, depth, started = [], 0, False
    while i < len(lines):
        for ch in lines[i]:
            if ch == "{":
                depth += 1
                started = True
            elif ch == "}":
                depth -= 1
        acc.append(lines[i])
        i += 1
        if started and depth == 0:
            break
    text = "\n".join(acc)
    return text[text.index("{") + 1:text.rindex("}")], i


def _env(lines: list[str], i: int, env: str) -> tuple[str, int]:
    end = rf"\end{{{env}}}"
    acc = []
    i += 1
    while i < len(lines) and end not in lines[i]:
        acc.append(lines[i])
        i += 1
    return "\n".join(acc), i + 1


def _render_env(env: str, chunk: str) -> list[tuple[str, object]]:
    if env == "abstract":
        return [("abstract", " ".join(chunk.split()))]
    if env == "IEEEkeywords":
        return [("keywords", " ".join(chunk.split()))]
    if env in ("enumerate", "itemize"):
        items = [x.strip() for x in re.split(r"\\item", chunk) if x.strip()]
        return [(env, [" ".join(x.split()) for x in items])]
    if env == "quote":
        return [("quote", " ".join(chunk.split()))]
    if env == "equation":
        return [("equation", " ".join(chunk.split()))]
    if env == "thebibliography":
        items = re.split(r"\\bibitem\{[^}]*\}", chunk)[1:]
        return [("bib", [" ".join(x.split()) for x in items])]
    if env == "tabular":
        return [("tabular", _tabular(chunk))]
    if env in ("figure", "table", "center"):
        out: list[tuple[str, object]] = []
        fig = re.search(r"\\includegraphics(?:\[[^]]*\])?\{([^}]*)\}", chunk)
        if fig:
            out.append(("image", fig.group(1)))
        for m in re.finditer(r"\\begin\{tabular\}(.*?)\\end\{tabular\}",
                             chunk, re.S):
            out.append(("tabular", _tabular(m.group(1))))
        cap = re.search(r"\\caption\{(.*?)\}\s*(\\label|$)", chunk, re.S)
        if cap:
            out.append(("caption", " ".join(cap.group(1).split())))
        if not out:
            txt = re.sub(r"\\(fbox|parbox)\s*", " ", chunk)
            txt = re.sub(r"\{0\.\d+\\columnwidth\}", " ", txt)
            txt = re.sub(r"\\(small|centering)\b", " ", txt)
            txt = " ".join(txt.split())
            if txt:
                out.append(("boxed", txt))
        return out
    return []


def _tabular(chunk: str) -> list[list[str]]:
    chunk = re.sub(r"^\s*\{[^}]*\}", "", chunk.strip(), count=1)
    chunk = re.sub(r"\\(hline|toprule|midrule|bottomrule)", "", chunk)
    rows = []
    for raw in chunk.split(r"\\"):
        raw = raw.strip()
        if not raw:
            continue
        mc = r"\\multicolumn\{\d+\}\{[^}]*\}\{(.*)\}"
        cells = [re.sub(mc, r"\1", c).strip() for c in raw.split("&")]
        rows.append(cells)
    return rows


def _roman(n: int) -> str:
    vals = [(10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    out = ""
    for v, s in vals:
        while n >= v:
            out += s
            n -= v
    return out
