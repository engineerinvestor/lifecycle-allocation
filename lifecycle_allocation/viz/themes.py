"""Consistent visual theme for lifecycle-allocation charts."""

from __future__ import annotations

from typing import Any

from matplotlib.axes import Axes

THEME: dict[str, Any] = {
    "colors": {
        "wealth": "#2196F3",
        "human_capital": "#4CAF50",
        "total": "#1565C0",
        "choi": "#2196F3",
        "sixty_forty": "#FF9800",
        "n_minus_age": "#9C27B0",
        "tdf": "#F44336",
        "user": "#607D8B",
        "leveraged": "#E91E63",
    },
    "figsize": (8, 5),
    "bar_width": 0.6,
    "font_size": {
        "title": 14,
        "label": 11,
        "annotation": 10,
        "tick": 9,
    },
}


def apply_theme(ax: Axes) -> None:
    """Apply consistent styling to a matplotlib axes."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=THEME["font_size"]["tick"])
