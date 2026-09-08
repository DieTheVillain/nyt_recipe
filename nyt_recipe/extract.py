"""
Turn an NYT Cooking page into a Recipe.

The previous implementation matched hashed CSS class names. NYT changed that
markup and three extractors began returning nothing without raising: recipes
came back with a title, their instructions and an empty ingredient list, which
rendered as a perfectly normal-looking PDF.

Every recipe page carries a schema.org Recipe in a JSON-LD block, published for
search engines and therefore far more stable than a class hash. That is the
primary source here. It is not the only one, for two reasons: it can go away,
and it flattens ingredient groups, so a recipe with "FOR THE CAKE" and "FOR THE
FROSTING" arrives as one undivided list. Headings come from the DOM and are
laid back over the flat list.

Losing a heading is cosmetic. Losing an ingredient is not, so whenever the two
sources disagree the flat list wins.
"""

import json
import re

import bs4

from .measures import normalize
from .recipe import IngredientGroup, Recipe

INGREDIENT_CLASS_RE = re.compile(r"ingredient_ingredient__")
GROUP_NAME_CLASS_RE = re.compile(r"ingredientgroup_name__")
INSTRUCTION_CLASS_RE = re.compile(r"preparation_step__")
PANTRY_BODY_RE = re.compile(r"pantry--body-long")

_ISO_DURATION_RE = re.compile(
    r"^P(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?)?$"
)


class ExtractionError(Exception):
    """Raised when a page cannot be read as a recipe."""


def from_html(raw):
    """
    Parse a recipe page. Raises ExtractionError if it yields no ingredients.

    A recipe with no ingredients is not a recipe, and returning one silently is
    the failure this module exists to prevent.
    """
    soup = bs4.BeautifulSoup(raw, "html.parser")
    data = _json_ld_recipe(soup)

    recipe = _from_json_ld(data) if data else _from_dom(soup)
    if not recipe.ingredients:
        # JSON-LD present but useless: try the DOM before giving up.
        recipe = _from_dom(soup)

    if not recipe.ingredients:
        raise ExtractionError(
            "No ingredients found. The page may not be a recipe, or NYT's "
            "markup may have changed again — run the fixture refresh and "
            "check tests/test_extract.py."
        )

    _apply_dom_groups(recipe, soup)
    return recipe


# ─── JSON-LD ──────────────────────────────────────────────────────────────────

def _json_ld_recipe(soup):
    """The first ld+json block that describes a Recipe, if any."""
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        text = tag.string or tag.get_text()
        if not text:
            continue
        try:
            payload = json.loads(text)
        except (ValueError, TypeError):
            continue
        for node in _candidate_nodes(payload):
            if _is_recipe(node):
                return node
    return None


def _candidate_nodes(payload):
    """Recipe nodes hide inside lists and @graph wrappers as well as at top level."""
    if isinstance(payload, list):
        for item in payload:
            yield from _candidate_nodes(item)
    elif isinstance(payload, dict):
        yield payload
        for item in payload.get("@graph", []) or []:
            yield from _candidate_nodes(item)


def _is_recipe(node):
    node_type = node.get("@type")
    if isinstance(node_type, list):
        return "Recipe" in node_type
    return node_type == "Recipe"


def _from_json_ld(data):
    ingredients = [normalize(i) for i in data.get("recipeIngredient") or [] if i and i.strip()]
    return Recipe(
        title=normalize(data.get("name")) or "",
        ingredient_groups=[IngredientGroup(items=ingredients)] if ingredients else [],
        instructions=_instructions_from_json_ld(data),
        description=normalize(_plain(data.get("description"))),
        author=_author(data.get("author")),
        source_url=_absolute(data.get("url")),
        image_url=_image(data.get("image")),
        total_time=_duration(data.get("totalTime")),
        servings=normalize(_plain(data.get("recipeYield"))),
        nutrition=_nutrition(data.get("nutrition")),
        rating=_rating(data.get("aggregateRating"), "ratingValue", float),
        rating_count=_rating(data.get("aggregateRating"), "ratingCount", int),
        tags=_tags(data),
    )


def _instructions_from_json_ld(data):
    steps = []
    for step in data.get("recipeInstructions") or []:
        if isinstance(step, dict):
            text = step.get("text") or step.get("name")
        else:
            text = step
        text = normalize(_plain(text))
        if text:
            steps.append(text)
    return steps


def _plain(value):
    """JSON-LD fields arrive as a string, a list of them, or a node."""
    if value is None:
        return None
    if isinstance(value, list):
        return ", ".join(filter(None, (_plain(v) for v in value)))
    if isinstance(value, dict):
        return value.get("name") or value.get("text") or value.get("@value")
    return str(value)


def _author(value):
    name = _plain(value)
    return normalize(name) if name else None


