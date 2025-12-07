from __future__ import annotations
from tkinter import ttk
from typing import Dict, List, Sequence
from sole_solutions.core.session_summary import (
    SessionSummary,
    compute_session_summary,
)


class SessionSummaryPanel(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # --- Left-aligned header/value pairs ---
        rows = [
            ("Frames", "frames"),
            ("Sensors", "sensors"),
            ("Global Min", "gmin"),
            ("Global Max", "gmax"),
            ("Contact Frames", "contact"),
            ("Contact Threshold", "threshold"),
            ("PTI", "pti"),
            ("Δt (s)", "dt"),
        ]

        self._vals: Dict[str, ttk.Label] = {}

        for r, (label, key) in enumerate(rows):
            ttk.Label(self, text=f"{label}:").grid(
                row=r,
                column=0,
                sticky="w",
                padx=(8, 4),
                pady=4,
            )
            v = ttk.Label(self, text="—", anchor="w")
            # NOTE: sticky="w" so the number hugs the label, not the far right
            v.grid(
                row=r,
                column=1,
                sticky="w",
                padx=(0, 8),
                pady=4,
            )
            self._vals[key] = v

        r = len(rows)

        # --- Avg pressure table ---
        ttk.Label(self, text="Avg Pressure (first 100 frames):").grid(
            row=r,
            column=0,
            columnspan=2,
            sticky="w",
            padx=8,
            pady=(12, 4),
        )
        self.avg_tree = ttk.Treeview(
            self,
            columns=("avg",),
            show="headings",
            height=8,
        )
        self.avg_tree.heading("avg", text="Avg Pressure")
        self.avg_tree.column("avg", anchor="center", stretch=True)
        self.avg_tree.grid(
            row=r + 1,
            column=0,
            columnspan=2,
            sticky="nsew",
            padx=8,
            pady=4,
        )

        # --- vGRF table ---
        ttk.Label(self, text="Estimated vGRF (first 100 frames):").grid(
            row=r + 2,
            column=0,
            columnspan=2,
            sticky="w",
            padx=8,
            pady=(12, 4),
        )
        self.vgrf_tree = ttk.Treeview(
            self,
            columns=("vgrf",),
            show="headings",
            height=8,
        )
        self.vgrf_tree.heading("vgrf", text="Sum of Sensors")
        self.vgrf_tree.column("vgrf", anchor="center", stretch=True)
        self.vgrf_tree.grid(
            row=r + 3,
            column=0,
            columnspan=2,
            sticky="nsew",
            padx=8,
            pady=4,
        )

        # Layout: let the tables expand, but keep the header/value pair tight
        self.grid_columnconfigure(0, weight=0)   # label column
        self.grid_columnconfigure(1, weight=0)   # value column (no stretching)
        self.grid_rowconfigure(r + 1, weight=1)  # avg_tree row
        self.grid_rowconfigure(r + 3, weight=1)  # vgrf_tree row

    def load(
        self,
        data_storage: List[Dict[str, object]],
        sensor_keys: Sequence[str],
        contact_threshold: float = 20.0,
        dt: float = 1.0,
    ) -> None:
        s: SessionSummary = compute_session_summary(
            data_storage=data_storage,
            sensor_keys=sensor_keys,
            contact_threshold=contact_threshold,
            dt=dt,
        )

        # Update header/value labels
        self._vals["frames"].configure(text=str(s.frames))
        self._vals["sensors"].configure(text=str(s.sensors))
        self._vals["gmin"].configure(text=f"{s.global_min:.2f}")
        self._vals["gmax"].configure(text=f"{s.global_max:.2f}")
        self._vals["contact"].configure(text=str(s.contact_time_frames))
        self._vals["threshold"].configure(text=f"{s.contact_threshold:.2f}")
        self._vals["pti"].configure(text=f"{s.pti:.2f}")
        self._vals["dt"].configure(text=f"{s.dt:.3f}")

        # Clear tables
        for tree in (self.avg_tree, self.vgrf_tree):
            for iid in tree.get_children():
                tree.delete(iid)

        # Fill avg pressure (first 100 frames)
        for v in s.avg_pressure_per_frame[:100]:
            self.avg_tree.insert("", "end", values=(f"{v:.2f}",))

        # Fill estimated vGRF (sum of sensors) (first 100 frames)
        for v in s.estimated_vgrf_per_frame[:100]:
            self.vgrf_tree.insert("", "end", values=(f"{v:.2f}",))
