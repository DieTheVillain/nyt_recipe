from nyt_recipe.measures import (
    VULGAR_TO_ASCII,
    normalize,
    to_ascii_fractions,
    to_unicode_fractions,
)

# Built from its code point on purpose: a literal non-breaking space is
# invisible in source and indistinguishable from a plain one, which would
# make every assertion below unreadable and impossible to trust.
NBSP = chr(0xA0)


def test_converts_every_vulgar_fraction_to_ascii():
    """
    The old code mapped only 1/4, 1/2 and 3/4, so the rest reached the PDF
    renderer as glyphs it had no font for and were dropped.
    """
    cases = {
        "¼": "1/4", "½": "1/2", "¾": "3/4",
        "⅐": "1/7", "⅑": "1/9", "⅒": "1/10",
        "⅓": "1/3", "⅔": "2/3",
        "⅕": "1/5", "⅖": "2/5", "⅗": "3/5", "⅘": "4/5",
        "⅙": "1/6", "⅚": "5/6",
        "⅛": "1/8", "⅜": "3/8", "⅝": "5/8", "⅞": "7/8",
    }
    for glyph, ascii_form in cases.items():
        assert to_ascii_fractions(glyph) == ascii_form, f"failed for {glyph!r}"


def test_converts_ascii_fractions_back_to_glyphs():
    assert to_unicode_fractions("1/2 cup sugar") == "½ cup sugar"
    assert to_unicode_fractions("3/8 teaspoon salt") == "⅜ teaspoon salt"


def test_ascii_conversion_round_trips_for_every_fraction():
    for glyph in VULGAR_TO_ASCII:
        assert to_unicode_fractions(to_ascii_fractions(glyph)) == glyph


def test_does_not_convert_a_fraction_embedded_in_a_larger_number():
    """A bare regex would find 1/4 inside 21/40 and mangle it."""
    assert to_unicode_fractions("21/40") == "21/40"


def test_normalize_collapses_whitespace_and_strips():
    assert normalize("  1 cup   soy   sauce \n") == "1 cup soy sauce"


def test_normalize_binds_mixed_numbers_so_they_never_wrap():
    """'1 1/2' must not break across a line, or the reader sees '1' at the end
    of one line and the fraction at the start of the next."""
    assert normalize("1 ½ teaspoons brown sugar") == f"1{NBSP}½ teaspoons brown sugar"


def test_normalize_keeps_an_existing_nbsp_in_a_mixed_number():
    """NYT already uses a non-breaking space here. It must survive rather than
    be widened to a plain space, and must not be doubled."""
    assert normalize(f"4{NBSP}½ cups flour") == f"4{NBSP}½ cups flour"


def test_normalize_leaves_a_lone_fraction_alone():
    assert normalize("½ teaspoon black pepper") == "½ teaspoon black pepper"


def test_normalize_converts_nbsp_between_words_to_a_plain_space():
    """Only mixed numbers keep one. Otherwise a long ingredient line refuses to
    wrap anywhere and overflows its column."""
    assert normalize(f"soy{NBSP}sauce and sugar") == "soy sauce and sugar"


def test_normalize_preserves_ranges_and_dual_units():
    """A real NYT line. The range, the slash pair and the order must survive;
    only the mixed number inside it gains a binding space."""
    line = "½ to 1 ½ cups/118 to 355 milliliters apple cider"
    expected = f"½ to 1{NBSP}½ cups/118 to 355 milliliters apple cider"
    assert normalize(line) == expected


def test_normalize_handles_empty_and_none():
    assert normalize("") == ""
    assert normalize(None) is None
