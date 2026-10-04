"""
Presentation MathML -> LaTeX, for the subset OpenStax actually uses.

The output has to render in KaTeX, because that is what the marking
system's editor uses. So every command emitted here is one KaTeX knows,
and scripts/check_latex.mjs renders every converted expression to prove
it rather than trusting this file.

Non-ASCII characters that are invisible or easily confused (non-breaking
space, zero-width space, the combining slash) are written as escapes
below, never pasted in literally.
"""

import xml.etree.ElementTree as ET

M = "{http://www.w3.org/1998/Math/MathML}"

SYMBOLS = {
    "−": "-", "–": "-", "—": "-",          # minus, en/em dash
    "·": r"\cdot", "⋅": r"\cdot", "∙": r"\cdot", "•": r"\cdot",
    "×": r"\times", "÷": r"\div", "±": r"\pm",
    "≠": r"\neq", "≤": r"\leq", "≥": r"\geq", "≈": r"\approx",
    "≟": r"\stackrel{?}{=}",
    "✓": r"\checkmark",
    "∑": r"\sum", "∘": r"\circ", "…": r"\ldots",
    "∪": r"\cup", "∠": r"\angle", "⊥": r"\perp", "∥": r"\parallel",
    "π": r"\pi", "Δ": r"\Delta", "∞": r"\infty",
    "°": r"^{\circ}", "º": r"^{\circ}",
    "′": "'", "″": "''", "│": "|",
    "¾": r"\tfrac{3}{4}", "⦜": r"\angle",
    "↘": r"\searrow", "↙": r"\swarrow", "△": r"\triangle",
    "“": r"\text{``}", "”": r"\text{''}", "‘": r"\text{`}", "’": "'",
    "{": r"\{", "}": r"\}",
    "%": r"\%", "$": r"\$", "&": r"\&", "#": r"\#",
    "\u00a0": " ",                                          # non-breaking space
}

# A run of underscores is a fill-in blank, not a subscript.
BLANK = r"\underline{\hspace{2em}}"

# U+0338 overlays a slash on the character before it: a crossed-out
# digit, which the books use to show cancelling.
COMBINING_SLASH = "\u0338"

DROP = {"\u200b"}                                           # zero-width space

# Symbols that need maths mode even when they turn up inside <mtext>.
MATH_IN_TEXT = {k for k, v in SYMBOLS.items()
                if (v.startswith("\\") or "^" in v) and k not in "{}%$&#"}

# Plain replacements inside text runs, where KaTeX has no metrics for the
# original glyph: dashes, primes (feet and inches) and curly quotes.
TEXT_PLAIN = {
    "\u2212": "-", "\u2013": "-", "\u2014": "-",
    "′": "'", "″": "''", "“": '"', "”": '"', "‘": "'", "’": "'",
}

FUNCTIONS = {"sin", "cos", "tan", "log", "ln", "exp", "min", "max", "lim"}

# Characters that are special in LaTeX and can turn up inside <mtext>.
TEXT_ESCAPES = {
    "\\": r"\textbackslash{}", "{": r"\{", "}": r"\}",
    "%": r"\%", "$": r"\$", "&": r"\&", "#": r"\#", "_": r"\_",
    "^": r"\^{}", "~": r"\~{}",
}


def _tag(el: ET.Element) -> str:
    return el.tag.replace(M, "")


def _text(el: ET.Element) -> str:
    return (el.text or "").strip()


def _symbols(s: str) -> str:
    out: list[str] = []
    for ch in s:
        if ch in DROP:
            continue
        if ch == COMBINING_SLASH and out:
            out[-1] = r"\cancel{" + out[-1].strip() + "}"
            continue
        rep = SYMBOLS.get(ch, ch)
        # Spaced, so a following letter can't merge into the command name:
        # "\pi" then "r" must not become the unknown "\pir".
        if rep.startswith("\\") and rep[-1].isalpha():
            rep += " "
        out.append(rep)
    return "".join(out)


def _token(s: str) -> str:
    if s and set(s) <= {"_"}:
        return BLANK
    return _symbols(s)


