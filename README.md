# NYT Recipe

Save recipes from [NYT Cooking](https://cooking.nytimes.com/) as PDF, HTML or
Markdown — from the command line, or from Discord with `/recipe`.

Based on the work of Ian Brault at https://github.com/ianbrault/nyt_recipe

---

## What it captures

Title, ingredients (with their **group headings**, such as "FOR THE CAKE"),
preparation steps, and the things NYT publishes that most scrapers drop:
description, author, total time, yield, nutrition, rating and tags.

Quantities are preserved exactly as written — `1 ½ teaspoons`, `½ to 1 ½
cups/118 to 355 milliliters` — with mixed numbers bound so they never break
across a line.

---

## Installation

Requires Python 3.9 or newer.

```bash
git clone https://github.com/DieTheVillain/nyt_recipe.git
cd nyt_recipe
pip install -r nyt_recipe/requirements.txt
```

### PDF output

PDF works out of the box if you have **Google Chrome** or **Edge** installed —
no configuration needed.

Optionally, install [WeasyPrint](https://doc.courtbouillon.org/weasyprint/)
with its GTK runtime and it will be used instead. On Windows the GTK libraries
are not present by default and WeasyPrint will fail to import; the renderer
notices and falls back to Chrome on its own.

HTML and Markdown need neither.

---

## Command line

```bash
python -m nyt_recipe.main [options] <URL> [<URL> ...]
```

| Option | Meaning |
|---|---|
| `-f`, `--format` | `pdf` (default), `html` or `markdown` |
| `-t`, `--theme` | `light` (default), `dark` or `serif` |
| `-o`, `--output` | Output directory (default `~/recipes`) |
| `-d`, `--debug` | Verbose output |
| `-h`, `--help` | Usage |

Run it with no URL and it will ask for one. Exits non-zero if any recipe
could not be saved, so it is safe to drive from a script.

### Examples

```bash
# A PDF in the serif theme
python -m nyt_recipe.main -f pdf -t serif \
  https://cooking.nytimes.com/recipes/1018301-apple-cider-honey-cake

# Markdown, several at once, into a chosen folder
python -m nyt_recipe.main -f markdown -o C:\recipes URL1 URL2
```

---

## Discord bot

`/recipe url:<NYT URL> [file_format:] [theme:] [preview:]`

`preview: true` prints the recipe into the channel instead of attaching a file.

The bot reads its token from the `DISCORD_BOT_TOKEN` environment variable:

```bash
set DISCORD_BOT_TOKEN=your-token-here      # Windows
export DISCORD_BOT_TOKEN=your-token-here   # macOS / Linux
python -m nyt_recipe.bot
```

For local convenience it will also read `config.json` — copy
`config.json.example` and fill it in. **That file is gitignored and must never
be committed.** Set `RECIPE_OUTPUT_DIR` to change where files are written.

---

## Tests

```bash
pip install pytest pypdf
python -m pytest
```

The tests run against saved NYT pages in `tests/fixtures/`, so they need no
network and cannot drift with the site. They cover the full Unicode fraction
set, ingredient grouping, the fallback path when the structured data is
missing, and a real PDF render whose fraction glyphs are read back out of the
finished file.

Skip the PDF test with `-m "not slow"`.

### When NYT changes their markup

The recipe data is read from the schema.org JSON-LD block NYT publishes for
search engines, which is far more stable than their CSS class names — those
are content-hashed and have broken this tool before. HTML scraping remains as
a fallback.

If a page yields no ingredients, extraction **raises** rather than returning an
empty recipe, so a silent failure shows up immediately instead of arriving as
a well-formatted PDF with nothing in it. Re-download the fixtures and run the
tests to see what changed.
