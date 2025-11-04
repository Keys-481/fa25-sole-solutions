from __future__ import annotations
import tkinter as tk
from tkinter import ttk


class AboutWindow(ttk.Frame):
   

    def __init__(self, master, **kwargs):
        super().__init__(master, padding=20, **kwargs)

        master.title("About — Sole Solutions")
        master.resizable(False, False)

        # --- Title ---
        ttk.Label(
            self,
            text="Sole Solutions: Data Visualizer",
            font=("Arial", 16, "bold")
        ).pack(pady=(0, 10))

        # --- Description text ---
        desc = (
            "Version 1.0.0\n"
            "Developed for BSU CS 481\n\n"
            "Created by:\n"
            "Nathan Rings\n"
            "John Halpin\n"
            "Chase Davis\n"
            "Ryan Macfarlane\n\n"
            "This application provides:\n"
            "• CSV import and data inspection\n"
            "• Plantar pressure visualization\n"
            "• Left/Right insole comparison\n"
            "• Session summary metrics\n"
            "• Exporting: CSV, PNG, DOCX, PDF\n"
        )

        ttk.Label(self, text=desc, justify="left").pack(pady=(0, 12))

        # --- Close button ---
        ttk.Button(self, text="Close", command=master.destroy).pack()

        # --- Center window over parent (done after idle tasks) ---
        self.after(10, lambda: self._center(master))

    def _center(self, win):
        """Centers this toplevel over its parent window."""
        win.update_idletasks()
        parent = win.master  # the main root
        if parent is None:
            return

        x = parent.winfo_rootx() + (parent.winfo_width() - win.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{x}+{y}")
