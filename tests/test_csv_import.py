import os
import csv

SAMPLE_CSV = "tests/sample_data/sensor_sample_data.csv"

def test_csv_file_exists():
    """Confirm that the sample CSV exists."""
    assert os.path.exists(SAMPLE_CSV)
    assert SAMPLE_CSV.lower().endswith(".csv")

def test_csv_readable():
    """CSV file can be opened and read."""
    with open(SAMPLE_CSV, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
    # There should be at least one header row + one data row
    assert len(rows) >= 2
    assert "Frame" in rows[0] or "Sensor" in rows[0]  # header check

def test_csv_has_expected_columns():
    """Check that the CSV contains all expected columns."""
    expected_columns = [
        "Frame", "Date", "Time", "Units", "Threshold", "Note", "Sensor", "Insole",
        "Rows", "Columns", "Avg Pressure (kPa)", "Minimum Pressure (kPa)",
        "Peak Pressure (kPa)", "Contact Area (cm)", "Total Area (cm)",
        "Contact %", "Est. Load (N)", "Std Dev.", "COP Row", "COP Column"
    ] + [str(i) for i in range(1, 342)]  # 1 through 341

    with open(SAMPLE_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames

    # Ensure every expected column exists in the CSV header
    for col in expected_columns:
        assert col in columns, f"Missing expected column: {col}"

def test_csv_first_row_data():
    """Validate data types or example values for the first row."""
    with open(SAMPLE_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        first_row = next(reader)

    # Example checks for key fields
    assert first_row["Frame"].isdigit()
    assert len(first_row["Date"]) > 0
    assert len(first_row["Time"]) > 0
    assert "kPa" in first_row["Units"] or first_row["Units"].strip() != ""
    assert float(first_row["Avg Pressure (kPa)"]) >= 0
    assert float(first_row["Peak Pressure (kPa)"]) >= 0
