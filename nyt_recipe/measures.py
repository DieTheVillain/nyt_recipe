"""
Fractions and measurements as NYT Cooking writes them.

Ingredient lines are not simple. Real examples:

    ½ to 1 ½ cups/118 to 355 milliliters apple cider
    ¾ cup/170 grams melted unsalted butter or ¾ cup/177 milliliters olive oil
    4 ½ cups plus 1 tablespoon/420 grams almond flour (see tip)

A range, a mixed number and a US/metric pair can all appear in one line. The
job here is to render those correctly and never to damage them; structured
parsing is best-effort and always falls back to the original text.
"""

import re

# The full Unicode vulgar fraction set. The previous implementation knew only
# the first three, so the rest reached the renderer unmapped.
VULGAR_TO_ASCII = {
    "¼": "1/4",
    "½": "1/2",
    "¾": "3/4",
    "⅐": "1/7",
    "⅑": "1/9",
    "⅒": "1/10",
    "⅓": "1/3",
    "⅔": "2/3",
    "⅕": "1/5",
    "⅖": "2/5",
    "⅗": "3/5",
    "⅘": "4/5",
    "⅙": "1/6",
    "⅚": "5/6",
    "⅛": "1/8",
    "⅜": "3/8",
    "⅝": "5/8",
    "⅞": "7/8",
}


ASCII_TO_VULGAR = {v: k for k, v in VULGAR_TO_ASCII.items()}

# Longest first so "1/10" is tried before "1/1x" patterns, and bounded by
# digit lookaround so "1/4" is not found inside "21/40".
_ASCII_FRACTION_RE = re.compile(
    r"(?<!\d)(" + "|".join(re.escape(a) for a in sorted(ASCII_TO_VULGAR, key=len, reverse=True)) + r")(?!\d)"
)


def to_ascii_fractions(text):
    """Replace every Unicode vulgar fraction with its ASCII form."""
    if not text:
        return text
    return "".join(VULGAR_TO_ASCII.get(ch, ch) for ch in text)


def to_unicode_fractions(text):
    """Replace ASCII fractions with their Unicode glyphs, where one exists."""
    if not text:
        return text
    return _ASCII_FRACTION_RE.sub(lambda m: ASCII_TO_VULGAR[m.group(1)], text)


NBSP = chr(0xA0)  # non-breaking space

_VULGAR_CLASS = "".join(VULGAR_TO_ASCII)

# A whole number followed by a fraction is one quantity — "1 ½" — and must not
# be split across a line, or the reader gets "1" at the end of one line and
# "½ teaspoons" at the start of the next. Matches either spacing, since NYT is
# inconsistent about which it uses.
_MIXED_NUMBER_RE = re.compile(r"(\d)[ " + NBSP + r"]+([" + _VULGAR_CLASS + r"])")


def normalize(text):
    """
    Tidy an ingredient or instruction line without changing what it says.

    Collapses runs of whitespace, converts stray non-breaking spaces back to
    ordinary ones so long lines can wrap, then re-binds mixed numbers with a
    non-breaking space. Ranges ("½ to 1 ½"), US/metric pairs ("cups/118
    milliliters") and everything else are passed through untouched.
    """
    if not text:
        return text
    # Every kind of space becomes a plain one first, so the binding step below
    # is the single place that decides what stays non-breaking.
    collapsed = " ".join(text.replace(NBSP, " ").split())
    return _MIXED_NUMBER_RE.sub(lambda m: f"{m.group(1)}{NBSP}{m.group(2)}", collapsed)
