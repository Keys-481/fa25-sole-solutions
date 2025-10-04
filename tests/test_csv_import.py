import csv
import tempfile
import os
import pytest

@pytest.fixture
def sample_csv_file():
    """Create a temporary CSV file for testing."""
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "height", "weight"])
        writer.writerow(["Alice", "170", "60"])
        writer.writerow(["Bob", "180", "75"])
    yield path
    os.remove(path)


def test_csv_file_valid(sample_csv_file):
    """Confirm that the file exists and ends with .csv."""
    assert os.path.exists(sample_csv_file)
    assert sample_csv_file.lower().endswith(".csv")


def test_csv_contents_readable(sample_csv_file):
    """Read the CSV and confirm expected content."""
    with open(sample_csv_file, newline="") as f:
        reader = list(csv.reader(f))
    assert reader[0] == ["name", "height", "weight"]
    assert reader[1][0] == "Alice"
    assert len(reader) == 3
