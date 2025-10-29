"""CSV processing helpers for Sole Solutions.

This module provides a small CSVProcessor class that reads CSV files
and computes per-sensor peak pressures based on the columns:
 - "Sensor"
 - "Peak Pressure (kPa)"

The implementation uses the standard library so there are no extra
dependencies.
"""
from __future__ import annotations

from typing import Dict, List, Optional
import csv


class CSVProcessor:
    """Load CSV data and compute derived values.

    Usage:
        p = CSVProcessor()
        p.load('data.csv')
        peaks = p.peak_pressure_per_sensor()
    """

    def __init__(self, file_path: Optional[str] = None) -> None:
        self.file_path = file_path
        self.rows: List[Dict[str, str]] = []

    def load(self, file_path: Optional[str] = None, encoding: str = "utf-8") -> None:
        """Load CSV rows into memory as a list of dicts.

        file_path: path to csv file. If omitted, uses the instance's
        `file_path` set at construction.
        """
        path = file_path or self.file_path
        if not path:
            raise ValueError("No file path provided to load()")

        with open(path, newline="", encoding=encoding) as fh:
            reader = csv.DictReader(fh)
            self.rows = [row for row in reader]

    @classmethod
    def from_file(cls, file_path: str, encoding: str = "utf-8") -> "CSVProcessor":
        p = cls(file_path)
        p.load(file_path, encoding=encoding)
        return p

    def peak_pressure_per_sensor(self) -> Dict[str, float]:
        """Return a mapping of sensor -> peak pressure (float).

        Rows missing the required columns or having non-numeric peak
        values are skipped. Comparison uses float(max).
        """
        if not self.rows:
            raise ValueError("No data loaded. Call load() first.")

        peaks: Dict[str, float] = {}
        for row in self.rows:
            sensor = row.get("Sensor")
            peak_str = row.get("Peak Pressure (kPa)")
            if sensor is None or peak_str is None:
                # skip rows that don't have expected columns
                continue
            peak_str = peak_str.strip()
            if peak_str == "":
                continue
            try:
                val = float(peak_str)
            except (ValueError, TypeError):
                # skip non-numeric values
                continue

            prev = peaks.get(sensor)
            if prev is None or val > prev:
                peaks[sensor] = val

        return peaks


__all__ = ["CSVProcessor"]
