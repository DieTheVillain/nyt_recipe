@echo off
title NYT Recipe Bot
REM Runs from wherever this file lives, so the repo can be moved or cloned
REM anywhere. The bot must start as a module -- "python nyt_recipe\bot.py"
REM fails, because the package uses relative imports.
cd /d "%~dp0"

REM The token comes from the DISCORD_BOT_TOKEN environment variable, or from
REM config.json beside this file. Never put the token in this script -- it is
REM committed to the repository; config.json is not.
python -m nyt_recipe.bot

REM Keep the window open if the bot exits, so the reason stays readable.
echo.
echo Bot stopped. Press any key to close.
pause >nul
