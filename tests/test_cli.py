import os
import pytest

from nyt_recipe.main import safe_filename
from nyt_recipe.recipe import IngredientGroup, Recipe


def test_safe_filename_strips_characters_windows_rejects():
    assert "/" not in safe_filename("Pasta w/ Sauce")
    assert ":" not in safe_filename("Dinner: Fast")
    for ch in '<>:"/\\|?*':
        assert ch not in safe_filename(f"a{ch}b")


def test_safe_filename_collapses_whitespace():
    assert safe_filename("  Chicken   Teriyaki  ") == "Chicken Teriyaki"


def test_safe_filename_never_returns_an_empty_name():
    """A title of only illegal characters would otherwise produce a file with
    no name, or a dotfile."""
    assert safe_filename("///") == "---"
    assert safe_filename("") == "recipe"
    assert safe_filename("   ") == "recipe"


def test_safe_filename_does_not_end_in_a_dot():
    """Windows silently strips a trailing dot, so the name on disk stops
    matching the name we think we wrote."""
    assert not safe_filename("Mise en place.").endswith(".")


def _recipe(instructions=None):
    return Recipe(
        title="Chicken Teriyaki",
        ingredient_groups=[IngredientGroup(items=["1 cup soy sauce"])],
        instructions=instructions if instructions is not None else ["Cook it."],
        author="John T. Edge",
        total_time="30 minutes",
        source_url="https://cooking.nytimes.com/recipes/1012984-chicken-teriyaki",
    )


def test_preview_includes_the_whole_recipe_when_it_fits():
    pytest.importorskip("discord")
    from nyt_recipe.bot import format_preview

    text = format_preview(_recipe())
    assert "Chicken Teriyaki" in text
    assert "1 cup soy sauce" in text
    assert "1. Cook it." in text


def test_preview_is_trimmed_to_discord_message_limit():
    """Discord rejects anything over 2000 characters outright, so a long
    recipe must come back shortened rather than not at all."""
    pytest.importorskip("discord")
    from nyt_recipe.bot import MESSAGE_LIMIT, format_preview

    text = format_preview(_recipe(instructions=[f"Step {i}. " + "x" * 200 for i in range(40)]))
    assert len(text) <= MESSAGE_LIMIT
    assert "truncated" in text


def test_trimming_cuts_whole_lines_not_mid_word():
    pytest.importorskip("discord")
    from nyt_recipe.bot import trim

    out = trim(["alpha", "bravo", "charlie"], limit=40)
    for line in out.splitlines():
        assert line in ("alpha", "bravo", "charlie", "… (truncated)")


def test_saved_files_are_prefixed_with_their_source(tmp_path):
    """So a recipe is identifiable as NYT's once it is sitting in a folder
    alongside files from anywhere else."""
    from nyt_recipe.main import save

    for fmt, suffix in (("markdown", ".md"), ("html", ".html")):
        path = save(_recipe(), str(tmp_path), fmt)
        assert os.path.basename(path) == f"NYT Cooking - Chicken Teriyaki{suffix}"


def test_the_prefix_survives_a_title_full_of_illegal_characters(tmp_path):
    from nyt_recipe.main import save

    recipe = _recipe()
    recipe.title = 'Pasta w/ "Sauce": Fast'
    path = save(recipe, str(tmp_path), "markdown")
    name = os.path.basename(path)
    assert name.startswith("NYT Cooking - ")
    for ch in r'<>:"/\|?*':
        assert ch not in name


def test_a_recipe_with_no_usable_title_still_gets_a_sensible_name(tmp_path):
    from nyt_recipe.main import save

    recipe = _recipe()
    recipe.title = "///"
    path = save(recipe, str(tmp_path), "markdown")
    assert os.path.basename(path).startswith("NYT Cooking - ")
