"""
The recipe as Markdown — the format that survives a paste into anything.

Deliberately plain: no HTML entities, no wrapping, fraction glyphs left as
they are so the text stays readable in a terminal, a notes app or a commit
message.
"""


def to_markdown(recipe):
    lines = [f"# {recipe.title}", ""]

    byline = []
    if recipe.author:
        byline.append(f"By {recipe.author}")
    if recipe.rating:
        stars = f"{recipe.rating:g}★"
        if recipe.rating_count:
            stars += f" ({recipe.rating_count})"
        byline.append(stars)
    if byline:
        lines += [" · ".join(byline), ""]

    if recipe.description:
        lines += [recipe.description, ""]

    meta = []
    if recipe.total_time:
        meta.append(f"**Time:** {recipe.total_time}")
    if recipe.servings:
        meta.append(f"**Yield:** {recipe.servings}")
    if meta:
        lines += ["  ".join(meta), ""]

    lines += ["## Ingredients", ""]
    for group in recipe.ingredient_groups:
        if group.heading:
            lines += [f"### {group.heading}", ""]
        lines += [f"- {item}" for item in group.items]
        lines.append("")

    lines += ["## Preparation", ""]
    lines += [f"{n}. {step}" for n, step in enumerate(recipe.instructions, 1)]
    lines.append("")

    if recipe.nutrition:
        lines += ["## Nutrition (per serving)", ""]
        lines += [f"- {_label(k)}: {v}" for k, v in recipe.nutrition.items()]
        lines.append("")

    if recipe.tags:
        lines += [f"**Tags:** {', '.join(recipe.tags)}", ""]
    if recipe.source_url:
        lines += [f"Source: {recipe.source_url}", ""]

    return "\n".join(lines).rstrip() + "\n"


def _label(key):
    text = key.replace("Content", "")
    return text[:1].upper() + "".join(f" {c.lower()}" if c.isupper() else c for c in text[1:])
