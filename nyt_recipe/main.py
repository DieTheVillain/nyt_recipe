"""
Command line entry point.

Fetches one or more NYT Cooking recipes and writes them out as HTML, PDF or
Markdown.
"""

import argparse
import os
import sys

import requests

from .extract import ExtractionError, from_html
from .output import debug, error, toggle_debug
from .render.html import to_html
from .render.markdown import to_markdown
from .render.pdf import PdfError, to_pdf

# NYT serves a trimmed page to clients that look automated.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0 Safari/537.36"
)

FORMATS = ("pdf", "html", "markdown")
THEMES = ("light", "dark", "serif")

# Saved files carry their origin, so a recipe stays identifiable once it is
# sitting in a folder alongside files from everywhere else.
FILENAME_PREFIX = "NYT Cooking - "


def fetch(url):
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    response.raise_for_status()
    return response.text


def safe_filename(title):
    """A recipe title is not a filename: slashes and colons are illegal."""
    cleaned = "".join("-" if c in '<>:"/\\|?*' else c for c in title)
    cleaned = " ".join(cleaned.split()).strip(" .")
    return cleaned or "recipe"


def recipe_filename(title):
    """The stem a saved recipe gets: its source, then a filesystem-safe title.

    The prefix is added after sanitising, so a title made entirely of illegal
    characters still produces a recognisable name rather than a bare one.
    """
    return f"{FILENAME_PREFIX}{safe_filename(title)}"


def save(recipe, output_path, output_format, theme="light"):
    os.makedirs(output_path, exist_ok=True)
    stem = recipe_filename(recipe.title)

    if output_format == "markdown":
        path = os.path.join(output_path, f"{stem}.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(to_markdown(recipe))
        return path

    html = to_html(recipe, theme=theme)
    if output_format == "html":
        path = os.path.join(output_path, f"{stem}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        return path

    path = os.path.join(output_path, f"{stem}.pdf")
    return to_pdf(html, path)


def download(url, output_path, output_format, theme="light"):
    """Fetch, parse and save one recipe. Returns the path, or None on failure."""
    debug(f"fetching {url}")
    try:
        raw = fetch(url)
    except requests.exceptions.RequestException as ex:
        error(f"Could not fetch {url}: {ex}")
        return None

    try:
        recipe = from_html(raw)
    except ExtractionError as ex:
        # Loud on purpose. The old code logged a warning and carried on to
        # write out a recipe with no ingredients.
        error(f"Could not read a recipe from {url}: {ex}")
        return None

    try:
        path = save(recipe, output_path, output_format, theme=theme)
    except PdfError as ex:
        error(str(ex))
        return None

    print(f'Saved "{recipe.title}" to {path}')
    return path


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Download recipes from NYT Cooking as PDF, HTML or Markdown."
    )
    parser.add_argument(
        "url", metavar="URL", nargs="*",
        help="Recipe URL(s). Leave blank to be prompted.",
    )
    parser.add_argument(
        "-o", "--output", metavar="PATH",
        default=os.path.join(os.path.expanduser("~"), "recipes"),
        help="Output directory (default: ~/recipes)",
    )
    parser.add_argument("-f", "--format", choices=FORMATS, default="pdf",
                        help="Output format (default: pdf)")
    parser.add_argument("-t", "--theme", choices=THEMES, default="light",
                        help="Visual theme for HTML and PDF (default: light)")
    parser.add_argument("-d", "--debug", action="store_true", help="Verbose output")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    toggle_debug(args.debug)

    urls = args.url or [input("Enter the NYT Cooking recipe URL: ").strip()]
    urls = [u for u in urls if u]
    if not urls:
        error("No URL given.")
        return 1

    failures = 0
    for url in urls:
        if download(url, args.output, args.format, theme=args.theme) is None:
            failures += 1

    # A non-zero exit means something did not come out, which matters when
    # this is driven from a script.
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
