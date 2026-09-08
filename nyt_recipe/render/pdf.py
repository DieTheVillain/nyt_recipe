"""
HTML to PDF.

Replaces wkhtmltopdf, which is discontinued and drops glyphs it has no font
for — the direct cause of fractions going missing, and of the entity-rewriting
workaround that only ever covered ¼ ½ ¾.

Two engines are supported and picked at run time:

* **WeasyPrint** — preferred. Pure Python and pip-installable, but its
  rendering is backed by GTK libraries that are not present on a stock Windows
  install, where importing it fails with a missing `libgobject-2.0-0`.
* **Headless Chrome** — the fallback, and what actually runs on Windows today.
  Verified to preserve all eighteen Unicode vulgar fractions through a full
  render-and-read-back cycle.

Choosing at run time means installing the GTK runtime later silently upgrades
the output, and nobody has to install anything today.
"""


import os
import shutil
import subprocess
import sys
import tempfile


class PdfError(Exception):
    """Raised when no PDF engine is available, or one fails."""


CHROME_CANDIDATES = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "google-chrome",
    "chromium",
    "chromium-browser",
)


def to_pdf(html, path):
    """Render an HTML string to a PDF at `path`. Returns the path."""
    if _weasyprint_available():
        return _with_weasyprint(html, path)

    chrome = find_chrome()
    if chrome:
        return _with_chrome(html, path, chrome)

    raise PdfError(
        "No PDF engine available. Install WeasyPrint with its GTK runtime, or "
        "install Google Chrome, or export to HTML or Markdown instead."
    )


def available_engine():
    """Name of the engine that would be used, or None. Useful in diagnostics."""
    if _weasyprint_available():
        return "weasyprint"
    return "chrome" if find_chrome() else None


_WEASYPRINT = None


def _weasyprint_available():
    """
    Probe once, in a subprocess.

    When its GTK libraries are missing, WeasyPrint prints a multi-line banner
    pointing at its install docs and then raises OSError rather than
    ImportError. The banner does not go through anything this process can
    redirect — silencing file descriptor 2 around the import does not catch it
    — and it is WeasyPrint's business, not the user's, who asked for a recipe.

    So the import is attempted in a child process whose output goes nowhere,
    and the answer is cached. The cost is one interpreter start, once.
    """
    global _WEASYPRINT
    if _WEASYPRINT is None:
        try:
            result = subprocess.run(
                [sys.executable, "-c", "import weasyprint"],
                capture_output=True,
                timeout=60,
            )
            _WEASYPRINT = result.returncode == 0
        except (OSError, subprocess.SubprocessError):
            _WEASYPRINT = False
    return _WEASYPRINT


def _with_weasyprint(html, path):
    from weasyprint import HTML

    HTML(string=html).write_pdf(path)
    return path


def find_chrome():
    for candidate in CHROME_CANDIDATES:
        if os.path.isabs(candidate):
            if os.path.exists(candidate):
                return candidate
        else:
            found = shutil.which(candidate)
            if found:
                return found
    return None


def _with_chrome(html, path, chrome):
    # Chrome prints from a file rather than stdin; a temporary one keeps the
    # document self-contained.
    handle, source = tempfile.mkstemp(suffix=".html")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as f:
            f.write(html)

        result = subprocess.run(
            [
                chrome,
                "--headless",
                "--disable-gpu",
                "--no-pdf-header-footer",
                f"--print-to-pdf={os.path.abspath(path)}",
                _file_url(source),
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if not os.path.exists(path):
            raise PdfError(
                f"Chrome produced no PDF (exit {result.returncode}): "
                f"{(result.stderr or '').strip()[:400]}"
            )
        return path
    finally:
        try:
            os.unlink(source)
        except OSError:
            pass


def _file_url(path):
    return "file:///" + os.path.abspath(path).replace("\\", "/")
