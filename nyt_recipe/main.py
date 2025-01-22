# (c) 2021 Ian Brault
# This code is licensed under the MIT License (see LICENSE.txt for details)
# Changes to allow for PDF and HTML writing with inclusion of header photo by Matthew St. Jean, 2025

import argparse
import os
import sys  # <-- Add this line to fix the error
import requests
import pdfkit
from bs4 import BeautifulSoup
from output import *
from recipe import Recipe
import subprocess


def download_image(image_url, output_path, image_name):
    try:
        # Download the image
        response = requests.get(image_url)
        response.raise_for_status()

        # Get the file extension from the URL
        file_extension = os.path.splitext(image_url)[-1]
        image_path = os.path.join(output_path, f"{image_name}{file_extension}")

        # Save the image to the output directory
        with open(image_path, "wb") as img_file:
            img_file.write(response.content)
        print(f"Image saved as {image_path}")
        return image_path  # Return the image file path
    except requests.exceptions.RequestException as ex:
        error(f"Failed to download image from {image_url}")
        debug(str(ex))
        return None


def save_recipe(recipe, output_path, output_format, image_url=None):
    # Generate the image tag if an image URL is provided
    image_tag = ""
    if image_url:
        image_tag = f'<img src="{image_url}" alt="{recipe.title}">'

    # Check the desired output format
    if output_format == "pdf":
        # Handle PDF saving logic
        recipe_html = recipe.to_html(image_tag=image_tag)
        stem = recipe.title.lower().replace(" ", "_").replace("'", "")
        pdf_file = os.path.join(output_path, f"{stem}.pdf")
        debug(f"saving to {pdf_file}")

        try:
            # Use wkhtmltopdf to generate a PDF from HTML content
            command = [
                "wkhtmltopdf",
                "-",
                pdf_file,
            ]  # "-" means input is coming from stdin
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
    else:
        # Default to HTML
        recipe_html = recipe.to_html(image_tag=image_tag)
        stem = recipe.title.lower().replace(" ", "_").replace("'", "")
        recipe_file = os.path.join(output_path, f"{stem}.html")
        debug(f"saving to {recipe_file}")

        try:
            with open(recipe_file, "w") as f:
                f.write(recipe_html)
        except (IOError, OSError) as ex:
            error(f"failed to write the recipe file {recipe_file}")
            debug(str(ex))

        print(f'Saved recipe "{recipe.title}" to {recipe_file}')


def download_and_save_recipe(url, output_path, output_format):
    print(f"Downloading recipe from: {url}")
    try:
        debug(f"Fetching from {url}")
        raw = requests.get(url).text
        print(f"Fetched HTML content, length: {len(raw)}")
    except requests.exceptions.RequestException as ex:
        error(f"Failed to get the recipe from {url}")
        debug(str(ex))
        return

    print("Extracting recipe data...")
    soup = BeautifulSoup(raw, "html.parser")

    # Extract the recipe image URL from the div with the specified class
    image_div = soup.find(
        "div", class_="recipeheaderimage_imageAndButtonContainer__X9zME"
    )
    image_url = None
    if image_div:
        # Look for an inline style or background image URL within the div
        style = image_div.get("style", "")
        if "background-image" in style:
            image_url = style.split("url(")[-1].split(")")[0].strip('"')

        if not image_url:
            img_tag = image_div.find("img")
            if img_tag:
                image_url = img_tag.get("src")

    print(f"Extracted recipe title: {soup.title.string}")
    recipe = Recipe.from_html(raw)

    # Save the recipe with the image embedded in the HTML or as a PDF
    save_recipe(recipe, output_path, output_format, image_url=image_url)
    print("Recipe saved!")


def parse_args(args):
    parser = argparse.ArgumentParser(
        description="Downloads recipes from NYT Cooking and saves them in a "
        "format that can be easily imported by Apple Notes."
    )

    parser.add_argument("url", metavar="URL", nargs="+")
    parser.add_argument(
        "-o",
        "--output",
        metavar="PATH",
        default=os.path.join(
            os.environ.get("USERPROFILE", ""), "recipes"
        ),  # Use USERPROFILE on Windows
        help="Output directory, defaults to ~/recipes",
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable debug output"
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["html", "pdf"],
        default="html",  # Add format option
        help="Format to save the recipe in (html or pdf), default is html",
    )

    return parser.parse_args(args)


if __name__ == "__main__":
    print("Script started...")
    args = parse_args(sys.argv[1:])
    toggle_debug(args.debug)
    if not isinstance(args.url, list):
        args.url = [args.url]
    for url in args.url:
        download_and_save_recipe(url, args.output, args.format)
