import os
import sys

# Put the package's parent on the path so `import nyt_recipe...` works when
# pytest is run from the repository root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def fixture(name):
    """Read a saved NYT Cooking page by name."""
    with open(os.path.join(FIXTURE_DIR, name), encoding="utf-8") as f:
        return f.read()
