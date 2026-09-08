"""
The recipe as a page.

Two things the previous template got wrong. It interpolated recipe text into
HTML unescaped, so an ampersand in a title produced invalid markup. And it
rewrote ¼ ½ ¾ into HTML entities to work around a PDF engine that could not
draw them, which left the other fifteen fractions broken and is the wrong layer
to fix a font problem in. Text goes in as written; the renderer is made capable
instead.
"""

from html import escape

THEMES = {
    "light": {
        "bg": "#ffffff", "fg": "#1a1a1a", "muted": "#6b6b6b",
        "rule": "#e6e3dd", "accent": "#8a3324", "card": "#faf8f5",
        "font": "'Helvetica Neue', Helvetica, Arial, sans-serif",
    },
    "dark": {
        "bg": "#151312", "fg": "#ece7e1", "muted": "#9c948b",
        "rule": "#2f2a26", "accent": "#e2725b", "card": "#1e1b19",
        "font": "'Helvetica Neue', Helvetica, Arial, sans-serif",
    },
    "serif": {
        "bg": "#fdfcfa", "fg": "#201c18", "muted": "#6f665d",
        "rule": "#e3ddd3", "accent": "#7b3f00", "card": "#f6f2ec",
        "font": "Georgia, 'Iowan Old Style', 'Times New Roman', serif",
    },
}

# Fraction glyphs live outside many UI fonts. Naming families that carry them
# ahead of the theme font is what actually keeps ½ on the page — the previous
# entity rewrite was treating this as a text problem.
FRACTION_FONTS = "'DejaVu Sans', 'Segoe UI Symbol', 'Arial Unicode MS'"


def to_html(recipe, theme="light"):
    """Render a complete, standalone HTML document for one recipe."""
    palette = THEMES.get(theme, THEMES["light"])

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{escape(recipe.title)}</title>
<style>{_stylesheet(palette)}</style>
</head>
<body>
<article class="recipe">
  <header>
    <h1>{escape(recipe.title)}</h1>
    {_byline(recipe)}
    {_image(recipe)}
    {_description(recipe)}
    {_meta_row(recipe)}
  </header>
  <div class="columns">
    <section class="ingredients">
      <h2>Ingredients</h2>
      {_ingredients(recipe)}
    </section>
    <section class="instructions">
      <h2>Preparation</h2>
      <ol>{_instructions(recipe)}</ol>
    </section>
  </div>
  {_nutrition(recipe)}
  {_footer(recipe)}
</article>
</body>
</html>"""


def _stylesheet(p):
    return f"""
  @page {{ margin: 18mm 16mm; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 32px;
    background: {p['bg']}; color: {p['fg']};
    font-family: {FRACTION_FONTS}, {p['font']};
    line-height: 1.55; font-size: 15px;
  }}
  .recipe {{ max-width: 900px; margin: 0 auto; }}
  h1 {{ font-size: 34px; line-height: 1.15; margin: 0 0 6px; letter-spacing: -0.01em; }}
  h2 {{
    font-size: 12px; text-transform: uppercase; letter-spacing: .16em;
    color: {p['muted']}; margin: 0 0 12px;
    padding-bottom: 8px; border-bottom: 1px solid {p['rule']};
  }}
  .byline {{ color: {p['muted']}; font-size: 14px; margin: 0 0 14px; }}
  .hero {{ width: 100%; height: auto; border-radius: 4px; margin: 6px 0 18px; }}
  .description {{ color: {p['fg']}; margin: 0 0 18px; }}

  .meta {{
    display: flex; flex-wrap: wrap; gap: 10px;
    padding: 12px 14px; margin: 0 0 26px;
    background: {p['card']}; border: 1px solid {p['rule']}; border-radius: 4px;
  }}
  .meta div {{ font-size: 13px; }}
  .meta .label {{
    display: block; font-size: 10px; text-transform: uppercase;
    letter-spacing: .14em; color: {p['muted']}; margin-bottom: 2px;
  }}
  .meta div + div {{ padding-left: 10px; border-left: 1px solid {p['rule']}; }}

  /* Ingredients beside the method, the way a recipe card reads. Falls back to
     one column on narrow screens and stays two-up in print. */
  .columns {{ display: grid; grid-template-columns: 1fr 1.6fr; gap: 34px; align-items: start; }}
  @media (max-width: 680px) {{ .columns {{ grid-template-columns: 1fr; gap: 26px; }} }}

  .ingredients ul {{ list-style: none; margin: 0 0 18px; padding: 0; }}
  .ingredients li {{ padding: 6px 0; border-bottom: 1px solid {p['rule']}; }}
  .ingredients h3 {{
    font-size: 11px; text-transform: uppercase; letter-spacing: .14em;
    color: {p['accent']}; margin: 18px 0 6px;
  }}
  .ingredients h3:first-child {{ margin-top: 0; }}

  .instructions ol {{ margin: 0; padding-left: 20px; }}
  .instructions li {{ margin-bottom: 14px; padding-left: 4px; }}

  .nutrition {{ margin-top: 30px; }}
  .nutrition ul {{
    list-style: none; padding: 0; margin: 0;
    display: flex; flex-wrap: wrap; gap: 8px 18px; font-size: 13px; color: {p['muted']};
  }}
  footer {{
    margin-top: 30px; padding-top: 14px; border-top: 1px solid {p['rule']};
    font-size: 12px; color: {p['muted']};
  }}
  footer a {{ color: inherit; }}
  .tags {{ margin-top: 4px; }}
