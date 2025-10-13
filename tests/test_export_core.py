import csv
import matplotlib.pyplot as plt
from sole_solutions.core.export import write_table_csv, save_plot_png

def test_write_table_csv(tmp_path):
    """Verify that table data writes correctly to CSV."""
    out = tmp_path / "table.csv"
    cols = ["A", "B"]
    rows = [{"A": 1, "B": 2}, {"A": 3, "B": 4}]
    write_table_csv(str(out), cols, rows)

    with open(out, newline="", encoding="utf-8") as f:
        r = list(csv.reader(f))
    assert r == [["A", "B"], ["1", "2"], ["3", "4"]]

def test_save_plot_png(tmp_path):
    """Ensure matplotlib figures save successfully as PNG."""
    out = tmp_path / "fig.png"
    fig, ax = plt.subplots(figsize=(3, 2))
    ax.plot([0, 1, 2], [1, 2, 3])
    save_plot_png(fig, str(out))
    assert out.exists()
    assert out.stat().st_size > 1000
