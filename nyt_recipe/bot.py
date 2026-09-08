"""
Discord bot: /recipe <url> returns the recipe as a file or a preview.

The token is read from the DISCORD_BOT_TOKEN environment variable, falling back
to a gitignored config.json for local convenience. It is never committed — see
config.json.example.
"""

import asyncio
import json
import os
import sys

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from .extract import ExtractionError, from_html
from .main import USER_AGENT, safe_filename, save
from .render.pdf import PdfError

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

FORMATS = ("pdf", "html", "markdown")
THEMES = ("light", "dark", "serif")

# Discord rejects messages over 2000 characters.
MESSAGE_LIMIT = 1900


def load_token():
    """Environment first; config.json is a local convenience, never committed."""
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if token:
        return token

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(here, "config.json")
    if os.path.exists(config_path):
        with open(config_path, encoding="utf-8") as f:
            token = json.load(f).get("DISCORD_BOT_TOKEN")
        if token:
            return token

    raise SystemExit(
        "No Discord token. Set DISCORD_BOT_TOKEN, or copy config.json.example "
        "to config.json and put the token there."
    )


def output_dir():
    return os.environ.get("RECIPE_OUTPUT_DIR") or os.path.join(
        os.path.expanduser("~"), "recipes"
    )


intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")


@bot.tree.command(name="recipe", description="Download a recipe from NYT Cooking")
@app_commands.describe(
    url="The NYT Cooking recipe URL",
    file_format="pdf, html or markdown",
    theme="light, dark or serif",
    preview="Show the recipe in chat instead of sending a file",
)
@app_commands.choices(
    file_format=[app_commands.Choice(name=f, value=f) for f in FORMATS],
    theme=[app_commands.Choice(name=t, value=t) for t in THEMES],
)
async def recipe_command(
    interaction: discord.Interaction,
    url: str,
    file_format: str = "pdf",
    theme: str = "light",
    preview: bool = False,
):
    await interaction.response.defer(thinking=True)

    try:
        raw = await fetch(url)
    except aiohttp.ClientError as ex:
        await interaction.followup.send(f"Could not fetch that page: {ex}")
        return
    except asyncio.TimeoutError:
        await interaction.followup.send("That page took too long to load.")
        return

    try:
        recipe = from_html(raw)
    except ExtractionError:
        # Never hand back a file that looks fine and has no ingredients.
        await interaction.followup.send(
            "I couldn't read a recipe from that page. Check it's an NYT Cooking "
            "recipe URL — if it is, NYT may have changed their markup again."
        )
        return

    if preview:
        await interaction.followup.send(format_preview(recipe))
        return

    try:
        path = await asyncio.to_thread(
            save, recipe, output_dir(), file_format, theme
        )
    except PdfError as ex:
        await interaction.followup.send(f"{ex}")
        return
    except OSError as ex:
        await interaction.followup.send(f"Could not write the file: {ex}")
        return

    await interaction.followup.send(
        f"**{recipe.title}**", file=discord.File(path, filename=os.path.basename(path))
    )


async def fetch(url):
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, headers={"User-Agent": USER_AGENT}) as response:
            response.raise_for_status()
            return await response.text()


def format_preview(recipe):
    """A readable chat summary, trimmed to Discord's message limit."""
    lines = [f"**{recipe.title}**"]

    meta = [b for b in (recipe.author and f"By {recipe.author}",
                        recipe.total_time, recipe.servings) if b]
    if meta:
        lines.append(" · ".join(meta))

    lines.append("")
    lines.append("**Ingredients**")
    for group in recipe.ingredient_groups:
        if group.heading:
            lines.append(f"*{group.heading}*")
        lines += [f"• {item}" for item in group.items]

    lines.append("")
    lines.append("**Preparation**")
    lines += [f"{n}. {step}" for n, step in enumerate(recipe.instructions, 1)]

    if recipe.source_url:
        lines += ["", f"<{recipe.source_url}>"]

    return trim(lines)


def trim(lines, limit=MESSAGE_LIMIT):
    """Drop whole lines from the end until it fits, rather than cutting a word
    in half or letting Discord reject the message outright."""
    text = "\n".join(lines)
    if len(text) <= limit:
        return text

    kept = []
    length = 0
    for line in lines:
        if length + len(line) + 1 > limit - 20:
            break
        kept.append(line)
        length += len(line) + 1
    kept.append("… (truncated)")
    return "\n".join(kept)


def run():
    bot.run(load_token())


if __name__ == "__main__":
    run()