def _absolute(url):
    """NYT publishes a protocol-relative url; a bare // is not clickable."""
    if not url:
        return None
    url = url.strip()
    if url.startswith("//"):
        return f"https:{url}"
    return url


def _image(value):
    """image is a string, a list, or a list of ImageObject nodes."""
    if not value:
        return None
    if isinstance(value, str):
        return _absolute(value)
    if isinstance(value, dict):
        return _absolute(value.get("contentUrl") or value.get("url"))
    if isinstance(value, list):
        for item in value:
            found = _image(item)
            if found:
                return found
    return None


def _duration(iso):
    """PT30M reads as "30 minutes"; nobody wants ISO-8601 on a recipe card."""
    if not iso:
        return None
    match = _ISO_DURATION_RE.match(str(iso).strip())
    if not match:
        return None
    days = int(match.group("days") or 0)
    hours = int(match.group("hours") or 0) + days * 24
    minutes = int(match.group("minutes") or 0)
    parts = []
    if hours:
        parts.append(f"{hours} hour" + ("s" if hours != 1 else ""))
    if minutes:
        parts.append(f"{minutes} minute" + ("s" if minutes != 1 else ""))
    return " ".join(parts) or None


def _nutrition(value):
    if not isinstance(value, dict):
        return {}
    return {
        k: v for k, v in value.items()
        if not k.startswith("@") and isinstance(v, (str, int, float)) and str(v).strip()
    }


def _rating(value, key, cast):
    if not isinstance(value, dict) or value.get(key) in (None, ""):
        return None
    try:
        return cast(float(value[key]))
    except (TypeError, ValueError):
        return None


def _tags(data):
    """Keywords, category and cuisine are all comma-joined strings."""
    seen = []
    for key in ("keywords", "recipeCategory", "recipeCuisine"):
        raw = _plain(data.get(key)) or ""
        for part in raw.split(","):
            tag = part.strip()
            if tag and tag not in seen:
                seen.append(tag)
    return seen


# ─── DOM fallback ─────────────────────────────────────────────────────────────

def _from_dom(soup):
    """
    Used when JSON-LD is absent or yields nothing.

    Matches on the stable part of NYT's class names and does not care which
    element carries them — the last breakage was a move from <li> to <p>.
    """
    ingredients = []
    for tag in soup.find_all(attrs={"class": INGREDIENT_CLASS_RE}):
        text = normalize(tag.get_text(" ", strip=True))
        if text:
            ingredients.append(text)

    instructions = []
    for item in soup.find_all(attrs={"class": INSTRUCTION_CLASS_RE}):
        body = item.find(attrs={"class": PANTRY_BODY_RE})
        text = normalize((body or item).get_text(" ", strip=True))
        if text:
            instructions.append(text)

    return Recipe(
        title=_title_from_dom(soup),
        ingredient_groups=[IngredientGroup(items=ingredients)] if ingredients else [],
        instructions=instructions,
        image_url=_image_from_dom(soup),
    )


def _title_from_dom(soup):
    if not soup.title or not soup.title.string:
        return ""
    title = soup.title.string
    for suffix in (" Recipe", " - NYT Cooking"):
        title = title.replace(suffix, "")
    return normalize(title)


def _image_from_dom(soup):
    """
    The old code pinned a full class hash, recipeheaderimage_...__X9zME, which
    no longer exists. Prefer og:image, which is a published contract.
    """
    meta = soup.find("meta", attrs={"property": "og:image"})
    if meta and meta.get("content"):
        return _absolute(meta["content"])
    return None


# ─── Grouping ─────────────────────────────────────────────────────────────────

def _apply_dom_groups(recipe, soup):
    """
    Lay the DOM's group headings back over the flat ingredient list.

    Walks the ingredient elements in document order alongside the group
    headings that precede them, then checks the reconstructed list matches what
    we already have. If it does not, the flat list is kept: a missing heading
    is a cosmetic loss, a missing ingredient is a real one.
    """
    headings = soup.find_all(attrs={"class": GROUP_NAME_CLASS_RE})
    if not headings:
        return

    groups = []
    current = None
    for tag in soup.find_all(attrs={"class": [GROUP_NAME_CLASS_RE, INGREDIENT_CLASS_RE]}):
        classes = " ".join(tag.get("class") or [])
        if GROUP_NAME_CLASS_RE.search(classes):
            current = IngredientGroup(items=[], heading=normalize(tag.get_text(" ", strip=True)))
            groups.append(current)
        else:
            text = normalize(tag.get_text(" ", strip=True))
            if not text:
                continue
            if current is None:
                current = IngredientGroup(items=[], heading=None)
                groups.append(current)
            current.items.append(text)

    groups = [g for g in groups if g.items]
    regrouped = [item for g in groups for item in g.items]
    if regrouped == recipe.ingredients:
        recipe.ingredient_groups = groups
