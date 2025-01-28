import bs4
import re
from output import *

# Compiled regex patterns for better performance
ingredient_class_re = re.compile(r"ingredient_ingredient__.+")
instruction_class_re = re.compile(r"preparation_step__.+")
pantry_body_long_re = re.compile(r"pantry--body-long")

def _title_from_soup(soup):
    title = soup.title.string
    if title is None:
        warn("Recipe is missing a title")
        title = ""
    title = title.replace(" Recipe", "").replace(" - NYT Cooking", "").strip()
    debug(f"title: {title}")
    return title

def _serving_size_from_soup(soup):
    serving = ""
    yield_span = soup.find("span", string="Yield:")
    if yield_span is None:
        warn("Recipe is missing a serving size")
        return serving
    serving_span = yield_span.next_sibling
    if serving_span is None:
        warn("Recipe is missing a serving size")
        return serving
    serving = serving_span.text.strip()
    debug(f"serving size: {serving}")
    return serving

def _ingredients_from_soup(soup):
    ingredients = []
    ingredients_list = soup.findAll("li", attrs={"class": ingredient_class_re})
    if not ingredients_list:
        warn("Recipe is missing ingredients")
        return ingredients
    for item in ingredients_list:
        ingredient = " ".join(tag.text.strip() for tag in item.children)
        ingredient = ingredient.replace("\xa0", " ").strip()
        debug(f"ingredient: {ingredient}")
        ingredients.append(ingredient)
    return ingredients

def _instructions_from_soup(soup):
    instructions = []
    instructions_list = soup.findAll("li", attrs={"class": instruction_class_re})
    if not instructions_list:
        warn("Recipe is missing instructions")
        return instructions
    for item in instructions_list:
        step_tag = item.find("p", attrs={"class": pantry_body_long_re})
        if not step_tag:
            warn("Instruction is missing text")
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
        ingredients = "\n".join(
            f"{double_tab}<li>{self._sanitize_text(i)}</li>" for i in self.ingredients
        )
        instructions = "\n".join(
            f"{double_tab}<li>{self._sanitize_text(i)}</li>" for i in self.instructions
        )
        updated_template = """\
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: 'franklin', 'nyt-franklin', Arial, helvetica, sans-serif;
            font-size: 12px;
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }}
        h1 {{
            font-family: 'franklin', 'nyt-franklin', Arial, helvetica, sans-serif;
            font-size: 24px;
        }}
        p {{
            font-size: 12px;
            color: #333;
        }}
        img {{
            max-width: 100%;
            height: auto;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    {image_tag}
    <h2>Ingredients</h2>
    <ul>
{ingredients}
    </ul>
    <h2>Instructions</h2>
    <ol>
{instructions}
    </ol>
</body>
</html>
"""
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
