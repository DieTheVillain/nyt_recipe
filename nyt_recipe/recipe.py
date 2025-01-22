# (c) 2021 Ian Brault
# This code is licensed under the MIT License (see LICENSE.txt for details)
# Changes to allow for PDF and HTML writing with inclusion of header photo by Matthew St. Jean, 2025

import bs4
import re
from output import *

TEMPLATE = """\
<html>
<body>
    <h1>{title}</h1>
    <div>{image_tag}</div>
    <p>{serving_size}</p>
    <br>
    <h2>Ingredients</h2>
    <ul>
{ingredients}
    </ul>
    <br>
    <h2>Instructions</h2>
    <ol>
{instructions}
    </ol>
</body>
</html>
"""


def _title_from_soup(soup):
    title = soup.title.string
    if title is None:
        warn("recipe is missing a title")
        title = ""
    # strip the " - NYT Cooking" suffix and "Recipe"
    title = title.replace(" Recipe", "").replace(" - NYT Cooking", "").strip()

    debug(f"title: {title}")
    return title


def _serving_size_from_soup(soup):
    serving = ""

    yield_span = soup.find("span", string="Yield:")
    if yield_span is None:
        warn("recipe is missing a serving size")
        return serving
    serving_span = yield_span.next_sibling
    if serving_span is None:
        warn("recipe is missing a serving size")
        return serving

    serving = serving_span.text.strip()
    debug(f"serving size: {serving}")
    return serving


def _ingredients_from_soup(soup):
    ingredients = []
    class_re = re.compile(r"ingredient_ingredient__.+")

    ingredients_list = soup.findAll("li", attrs={"class": class_re})
    if not ingredients_list:
        warn("recipe is missing ingredients")
        return ingredients

    for item in ingredients_list:
        ingredient = " ".join(tag.text.strip() for tag in item.children)

        # Normalize ingredient string to ensure proper encoding
        ingredient = ingredient.replace(
            "\xa0", " "
        ).strip()  # Replace non-breaking spaces with regular spaces

        debug(f"ingredient: {ingredient}")
        ingredients.append(ingredient)

    return ingredients


def _instructions_from_soup(soup):
    instructions = []
    class_re = re.compile(r"preparation_step__.+")

    instructions_list = soup.findAll("li", attrs={"class": class_re})
    if not instructions_list:
        warn("recipe is missing instructions")
        return instructions

    for item in instructions_list:
        step_tag = item.find("p", attrs={"class": "pantry--body-long"})
        if not step_tag:
            warn("instruction is missing text")
            continue
        instruction = step_tag.text.strip()
        debug(f"instruction: {instruction}")
        instructions.append(instruction)

    return instructions


class Recipe(object):
    def __init__(self, title, ingredients, instructions, image_url=None):
        self.title = title
        self.ingredients = ingredients
        self.instructions = instructions
        self.image_url = image_url

    def _sanitize_text(self, text):
        """
        Sanitize text to handle special characters properly.
        """
        return (
            text.replace("¼", "&frac14;")
            .replace("½", "&frac12;")
            .replace("¾", "&frac34;")
        )

    def to_html(self, image_tag=None):
        double_tab = " " * 8

        # Add image tag after the title
        ingredients = "\n".join(
            f"{double_tab}<li>{self._sanitize_text(i)}</li>" for i in self.ingredients
        )
        instructions = "\n".join(
            f"{double_tab}<li>{self._sanitize_text(i)}</li>" for i in self.instructions
        )

        # Updated TEMPLATE to include a meta charset tag for proper encoding
        updated_template = """\
<html>
<head>
    <meta charset="utf-8">
</head>
<body>
    <h1>{title}</h1>
    {image_tag}
    <br>
    <h2>Ingredients</h2>
    <ul>
{ingredients}
    </ul>
    <br>
    <h2>Instructions</h2>
    <ol>
{instructions}
    </ol>
</body>
</html>
"""

        # Format HTML output using the updated template
        return updated_template.format(
            title=self.title,
            image_tag=image_tag if image_tag else "",
            ingredients=ingredients,
            instructions=instructions,
        )

    @staticmethod
    def from_html(raw):
        soup = bs4.BeautifulSoup(raw, "html.parser")

        title = _title_from_soup(soup)
        serving_size = _serving_size_from_soup(soup)
        ingredients = _ingredients_from_soup(soup)
        instructions = _instructions_from_soup(soup)

        return Recipe(title, ingredients, instructions)
