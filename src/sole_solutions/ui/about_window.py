from __future__ import annotations
from tkinter import ttk
import tkinter as tk
import webbrowser
import os


class AboutWindow(ttk.Frame):

    def __init__(self, master, **kwargs):
        super().__init__(master, padding=25, **kwargs)

        master.title("About — Sole Solutions")
        master.resizable(False, False)

        # --- Main container (centers everything visually) ---
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        # --- Title ---
        ttk.Label(
            container,
            text="Sole Solutions: Data Visualizer",
            font=("Arial", 16, "bold"),
            anchor="center",
            justify="center"
        ).pack(pady=(0, 15))

        # --- Description text (CENTERED) ---
        desc = (
            "Version 1.0.0\n"
            "Developed for BSU CS 481\n\n"
            "This app was created for a\n"
            "Boise State University\n"
            "Computer Science Senior Design Project by:\n\n"
            "Nathan Rings\n"
            "John Halpin\n"
            "Chase Davis\n"
            "Ryan Macfarlane\n\n"
            "This application provides:\n"
            "• CSV import and data inspection\n"
            "• Plantar pressure visualization\n"
            "• Left/Right insole comparison\n"
            "• Session summary metrics\n"
            "• Exporting: CSV, PNG, DOCX, PDF"
        )

        ttk.Label(
            container,
            text=desc,
            justify="center",
            anchor="center",
        ).pack(pady=(0, 20))

        # --- Sponsorship info + clickable link (CENTERED) ---
        url = (
            "https://www.boisestate.edu/coen-cs/community/"
            "cs481-senior-design-project/"
        )

        sponsor_text = (
            "For information about sponsoring a project go to\n"
            f"{url}"
        )

        sponsor_label = ttk.Label(
            container,
            text=sponsor_text,
            justify="center",
            anchor="center",
            foreground="blue",
            cursor="hand2",
            font=("Arial", 10)
        )
        sponsor_label.pack(pady=(0, 20))

        def open_url(event):
            webbrowser.open_new(url)

        sponsor_label.bind("<Button-1>", open_url)

        # --- Bottom row: Close button + logo ---
        bottom = ttk.Frame(container)
        bottom.pack(fill="x", pady=(5, 0))

        # Close button
        ttk.Button(bottom, text="Close", command=master.destroy).pack(side="left")

        # --- SDP screenshot logo ---
        logo_path = os.path.join(os.path.dirname(__file__), "sdp-logo.png")

        if os.path.exists(logo_path):
            try:
                logo = tk.PhotoImage(file=logo_path)

                # Auto-resize if large
                max_width = 140
                if logo.width() > max_width:
                    scale = logo.width() // max_width + 1
                    logo = logo.subsample(scale, scale)

                self._logo_image = logo
                ttk.Label(bottom, image=self._logo_image).pack(side="right", padx=5)
            except Exception as e:
                print("Logo failed to load:", e)
        else:
            print("Logo not found at:", logo_path)

        # --- Center window ---
        self.after(10, lambda: self._center(master))


    def _center(self, win):
        win.update_idletasks()
        parent = win.master
        if parent is None:
            return

        x = parent.winfo_rootx() + (parent.winfo_width() - win.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{x}+{y}")
