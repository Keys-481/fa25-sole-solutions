# Ensures matplotlib uses a headless backend on CI and locally for tests.
import matplotlib
matplotlib.use("Agg")
