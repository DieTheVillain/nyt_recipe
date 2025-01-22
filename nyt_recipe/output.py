# (c) 2021 Ian Brault
# This code is licensed under the MIT License (see LICENSE.txt for details)
# Changes to allow for PDF and HTML writing with inclusion of header photo by Matthew St. Jean, 2025

DEBUG = False


def toggle_debug(enabled):
    global DEBUG
    DEBUG = enabled


def error(text):
    print(f"\u001b[31merror: {text}\u001b[0m")


def warn(text):
    print(f"\u001b[33mwarning: {text}\u001b[0m")


def debug(text):
    if DEBUG:
        print(f"\u001b[32m{text}\u001b[0m")
