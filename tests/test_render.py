import pytest

from nyt_recipe.recipe import IngredientGroup, Recipe
from nyt_recipe.render.html import to_html
from nyt_recipe.render.markdown import to_markdown


def plain_recipe():
    return Recipe(
        title="Chicken Teriyaki",
        ingredient_groups=[IngredientGroup(items=["1 cup soy sauce", "1 ½ teaspoons brown sugar"])],
        instructions=["Combine everything.", "Simmer until thick."],
        author="John T. Edge",
        total_time="30 minutes",
        servings="8 servings",
        description="A weeknight teriyaki.",
        tags=["Chicken Thigh", "Easy"],
        source_url="https://cooking.nytimes.com/recipes/1012984-chicken-teriyaki",
    )


def grouped_recipe():
    return Recipe(
        title="Apple Cider Honey Cake",
        ingredient_groups=[
            IngredientGroup(heading="FOR THE APPLE CIDER BUTTER", items=["2 pounds apples"]),
            IngredientGroup(heading="FOR THE CAKE", items=["2 ½ cups flour", "1 teaspoon salt"]),
        ],
        instructions=["Cook the apples."],
    )


def test_html_includes_the_recipe_content():
    out = to_html(plain_recipe())
    assert "Chicken Teriyaki" in out
    assert "1 cup soy sauce" in out
    assert "Simmer until thick." in out


def test_html_shows_the_metadata_the_old_output_dropped():
    out = to_html(plain_recipe())
    for expected in ("John T. Edge", "30 minutes", "8 servings", "A weeknight teriyaki."):
        assert expected in out, f"missing {expected!r}"


def test_html_renders_group_headings():
    out = to_html(grouped_recipe())
    assert "FOR THE APPLE CIDER BUTTER" in out
    assert "FOR THE CAKE" in out


def test_html_keeps_fraction_glyphs_rather_than_entity_escaping_them():
    """The old code rewrote ¼ ½ ¾ as HTML entities to work around a renderer
    that could not draw them, and left the other fifteen broken."""
    out = to_html(plain_recipe())
    assert "½" in out
    assert "&frac12;" not in out


def test_html_escapes_markup_in_recipe_text():
    """Recipe text is untrusted input; the old template interpolated it raw."""
    nasty = plain_recipe()
    nasty.title = "Salt & Pepper <script>alert(1)</script>"
    out = to_html(nasty)
    assert "<script>alert(1)</script>" not in out
    assert "&amp;" in out


def test_html_applies_the_requested_theme():
    light = to_html(plain_recipe(), theme="light")
    dark = to_html(plain_recipe(), theme="dark")
    assert light != dark


def test_html_omits_absent_optional_fields_without_erroring():
    bare = Recipe(title="Toast", ingredient_groups=[IngredientGroup(items=["bread"])])
    out = to_html(bare)
    assert "Toast" in out
    assert "None" not in out


def test_markdown_numbers_instructions_and_lists_ingredients():
    out = to_markdown(plain_recipe())
    assert "# Chicken Teriyaki" in out
    assert "- 1 cup soy sauce" in out
    assert "1. Combine everything." in out


def test_markdown_renders_groups_as_subheadings():
    out = to_markdown(grouped_recipe())
    assert "### FOR THE APPLE CIDER BUTTER" in out
    assert "### FOR THE CAKE" in out


def test_markdown_keeps_fraction_glyphs():
    assert "½" in to_markdown(plain_recipe())


@pytest.mark.slow
def test_pdf_is_a_real_pdf_and_keeps_every_fraction():
    """
    The complaint that started this: fractions vanishing in the PDF. Renders
    for real and reads the glyphs back out, because a PDF that merely exists
    proves nothing.
    """
    pytest.importorskip("pypdf")
    from pypdf import PdfReader

    from nyt_recipe.render.pdf import to_pdf

    recipe = plain_recipe()
    recipe.ingredient_groups = [
        IngredientGroup(items=["¼ ½ ¾ ⅐ ⅑ ⅒ ⅓ ⅔ ⅕ ⅖ ⅗ ⅘ ⅙ ⅚ ⅛ ⅜ ⅝ ⅞"])
    ]
    import tempfile, os

    path = os.path.join(tempfile.mkdtemp(), "recipe.pdf")
    to_pdf(to_html(recipe), path)

    assert os.path.exists(path)
    with open(path, "rb") as f:
        assert f.read(5) == b"%PDF-"

    text = PdfReader(path).pages[0].extract_text()
    missing = [c for c in "¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞" if c not in text]
    assert not missing, f"dropped from the PDF: {missing}"
