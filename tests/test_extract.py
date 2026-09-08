import pytest

from conftest import fixture
from nyt_recipe.extract import ExtractionError, from_html


def test_finds_every_ingredient():
    """
    The regression this whole redesign exists for. NYT moved ingredients from
    <li class="ingredient_ingredient__..."> to <p class="pantry--ui
    ingredient_ingredient__...">, the selector still asked for <li>, and every
    recipe came back with an empty ingredient list and no error.
    """
    recipe = from_html(fixture("chicken-teriyaki.html"))
    assert len(recipe.ingredients) == 10
    assert "1 cup soy sauce" in recipe.ingredients


def test_keeps_fractions_in_ingredient_text():
    recipe = from_html(fixture("chicken-teriyaki.html"))
    brown_sugar = [i for i in recipe.ingredients if "brown sugar" in i]
    assert brown_sugar, "expected a brown sugar line"
    assert "½" in brown_sugar[0]


def test_reads_the_scalar_fields_the_old_code_discarded():
    recipe = from_html(fixture("chicken-teriyaki.html"))
    assert recipe.title == "Chicken Teriyaki"
    assert recipe.author == "John T. Edge"
    assert recipe.servings == "8 servings"
    assert recipe.total_time == "30 minutes"
    assert recipe.description
    assert recipe.source_url.startswith("https://cooking.nytimes.com/")


def test_finds_the_header_image():
    """The old selector was pinned to a class hash that no longer exists."""
    recipe = from_html(fixture("chicken-teriyaki.html"))
    assert recipe.image_url
    assert recipe.image_url.startswith("http")


def test_finds_tags():
    """tags_tag__ matched nothing, so the tags line was always empty."""
    recipe = from_html(fixture("chicken-teriyaki.html"))
    assert "Chicken Thigh" in recipe.tags


def test_reads_instructions_in_order():
    recipe = from_html(fixture("chicken-teriyaki.html"))
    assert len(recipe.instructions) == 4
    assert recipe.instructions[0].startswith("In a small saucepan")


def test_groups_ingredients_under_their_headings():
    """
    JSON-LD flattens ingredient groups. This recipe has two — FOR THE APPLE
    CIDER BUTTER and FOR THE CAKE — that only exist in the DOM, and losing
    them is a large part of what reads as bad formatting.
    """
    recipe = from_html(fixture("apple-cider-honey-cake.html"))
    headings = [g.heading for g in recipe.ingredient_groups]
    # Kept as NYT writes them; casing is a styling decision for the renderer.
    assert headings == ["FOR THE APPLE CIDER BUTTER", "FOR THE CAKE"]
    assert sum(len(g.items) for g in recipe.ingredient_groups) == 14


def test_an_ungrouped_recipe_is_one_unnamed_group():
    recipe = from_html(fixture("chicken-teriyaki.html"))
    assert len(recipe.ingredient_groups) == 1
    assert recipe.ingredient_groups[0].heading is None


def test_no_ingredient_is_lost_to_grouping():
    """Grouping is an enhancement. If heading matching goes wrong the flat
    list must survive intact, because losing an ingredient is a real bug and
    losing a heading is a cosmetic one."""
    for name in ("chicken-teriyaki.html", "apple-cider-honey-cake.html", "almond-cake.html"):
        recipe = from_html(fixture(name))
        grouped = [item for g in recipe.ingredient_groups for item in g.items]
        assert grouped == recipe.ingredients


def test_falls_back_to_the_dom_when_json_ld_is_missing():
    """JSON-LD is the primary source, but it must not be the only one."""
    raw = fixture("chicken-teriyaki.html")
    stripped = _strip_json_ld(raw)
    recipe = from_html(stripped)
    assert len(recipe.ingredients) == 10
    assert recipe.title == "Chicken Teriyaki"
    assert len(recipe.instructions) == 4


def test_raises_rather_than_returning_an_empty_recipe():
    """The old code logged a warning and handed back a recipe with no
    ingredients, which then rendered as a perfectly normal-looking PDF."""
    with pytest.raises(ExtractionError):
        from_html("<html><head><title>Not a recipe</title></head><body></body></html>")


def _strip_json_ld(raw):
    import re

    return re.sub(
        r'<script type="application/ld\+json".*?</script>', "", raw, flags=re.S
    )
