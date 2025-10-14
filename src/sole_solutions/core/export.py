"""
Helper file for exporting table data and plots.
Handles CSV writing and PNG saving without any UI dependencies.
"""

from __future__ import annotations
import csv
from typing import Sequence, Mapping
from matplotlib.figure import Figure


def write_table_csv(path: str, columns: Sequence[str], rows: Sequence[Mapping[str, object]]) -> None:
    """Write a list of row dicts to a CSV file."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([row.get(col, "") for col in columns])


def save_plot_png(fig: Figure, path: str, dpi: int = 150) -> None:
    """Save a matplotlib Figure as a PNG file."""
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
