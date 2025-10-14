"""
Helper file for metadata calculations and pagination.
Contains small, testable utility functions with no UI dependencies.
"""

from __future__ import annotations
from typing import List, Dict


def clamp_height(ft: int, inch: int) -> tuple[int, int]:
    """Clamp height values to a reasonable range."""
    ft = max(3, min(ft, 8))
    inch = max(0, min(inch, 11))
    return ft, inch


def inches_to_cm(ft: int, inch: int) -> float:
    """Convert height in feet/inches to centimeters."""
    total_in = ft * 12 + inch
    return round(total_in * 2.54, 1)


def clamp_weight_lb(lb: int) -> int:
    """Clamp weight (in pounds) to a reasonable range."""
    return max(60, min(lb, 350))


def paginate(
    rows: List[Dict],
    rows_per_page: int,
    page_index: int,
) -> tuple[List[Dict], int, int]:
    """Paginate a list of dictionary rows.

    Args:
        rows: The data to paginate.
        rows_per_page: Number of rows per page.
        page_index: 0-based page index.

    Returns:
        (page_rows, current_page_number, total_pages)
    """
    if not rows:
        return [], 0, 0

    rows_per_page = max(1, int(rows_per_page))
    max_page_index = (len(rows) - 1) // rows_per_page
    page = max(0, min(page_index, max_page_index))

    start = page * rows_per_page
    end = start + rows_per_page
    page_rows = rows[start:end]

    return page_rows, page + 1, max_page_index + 1
