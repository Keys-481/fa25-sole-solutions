import csv
import os

SAMPLE_CSV = "tests/sample_data/sensor_sample_data.csv"

def test_csv_file_exists():
    """Confirm that the sample CSV exists."""
    assert os.path.exists(SAMPLE_CSV)
    assert SAMPLE_CSV.lower().endswith(".csv")

def test_csv_readable():
    """CSV file can be opened and read."""
    with open(SAMPLE_CSV, newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    # There should be at least one header row + one data row
    assert len(rows) >= 2
    assert "Subject" in rows[0] or "name" in rows[0]  # header check

def test_csv_has_expected_columns():
    """Check that the CSV contains all expected columns."""
    expected_columns = [
        "Subject", "Height_cm", "Weight_kg", "Gender", "Foot_dominance",
        "Trial", "Time", "PeakPressure_Left", "PeakPressure_Right",
        "PTI_Left", "PTI_Right", "ContactArea_Left", "ContactArea_Right",
        "StanceTime_Left", "StanceTime_Right", "StepTime", "StrideTime",
        "Cadence", "vGRF_Left", "vGRF_Right", "Impulse_Left", "Impulse_Right",
        "LoadRate_Left", "LoadRate_Right", "FootstrikeAngle_Left", "FootstrikeAngle_Right",
        "StepLength", "StrideLength", "Balance_CoPSway", "Pressure_Heel",
        "Pressure_Midfoot", "Pressure_Forefoot", "AsymmetryIndex", "TotalSteps", "CumulativeLoad"
    ]
    with open(SAMPLE_CSV, newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
    for col in expected_columns:
        assert col in columns

def test_csv_first_row_data():
    """Validate data types or example values for the first row."""
    with open(SAMPLE_CSV, newline="") as f:
        reader = csv.DictReader(f)
        first_row = next(reader)
    # Example checks
    assert first_row["Subject"].startswith("Subject")
    assert float(first_row["Height_cm"]) > 0
    assert float(first_row["Weight_kg"]) > 0