"""


def _byline(recipe):
    bits = []
    if recipe.author:
        bits.append(f"By {escape(recipe.author)}")
    if recipe.rating:
        stars = f"{recipe.rating:g}★"
        if recipe.rating_count:
            stars += f" ({recipe.rating_count})"
        bits.append(stars)
    return f'<p class="byline">{" · ".join(bits)}</p>' if bits else ""


def _image(recipe):
    if not recipe.image_url:
        return ""
    return f'<img class="hero" src="{escape(recipe.image_url, quote=True)}" alt="{escape(recipe.title)}">'


def _description(recipe):
    return f'<p class="description">{escape(recipe.description)}</p>' if recipe.description else ""


def _meta_row(recipe):
    cells = []
    if recipe.total_time:
        cells.append(("Time", recipe.total_time))
    if recipe.servings:
        cells.append(("Yield", recipe.servings))
    if not cells:
        return ""
    inner = "".join(
        f'<div><span class="label">{escape(label)}</span>{escape(value)}</div>'
        for label, value in cells
    )
    return f'<div class="meta">{inner}</div>'


def _ingredients(recipe):
    blocks = []
    for group in recipe.ingredient_groups:
        if group.heading:
            blocks.append(f"<h3>{escape(group.heading)}</h3>")
        items = "".join(f"<li>{escape(item)}</li>" for item in group.items)
        blocks.append(f"<ul>{items}</ul>")
    return "".join(blocks)


def _instructions(recipe):
    return "".join(f"<li>{escape(step)}</li>" for step in recipe.instructions)


def _nutrition(recipe):
    if not recipe.nutrition:
        return ""
    items = "".join(
        f"<li><strong>{escape(_label(k))}</strong> {escape(str(v))}</li>"
        for k, v in recipe.nutrition.items()
    )
    return f'<section class="nutrition"><h2>Nutrition (per serving)</h2><ul>{items}</ul></section>'


def _label(key):
    """calorieContent -> Calorie, fatContent -> Fat."""
    text = key.replace("Content", "")
    return text[:1].upper() + "".join(f" {c.lower()}" if c.isupper() else c for c in text[1:])


def _footer(recipe):
    bits = []
    if recipe.source_url:
        url = escape(recipe.source_url, quote=True)
        bits.append(f'<div>Source: <a href="{url}">{escape(recipe.source_url)}</a></div>')
    if recipe.tags:
        tags = ", ".join(escape(t) for t in recipe.tags)
        bits.append(f'<div class="tags">{tags}</div>')
    return f"<footer>{''.join(bits)}</footer>" if bits else ""
