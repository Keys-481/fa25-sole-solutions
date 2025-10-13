"""
Helper file for text and CSV input handling.
Provides encoding-robust line reading and header detection.
"""

from __future__ import annotations
from typing import Optional, List


def _decode_bytes_safely(b: bytes) -> Optional[str]:
    """Decode bytes to text using BOM and UTF-16 heuristics before fallbacks."""
    if not b:
        return ""

    # --- BOM-based detection ---
    if b.startswith(b"\xef\xbb\xbf"):  # UTF-8 BOM
        try:
            return b.decode("utf-8-sig")
        except Exception:
            pass
    if b.startswith(b"\xff\xfe"):  # UTF-16 LE BOM
        try:
            return b.decode("utf-16")
        except Exception:
            pass
    if b.startswith(b"\xfe\xff"):  # UTF-16 BE BOM
        try:
            return b.decode("utf-16")
        except Exception:
            pass

    # --- Heuristic for UTF-16 without BOM ---
    # ASCII text encoded as UTF-16 tends to have many NUL bytes in one lane.
    # For LE, b[1::2] ~ 0x00; for BE, b[0::2] ~ 0x00.
    if len(b) >= 4 and len(b) % 2 == 0:
        le_zeros = sum(1 for x in b[1::2] if x == 0x00)
        be_zeros = sum(1 for x in b[0::2] if x == 0x00)
        lane = max(le_zeros, be_zeros)
        # If at least 25% of positions in a lane are NULs, treat as UTF-16.
        if lane >= (len(b) // 4):
            try:
                return b.decode("utf-16-le" if le_zeros >= be_zeros else "utf-16-be")
            except Exception:
                pass

    # --- Safe fallbacks ---
    for enc in ("utf-8", "latin1"):
        try:
            return b.decode(enc)
        except Exception:
            continue
    return None


def read_text_lines_any_encoding(path: str) -> Optional[List[str]]:
    """Read a text file into lines with robust decoding from bytes."""
    try:
        with open(path, "rb") as fb:
            raw = fb.read()
    except Exception:
        return None

    text = _decode_bytes_safely(raw)
    if text is None:
        return None
    return text.splitlines(True)  # keepends=True


def detect_header_start(lines: List[str]) -> int:
    """Find the first likely header row in a list of CSV lines.

    Prefer a row that starts with 'Frame' (actual CSV header). If none exists,
    fall back to a row that starts with 'Subject'. If still not found, return 0.
    BOM (\\ufeff) and stray NULs (\\x00) are ignored for matching.
    """
    BOM = "\ufeff"

    def clean(s: str) -> str:
        return s.lstrip(BOM).replace("\x00", "").strip()

    # Prefer the actual CSV header (Frame,...)
    for i, line in enumerate(lines):
        if clean(line).startswith("Frame"):
            return i

    # Fallback: metadata-style header some files include
    for i, line in enumerate(lines):
        if clean(line).startswith("Subject"):
            return i

    return 0
