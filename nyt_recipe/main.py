import argparse
import os
import sys
import requests
import subprocess
from bs4 import BeautifulSoup
from output import *
from recipe import Recipe

def download_image(image_url, output_path, image_name):
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        file_extension = os.path.splitext(image_url)[-1]
        image_path = os.path.join(output_path, f"{image_name}{file_extension}")
        with open(image_path, "wb") as img_file:
            img_file.write(response.content)
        print(f"Image saved as {image_path}")
        return image_path
    except requests.exceptions.RequestException as ex:
        error(f"Failed to download image from {image_url}: {ex}")
        return None

def save_recipe_as_pdf(recipe_html, output_path, recipe_title):
    stem = recipe_title.lower().replace(" ", "_").replace("'", "")
    pdf_file = os.path.join(output_path, f"{stem}.pdf")
    debug(f"saving to {pdf_file}")
    try:
        command = ["wkhtmltopdf", "-", pdf_file]
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        process.communicate(input=recipe_html.encode())
        print(f"PDF saved to {pdf_file}")
    except Exception as e:
        error(f"Error generating PDF: {e}")

def save_recipe_as_html(recipe_html, output_path, recipe_title):
    stem = recipe_title.lower().replace(" ", "_").replace("'", "")
    recipe_file = os.path.join(output_path, f"{stem}.html")
    debug(f"saving to {recipe_file}")
    try:
        with open(recipe_file, "w") as f:
            f.write(recipe_html)
        print(f'Saved recipe "{recipe_title}" to {recipe_file}')
    except (IOError, OSError) as ex:
        error(f"Failed to write the recipe file {recipe_file}: {ex}")

def save_recipe(recipe, output_path, output_format, image_url=None):
    image_tag = f'<img src="{image_url}" alt="{recipe.title}">' if image_url else ""
    recipe_html = recipe.to_html(image_tag=image_tag)
    if output_format == "pdf":
        save_recipe_as_pdf(recipe_html, output_path, recipe.title)
    else:
        save_recipe_as_html(recipe_html, output_path, recipe.title)

def find_image_url(soup):
    image_div = soup.find("div", class_="recipeheaderimage_imageAndButtonContainer__X9zME")
    if image_div:
        style = image_div.get("style", "")
        if "background-image" in style:
            return style.split("url(")[-1].split(")")[0].strip('"')
        img_tag = image_div.find("img")
        if img_tag:
            return img_tag.get("src")
    return None

def download_and_save_recipe(url, output_path, output_format):
    print(f"Downloading recipe from: {url}")
    try:
        debug(f"Fetching from {url}")
        raw = requests.get(url).text
        print(f"Fetched HTML content, length: {len(raw)}")
    except requests.exceptions.RequestException as ex:
        error(f"Failed to get the recipe from {url}: {ex}")
        return
    soup = BeautifulSoup(raw, "html.parser")
    image_url = find_image_url(soup)
    recipe = Recipe.from_html(raw)
    save_recipe(recipe, output_path, output_format, image_url=image_url)
    print("Recipe saved!")

def parse_args(args):
    parser = argparse.ArgumentParser(
        description="Downloads recipes from NYT Cooking and saves them in a format that can be easily imported by Apple Notes."
    )
    parser.add_argument(
        "url",
        metavar="URL",
        nargs="*",  # Allow zero or more URLs
        help="The NYT Cooking recipe URL(s) to download. Leave blank to prompt interactively.",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="PATH",
        default=os.path.join(os.environ.get("USERPROFILE", ""), "recipes"),
        help="Output directory, defaults to ~/recipes",
    )
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug output")
    parser.add_argument(
        "-f",
        "--format",
        choices=["html", "pdf"],
        default="html",
        help="Format to save the recipe in (html or pdf), default is html",
    )
    return parser.parse_args(args)

if __name__ == "__main__":
    print("Script started...")
    args = parse_args(sys.argv[1:])
    toggle_debug(args.debug)

    if not args.url:
        url = input("Enter the NYT Cooking recipe URL: ").strip()
        if not url:
            print("No URL provided. Exiting.")
            sys.exit(1)
        args.url = [url]

    for url in args.url:
        download_and_save_recipe(url, args.output, args.format)