def _mtext(el: ET.Element) -> str:
    raw = (el.text or "").replace("\u00a0", " ")
    if not raw.strip():
        return r"\ "
    # Split out symbols KaTeX only accepts in maths mode, such as a "≠"
    # in the middle of a sentence.
    parts: list[str] = []
    run: list[str] = []

    def flush() -> None:
        if run:
            parts.append(r"\text{" + "".join(TEXT_ESCAPES.get(c, c) for c in run) + "}")
            run.clear()

    for ch in raw:
        if ch in DROP:
            continue
        if ch in MATH_IN_TEXT:
            flush()
            parts.append(_symbols(ch))
        else:
            run.append(TEXT_PLAIN.get(ch, ch))
    flush()
    return "".join(parts)


def _group(s: str) -> str:
    """Brace a base or script unless it is already a single character."""
    return s if len(s) == 1 else "{" + s + "}"


def convert(el: ET.Element) -> str:
    t = _tag(el)
    kids = list(el)

    if t in ("math", "mrow", "mstyle", "mpadded", "semantics"):
        return "".join(convert(k) for k in kids)

    if t == "mi":
        s = _text(el)
        if s in FUNCTIONS:
            return "\\" + s + " "
        # ASCII only: "πr" is two symbols, not a word to set upright.
        if len(s) > 1 and s.isalpha() and s.isascii():
            return r"\mathrm{" + s + "}"
        return _token(s)

    if t == "mn":
        return _token(_text(el).replace(" ", ""))

    if t == "mo":
        return _token(_text(el))

    if t == "mtext":
        return _mtext(el)

    if t == "mspace":
        return r"\;"

    if t == "msup":
        return _group(convert(kids[0])) + "^{" + convert(kids[1]) + "}"

    if t == "msub":
        return _group(convert(kids[0])) + "_{" + convert(kids[1]) + "}"

    if t == "msubsup":
        return (_group(convert(kids[0])) + "_{" + convert(kids[1]) + "}"
                + "^{" + convert(kids[2]) + "}")

    if t == "mfrac":
        return r"\frac{" + convert(kids[0]) + "}{" + convert(kids[1]) + "}"

    if t == "msqrt":
        return r"\sqrt{" + "".join(convert(k) for k in kids) + "}"

    if t == "mroot":
        return r"\sqrt[" + convert(kids[1]) + "]{" + convert(kids[0]) + "}"

    if t == "mover":
        base, over = convert(kids[0]), convert(kids[1])
        if over.strip() in ("¯", "-", "‾", "_"):
            return r"\overline{" + base + "}"
        return r"\overset{" + over + "}{" + base + "}"

    if t == "munder":
        base, under = convert(kids[0]), convert(kids[1])
        if under.strip() == "⎵":
            return r"\underbrace{" + base + "}"
        return r"\underset{" + under + "}{" + base + "}"

    if t == "munderover":
        base = convert(kids[0])
        if base.strip() == r"\sum":
            return r"\sum_{" + convert(kids[1]) + "}^{" + convert(kids[2]) + "}"
        return (r"\underset{" + convert(kids[1]) + "}{\\overset{"
                + convert(kids[2]) + "}{" + base + "}}")

    if t == "menclose":
        inner = "".join(convert(k) for k in kids)
        notation = el.get("notation", "")
        if "strike" in notation:
            return r"\cancel{" + inner + "}"
        if "box" in notation:
            return r"\boxed{" + inner + "}"
        return inner

    if t == "mphantom":
        return r"\phantom{" + "".join(convert(k) for k in kids) + "}"

    if t == "mfenced":
        open_, close = el.get("open", "("), el.get("close", ")")
        sep = el.get("separators", ",")[:1] or ","
        inner = sep.join(convert(k) for k in kids)
        return r"\left" + _fence(open_) + inner + r"\right" + _fence(close)

    if t == "mtable":
        rows = [k for k in kids if _tag(k) == "mtr"]
        cols = max((len(list(r)) for r in rows), default=1)
        body = r" \\ ".join(" & ".join(convert(cell) for cell in r) for r in rows)
        return r"\begin{array}{" + "l" * cols + "}" + body + r"\end{array}"

    if t in ("mtr", "mtd"):
        return "".join(convert(k) for k in kids)

    # Anything unexpected: keep its content rather than drop it.
    return _symbols(_text(el)) + "".join(convert(k) for k in kids)


def _fence(ch: str) -> str:
    if ch == "":
        return "."
    return {"{": r"\{", "}": r"\}", "|": "|", "‖": r"\|"}.get(ch, ch)


def mathml_to_latex(el: ET.Element) -> str:
    return " ".join(convert(el).split())
