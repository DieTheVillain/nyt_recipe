"""
The recipe itself. Data only.

This module used to parse HTML, model a recipe and emit a styled document all
at once, with unreachable code after its template. Parsing now lives in
extract.py and rendering in render/, leaving this file with one job.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class IngredientGroup:
    """
    A run of ingredients under an optional heading, such as "FOR THE CAKE".

    NYT's JSON-LD flattens these away, so headings are recovered from the DOM.
    A recipe with no groups is one group with no heading, which keeps every
    consumer on a single code path.
    """

    items: List[str] = field(default_factory=list)
    heading: Optional[str] = None


@dataclass
class Recipe:
    title: str
    ingredient_groups: List[IngredientGroup] = field(default_factory=list)
    instructions: List[str] = field(default_factory=list)

    # Everything below is published by NYT and was previously discarded.
    description: Optional[str] = None
    author: Optional[str] = None
    source_url: Optional[str] = None
    image_url: Optional[str] = None
    total_time: Optional[str] = None
    servings: Optional[str] = None
    nutrition: dict = field(default_factory=dict)
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    tags: List[str] = field(default_factory=list)

    @property
    def ingredients(self):
        """Every ingredient in order, regardless of grouping."""
        return [item for group in self.ingredient_groups for item in group.items]

    @property
    def is_grouped(self):
        return any(group.heading for group in self.ingredient_groups)
