import io
import tempfile
from sole_solutions.csv_processing import CSVProcessor


def write_temp_csv(content: str):
    tf = tempfile.NamedTemporaryFile(mode="w+", delete=False, newline="", encoding="utf-8")
    tf.write(content)
    tf.flush()
    tf.close()
    return tf.name


def test_peak_computation_basic():
    csv_text = """Sensor,Peak Pressure (kPa),Other
A,10.5,x
B,5.0,y
A,12.0,z
B,7.25,w
"""
    path = write_temp_csv(csv_text)

    p = CSVProcessor()
    p.load(path)
    peaks = p.peak_pressure_per_sensor()

    assert peaks["A"] == 12.0
    assert peaks["B"] == 7.25


def test_non_numeric_and_missing_values_are_skipped():
    csv_text = """Sensor,Peak Pressure (kPa)
A,9.0
B,not_a_number
C,
D,15
D,14.5
"""
    path = write_temp_csv(csv_text)

    p = CSVProcessor.from_file(path)
    peaks = p.peak_pressure_per_sensor()

    assert peaks.get("A") == 9.0
    # B is non-numeric so should not appear
    assert "B" not in peaks
    # C has empty peak -> skipped
    assert "C" not in peaks
    # D should be 15 (the max)
    assert peaks.get("D") == 15.0
