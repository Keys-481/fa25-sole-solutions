import os
import csv
import codecs
from sole_solutions.core.io import read_text_lines_any_encoding, detect_header_start

BOM = "\ufeff"  # Invisible BOM character used by UTF-8-SIG / UTF-16


SAMPLE = (
    "Garbage line before header\n"
    "Subject,Id,Note\n"
    "Frame,Time,Units,1,2\n"
    "1,0.00,kPa,10,20\n"
    "2,0.01,kPa,11,21\n"
)

def _write_with_encoding(tmpdir, name, text, encoding):
    """Create a test file encoded with the specified encoding."""
    p = os.path.join(tmpdir, name)
    with codecs.open(p, "w", encoding=encoding) as f:
        f.write(text)
    return p


def test_read_text_lines_any_encoding_multiple_encodings(tmp_path):
    """Ensure we can read text files regardless of encoding (BOM-safe)."""
    for enc in ["utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "latin1", "utf-8"]:
        p = _write_with_encoding(tmp_path, f"file_{enc}.csv", SAMPLE, enc)
        lines = read_text_lines_any_encoding(str(p))
        assert lines is not None, f"Failed to read with encoding {enc}"

        idx = detect_header_start(lines)
        reader = csv.DictReader(lines[idx:])

        # Normalize any BOM that may appear on the first fieldname
        if reader.fieldnames:
            reader.fieldnames = [fn.lstrip(BOM) if fn else fn for fn in reader.fieldnames]

        rows = list(reader)
        assert rows, f"No rows parsed for {enc}"
        assert "Frame" in rows[0], f"'Frame' not found in row for {enc}; headers={reader.fieldnames}"
        assert rows[0]["Frame"] == "1"


def test_detect_header_start_no_marker_returns_zero():
    """Header detection should return 0 if no marker is found."""
    lines = ["a,b,c\n", "d,e,f\n"]
    assert detect_header_start(lines) == 0
