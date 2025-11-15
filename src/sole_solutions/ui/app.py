from sole_solutions.core.export_manager import (
    export_summary_docx, export_summary_pdf, export_per_frame_csv
)
from sole_solutions.core.session_summary import infer_sensor_keys, compute_session_summary
from sole_solutions.core.export import write_table_csv, save_plot_png

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import csv
import os
import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import re
import statistics
from sole_solutions.ui.session_summary_panel import SessionSummaryPanel
from sole_solutions.ui.about_window import AboutWindow
from typing import Dict
from sole_solutions.core.calculations import (
    CalcParams,
    extract_per_frame_pressures,
    compute_per_frame_bundle,
    detect_stance_windows,
    temporal_spatial_from_spans,
    compute_impulse_Ns,
    compute_load_rate,
)

# Drag & drop (graceful fallback if tkinterdnd2 is not present)
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except Exception:
    TkinterDnD = tk  # fallback to standard Tk
    DND_FILES = None
    DND_AVAILABLE = False


class Collapsible(ttk.Frame):
    """Collapsible section that preserves vertical layout order."""
    def __init__(self, master, title: str, *args, initially_open=True, **kwargs):
        super().__init__(master, *args, **kwargs)
        self._open = initially_open
        self._header = ttk.Frame(self)
        self._header.pack(fill="x", pady=(0, 2))
        self._indicator = ttk.Label(self._header, text="▼" if self._open else "▶", width=2)
        self._indicator.pack(side="left")
        self._title_lbl = ttk.Label(self._header, text=title)
        self._title_lbl.pack(side="left")

        self._body = ttk.Frame(self)
        if self._open:
            self._body.pack(fill="x")

        self._header.bind("<Button-1>", self._toggle)
        self._indicator.bind("<Button-1>", self._toggle)
        self._title_lbl.bind("<Button-1>", self._toggle)

    def _toggle(self, *_):
        self.set_open(not self._open)

    def set_open(self, open_: bool):
        if self._open == open_:
            return
        self._open = open_
        self._indicator.configure(text="▼" if self._open else "▶")
        if self._open:
            self._body.pack(fill="x")
        else:
            self._body.forget()

    @property
    def body(self):
        return self._body

    def is_open(self):
        return self._open


def run_ui():
    # Root window
    root = TkinterDnD.Tk() if DND_AVAILABLE else tk.Tk()
    root.title("Sole Solutions: Data Visualizer")
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    default_w = min(1400, max(1100, screen_w - 140))
    default_h = min(850,  max(650,  screen_h - 160))
    root.geometry(f"{default_w}x{default_h}")
    root.minsize(1100, 650)
    root.configure(bg="#f2f2f2")

    # ---------- Styles ----------
    style = ttk.Style()
    if "clam" in style.theme_names():
        style.theme_use("clam")
    style.configure("TNotebook.Tab", padding=(14, 8))
    style.configure("Header.TLabel", font=("Arial", 16, "bold"))
    style.configure("Hint.TLabel", foreground="#5b6670")
    style.configure("Import.TFrame", background="#eef7ff")

    # ---------- State ----------
    data_storage: list[dict] = []
    selected_zones: set[str] = set()
    metadata = {
        "height_ft": 0,
        "height_in": 0,
        "height_cm": 0.0,
        "weight_lb": 0,
        "gender": "Male",
        "dominance": "Left",
        "zones": selected_zones,
    }
    current_file: str | None = None
    ROWS_PER_PAGE = 100
    current_page = 0
    display_columns: list[str] = []

    # Export/summary state
    last_summary = None
    last_base_name = "export"

    # Responsive flags
    compact_mode = False  # tightened paddings/images, no re-ordering

    def _recalc_height_cm():
        total_in = metadata["height_ft"] * 12 + metadata["height_in"]
        metadata["height_cm"] = round(total_in * 2.54, 1)

    # ---------- Header ----------
    header = ttk.Frame(root)
    header.pack(fill="x", padx=16, pady=(12, 0))
    ttk.Label(header, text="Sole Solutions: Data Visualizer", style="Header.TLabel").pack(side="left")

    status_var = tk.StringVar(value="Ready")
    ttk.Label(header, textvariable=status_var, style="Hint.TLabel").pack(side="right", padx=(8, 0))

    # ---- Export selection dialog ----
    def choose_exports(has_summary: bool):
        win = tk.Toplevel(root)
        win.title("Export Options")
        win.transient(root)
        win.grab_set()
        win.resizable(False, False)

        frm = ttk.Frame(win, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Select files to export:", font=("Arial", 11, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        v_table = tk.BooleanVar(value=True)
        v_plot  = tk.BooleanVar(value=True)
        v_pf    = tk.BooleanVar(value=has_summary)
        v_docx  = tk.BooleanVar(value=False)
        v_pdf   = tk.BooleanVar(value=False)

        ttk.Checkbutton(frm, text="Table CSV", variable=v_table).grid(row=1, column=0, sticky="w")
        ttk.Checkbutton(frm, text="Plot PNG", variable=v_plot).grid(row=2, column=0, sticky="w")
        cb_pf  = ttk.Checkbutton(frm, text="Per-frame CSV (avg pressure & vGRF)", variable=v_pf)
        cb_doc = ttk.Checkbutton(frm, text="DOCX Report", variable=v_docx)
        cb_pdf = ttk.Checkbutton(frm, text="PDF Report", variable=v_pdf)
        cb_pf.grid(row=3, column=0, sticky="w")
        cb_doc.grid(row=4, column=0, sticky="w")
        cb_pdf.grid(row=5, column=0, sticky="w")

        if not has_summary:
            cb_pf.state(["disabled"])
            cb_doc.state(["disabled"])
            cb_pdf.state(["disabled"])

        btns = ttk.Frame(frm)
        btns.grid(row=6, column=0, sticky="e", pady=(10, 0))
        choice = {"ok": False}

        ttk.Button(btns, text="Cancel", command=lambda: win.destroy()).pack(side="right", padx=(0, 6))
        ttk.Button(btns, text="Export", command=lambda: (choice.update(ok=True), win.destroy())).pack(side="right")

        win.update_idletasks()
        x = root.winfo_rootx() + (root.winfo_width() - win.winfo_width()) // 2
        y = root.winfo_rooty() + (root.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{x}+{y}")
        root.wait_window(win)
        if not choice["ok"]:
            return None
        return {
            "table": v_table.get(),
            "plot":  v_plot.get(),
            "per_frame": v_pf.get() and has_summary,
            "docx": v_docx.get() and has_summary,
            "pdf":  v_pdf.get() and has_summary,
        }

    def do_export():
        if not tree.get_children() and not last_summary:
            messagebox.showwarning("Nothing to Export", "No data to export yet.")
            return

        choices = choose_exports(has_summary=bool(last_summary))
        if choices is None or not any(choices.values()):
            if choices is not None:
                messagebox.showinfo("No Selection", "No export options selected.")
            return

        export_dir = filedialog.askdirectory(title="Select export folder")
        if not export_dir:
            return

        base = (last_base_name if last_summary else (current_file or "export")).replace(" ", "_")
        saved_paths = []

        if choices["table"]:
            if not tree.get_children():
                messagebox.showwarning("Skip Table CSV", "No table rows to export.")
            else:
                try:
                    cols = list(tree["columns"])
                    table_rows = []
                    for iid in tree.get_children():
                        values = tree.item(iid, "values")
                        table_rows.append({col: values[idx] if idx < len(values) else "" for idx, col in enumerate(cols)})
                    csv_path = os.path.join(export_dir, f"{base}_table.csv")
                    write_table_csv(csv_path, cols, table_rows)
                    saved_paths.append(csv_path)
                except Exception as e:
                    messagebox.showwarning("Export Warning", f"Table CSV failed: {e}")

        if choices["plot"]:
            try:
                png_path = os.path.join(export_dir, f"{base}_plot.png")
                save_plot_png(fig, png_path, dpi=150)
                saved_paths.append(png_path)
            except Exception as e:
                messagebox.showwarning("Export Warning", f"Plot PNG failed: {e}")

        if last_summary:
            if choices["per_frame"]:
                try:
                    per_frame_path = os.path.join(export_dir, f"{base}_per_frame_summary.csv")
                    err = export_per_frame_csv(
                        per_frame_path,
                        last_summary.get("avg_pressure_per_frame", []),
                        last_summary.get("estimated_vgrf_per_frame", [])
                    )
                    if err:
                        messagebox.showwarning("Export Warning", err)
                    else:
                        saved_paths.append(per_frame_path)
                except Exception as e:
                    messagebox.showwarning("Export Warning", f"Per-frame CSV failed: {e}")

            if choices["docx"]:
                try:
                    docx_path = os.path.join(export_dir, f"{base}_report.docx")
                    err = export_summary_docx(last_summary, docx_path)
                    if err:
                        messagebox.showwarning("Export Warning", err)
                    else:
                        saved_paths.append(docx_path)
                except Exception as e:
                    messagebox.showwarning("Export Warning", f"DOCX export failed: {e}")

            if choices["pdf"]:
                try:
                    pdf_path = os.path.join(export_dir, f"{base}_report.pdf")
                    err = export_summary_pdf(last_summary, pdf_path)
                    if err:
                        messagebox.showwarning("Export Warning", err)
                    else:
                        saved_paths.append(pdf_path)
                except Exception as e:
                    messagebox.showwarning("Export Warning", f"PDF export failed: {e}")

        if saved_paths:
            status_var.set(f"Exported {len(saved_paths)} file(s) to {export_dir}")
            messagebox.showinfo("Export Complete", "Saved:\n- " + "\n- ".join(saved_paths))
        else:
            messagebox.showinfo("Nothing Saved", "No files were created.")

    ttk.Button(header, text="Export…", command=do_export).pack(side="right")

    def open_about():
        win = tk.Toplevel(root)
        AboutWindow(win).pack(fill="both", expand=True)

    ttk.Button(header, text="About", command=open_about).pack(side="right", padx=(0, 10))

    # ---------- Notebook ----------
    nb = ttk.Notebook(root)
    nb.pack(fill="both", expand=True, padx=16, pady=16)

    tab_table = ttk.Frame(nb)
    tab_visual = ttk.Frame(nb)
    nb.add(tab_table, text="Data Table")
    nb.add(tab_visual, text="Visualization")

    tab_summary = ttk.Frame(nb)
    nb.add(tab_summary, text="Session Summary")
    summary_panel = SessionSummaryPanel(tab_summary)
    summary_panel.pack(fill="both", expand=True)

    # =========================================================
    # ==================== Data Table tab =====================
    # =========================================================
    tab_table.columnconfigure(0, weight=0)  # left fixed-ish width
    tab_table.columnconfigure(1, weight=1)  # right grows
    tab_table.rowconfigure(0, weight=1)

    # ---- Left column ----
    left_col = tk.Frame(tab_table, bg="#f2f2f2", width=360)
    left_col.grid(row=0, column=0, sticky="nsw", padx=20, pady=20)
    left_col.grid_propagate(False)
    left_col.columnconfigure(0, weight=1)

    # 1) Import card
    import_container = ttk.Frame(left_col, style="Import.TFrame")
    import_container.grid(row=0, column=0, sticky="ew", pady=(0, 10))
    import_hint = ttk.Label(
        import_container,
        text="Import CSV (click)\n—or—\nDrag & Drop a CSV",
        anchor="center",
        style="Hint.TLabel",
        justify="center",
    )
    import_hint.pack(fill="x", padx=10, pady=12)

    def import_click(_event=None):
        import_csv()

    import_container.bind("<Button-1>", import_click)
    import_hint.bind("<Button-1>", import_click)

    if DND_AVAILABLE and DND_FILES:
        import_container.drop_target_register(DND_FILES)

        def drop_handler(event):
            files = root.splitlist(event.data)
            if files:
                import_csv(files[0])

        import_container.dnd_bind("<<Drop>>", drop_handler)

    # 2) Collapsible: Participant Info
    info_section = Collapsible(left_col, "Participant Info", initially_open=True)
    info_section.grid(row=1, column=0, sticky="ew", pady=6)
    info_frame = tk.Frame(info_section.body, bg="#ffffff")
    info_frame.pack(fill="x", padx=10, pady=10)

    def _only_int(P):
        return P == "" or P.isdigit()
    vcmd = (root.register(_only_int), "%P")

    tk.Label(info_frame, text="Height:", bg="#ffffff").grid(row=0, column=0, sticky="w", pady=(2, 2))
    tk.Label(info_frame, text="ft", bg="#ffffff").grid(row=0, column=2, sticky="w")
    tk.Label(info_frame, text="in", bg="#ffffff").grid(row=0, column=4, sticky="w")
    height_ft_var = tk.StringVar(value=str(metadata["height_ft"]))
    height_in_var = tk.StringVar(value=str(metadata["height_in"]))
    height_ft_entry = ttk.Entry(info_frame, textvariable=height_ft_var, width=4, validate="key", validatecommand=vcmd)
    height_in_entry = ttk.Entry(info_frame, textvariable=height_in_var, width=4, validate="key", validatecommand=vcmd)
    height_ft_entry.grid(row=0, column=1, sticky="w", padx=(6, 6))
    height_in_entry.grid(row=0, column=3, sticky="w", padx=(6, 6))

    tk.Label(info_frame, text="Weight:", bg="#ffffff").grid(row=1, column=0, sticky="w", pady=(6, 2))
    tk.Label(info_frame, text="lb", bg="#ffffff").grid(row=1, column=2, sticky="w")
    weight_lb_var = tk.StringVar(value=str(metadata["weight_lb"]))
    weight_lb_entry = ttk.Entry(info_frame, textvariable=weight_lb_var, width=6, validate="key", validatecommand=vcmd)
    # FIX: was "column-1 if False else 1" causing a SyntaxError; should just be column=1
    weight_lb_entry.grid(row=1, column=1, sticky="w", padx=(6, 6))

    def _commit_height(_evt=None):
        ft = int(height_ft_var.get()) if height_ft_var.get().isdigit() else metadata["height_ft"]
        inch = int(height_in_var.get()) if height_in_var.get().isdigit() else metadata["height_in"]
        ft = max(3, min(ft, 8))
        inch = max(0, min(inch, 11))
        metadata["height_ft"] = ft
        metadata["height_in"] = inch
        height_ft_var.set(str(ft))
        height_in_var.set(str(inch))
        _recalc_height_cm()
        refresh_info_labels()

    def _commit_weight(_evt=None):
        lb = int(weight_lb_var.get()) if weight_lb_var.get().isdigit() else metadata["weight_lb"]
        lb = max(60, min(lb, 350))
        metadata["weight_lb"] = lb
        weight_lb_var.set(str(lb))
        refresh_info_labels()

    for w in (height_ft_entry, height_in_entry):
        w.bind("<FocusOut>", _commit_height)
        w.bind("<Return>", _commit_height)
    weight_lb_entry.bind("<FocusOut>", _commit_weight)
    weight_lb_entry.bind("<Return>", _commit_weight)

    tk.Label(info_frame, text="Gender:", bg="#ffffff").grid(row=2, column=0, sticky="w", pady=(8, 0))
    gender_combo = ttk.Combobox(info_frame, values=["Male", "Female", "Unspecified"], state="readonly", width=16)
    gender_combo.grid(row=2, column=1, sticky="w", pady=(8, 0))
    gender_combo.current(0)
    gender_combo.bind("<<ComboboxSelected>>", lambda *_: metadata.__setitem__("gender", gender_combo.get()))

    tk.Label(info_frame, text="Foot Dominance:", bg="#ffffff").grid(row=3, column=0, sticky="w", pady=(6, 0))
    dominance_combo = ttk.Combobox(info_frame, values=["Left", "Right", "Both"], state="readonly", width=16)
    dominance_combo.grid(row=3, column=1, sticky="w", pady=(6, 0))
    dominance_combo.current(0)
    dominance_combo.bind("<<ComboboxSelected>>", lambda *_: metadata.__setitem__("dominance", dominance_combo.get()))

    # 3) Collapsible: Column Options
    colopts_section = Collapsible(left_col, "Column Options", initially_open=True)
    colopts_section.grid(row=2, column=0, sticky="ew", pady=6)
    colopts_frame = tk.Frame(colopts_section.body, bg="#ffffff")
    colopts_frame.pack(fill="x", padx=10, pady=10)
    tk.Label(colopts_frame, text="Select Column:", bg="#ffffff").grid(row=0, column=0, sticky="w")
    column_combo = ttk.Combobox(colopts_frame, values=[], state="readonly", width=20)
    column_combo.grid(row=0, column=1, sticky="ew", padx=(6, 0))
    column_combo.set("All")

    # 4) Collapsible: Filters
    filter_section = Collapsible(left_col, "Filters", initially_open=True)
    filter_section.grid(row=3, column=0, sticky="ew", pady=6)
    filter_frame = tk.Frame(filter_section.body, bg="#ffffff")
    filter_frame.pack(fill="x", padx=10, pady=10)
    tk.Label(filter_frame, text="Select Subject:", bg="#ffffff").grid(row=0, column=0, sticky="w")
    subject_combo = ttk.Combobox(filter_frame, values=[], state="readonly")
    subject_combo.grid(row=0, column=1, sticky="ew")
    tk.Label(filter_frame, text="Select Trial:", bg="#ffffff").grid(row=1, column=0, sticky="w")
    trial_combo = ttk.Combobox(filter_frame, values=[], state="readonly")
    trial_combo.grid(row=1, column=1, sticky="ew")

    # 5) Insole Zones (always shown)
    zones_holder = ttk.LabelFrame(left_col, text="Insole Zones (3×2)")
    zones_holder.grid(row=4, column=0, sticky="ew", pady=6)
    zones_frame = tk.Frame(zones_holder, bg="#ffffff")
    zones_frame.pack(fill="x", padx=10, pady=10)

    # images (optionally subsampled in compact mode)
    img_dir = os.path.join(os.path.dirname(__file__), "images")
    base_bottom_left  = tk.PhotoImage(file=os.path.join(img_dir, "bottomleft.png"))
    base_bottom_right = tk.PhotoImage(file=os.path.join(img_dir, "bottomright.png"))
    base_middle_left  = tk.PhotoImage(file=os.path.join(img_dir, "middleleft.png"))
    base_middle_right = tk.PhotoImage(file=os.path.join(img_dir, "middleright.png"))
    base_top_left     = tk.PhotoImage(file=os.path.join(img_dir, "topleft.png"))
    base_top_right    = tk.PhotoImage(file=os.path.join(img_dir, "topright.png"))

    current_top_left     = base_top_left
    current_top_right    = base_top_right
    current_middle_left  = base_middle_left
    current_middle_right = base_middle_right
    current_bottom_left  = base_bottom_left
    current_bottom_right = base_bottom_right

    zone_canvas = tk.Canvas(zones_frame, width=150, height=200, bg="#ffffff", highlightthickness=1, relief="ridge")
    zone_canvas.pack()

    zone_labels = [
        ["FF\nMedial",  "FF\nLateral"],
        ["MF\nMedial",  "MF\nLateral"],
        ["Heel\nMedial","Heel\nLateral"]
    ]
    zone_keys = [
        ["FF-Medial",  "FF-Lateral"],
        ["MF-Medial",  "MF-Lateral"],
        ["Heel-Medial","Heel-Lateral"]
    ]
    rect_ids: dict[int, str] = {}

    def _zone_images():
        return [
            [current_top_left,    current_top_right],
            [current_middle_left, current_middle_right],
            [current_bottom_left, current_bottom_right],
        ]

    def draw_zone_grid():
        zone_canvas.delete("all")
        w = int(zone_canvas["width"])
        h = int(zone_canvas["height"])
        cols, rows = 2, 3
        cw, ch = w / cols, h / rows
        imgs = _zone_images()
        for r in range(rows):
            for c in range(cols):
                key = zone_keys[r][c]
                x0, y0 = c * cw, r * ch
                x1, y1 = x0 + cw, y0 + ch
                is_sel = key in selected_zones
                fill = "#46c081" if is_sel else "#ffffff"
                outline = "#2c7a57" if is_sel else "#9aa3ab"
                rid = zone_canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline=outline, width=2)
                rect_ids[rid] = key
                zone_canvas.create_image((x0+x1)/2, (y0+y1)/2, image=imgs[r][c], anchor="center")
                zone_canvas.create_text((x0+x1)/2, (y0+y1)/2, text=zone_labels[r][c], font=("Arial", 9 if compact_mode else 10))
        zone_canvas.create_rectangle(1, 1, w-1, h-1, outline="#9aa3ab", width=1)

    def toggle_zone(event):
        item = zone_canvas.find_closest(event.x, event.y)
        if not item:
            return
        rid = item[0]
        if rid not in rect_ids:
            for cand in zone_canvas.find_overlapping(event.x, event.y, event.x, event.y):
                if cand in rect_ids:
                    rid = cand
                    break
        key = rect_ids.get(rid)
        if not key:
            return
        if key in selected_zones:
            selected_zones.remove(key)
        else:
            selected_zones.add(key)
        metadata["zones"] = selected_zones
        draw_zone_grid()
        sel_var.set("Selected: " + (", ".join(sorted(selected_zones)) if selected_zones else "None"))
        _update_status_peek()

    zone_canvas.bind("<Button-1>", toggle_zone)
    sel_var = tk.StringVar(value="Selected: None")
    ttk.Label(zones_frame, textvariable=sel_var, style="Hint.TLabel").pack(anchor="w", padx=4, pady=(4, 0))

    # ---- Right column (table) ----
    right_frame = tk.Frame(tab_table, bg="#f2f2f2")
    right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
    right_frame.columnconfigure(0, weight=1)

    table_frame = tk.Frame(right_frame, bg="#ffffff", relief="groove", bd=2)
    table_frame.grid(row=0, column=0, sticky="ew")
    tree = ttk.Treeview(table_frame, show="headings", height=12)
    tree.grid(row=0, column=0, sticky="nsew")
    v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    v_scrollbar.grid(row=0, column=1, sticky="ns")
    tree.configure(yscrollcommand=v_scrollbar.set)
    h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
    h_scrollbar.grid(row=1, column=0, sticky="ew")
    tree.configure(xscrollcommand=h_scrollbar.set)
    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)

    pagination_frame = tk.Frame(right_frame, bg="#f2f2f2")
    pagination_frame.grid(row=1, column=0, sticky="ew", pady=(8, 0))
    prev_btn = ttk.Button(pagination_frame, text="Previous")
    prev_btn.pack(side="left", padx=5)
    next_btn = ttk.Button(pagination_frame, text="Next")
    next_btn.pack(side="left", padx=5)
    page_label = tk.Label(pagination_frame, text="Page 0 of 0", bg="#f2f2f2")
    page_label.pack(side="right")

    # =========================================================
    # ================== Visualization tab ====================
    # =========================================================
    viz_container = tk.Frame(tab_visual, bg="#f2f2f2")
    viz_container.pack(fill="both", expand=True, padx=20, pady=20)

    range_frame = tk.Frame(viz_container, bg="#f2f2f2")
    range_frame.pack(fill="x", pady=(0, 10))

    metric_frame = tk.Frame(viz_container, bg="#f2f2f2")
    metric_frame.pack(fill="x", pady=(0, 10))

    tk.Label(metric_frame, text="Select Metric:", bg="#f2f2f2").pack(side="left", padx=(4, 4))
    metric_var = tk.StringVar(value="Peak Pressure")
    metric_combo = ttk.Combobox(
        metric_frame,
        textvariable=metric_var,
        state="readonly",
        values=["Peak Pressure", "Minimum Pressure", "Contact Area", "Avg Pressure", "Contact %", "Estimated Load"],
        width=20
    )
    metric_combo.pack(side="left", padx=(4, 6))
    metric_combo.bind("<<ComboboxSelected>>", lambda *_: update_plot())

    foot_toggle_frame = tk.Frame(viz_container, bg="#f2f2f2")
    foot_toggle_frame.pack(fill="x", pady=(0, 10))

    show_left_var = tk.BooleanVar(value=True)
    show_right_var = tk.BooleanVar(value=True)

    left_check = ttk.Checkbutton(
        foot_toggle_frame, text="Show Left Foot", variable=show_left_var,
        command=lambda: update_plot()
    )
    right_check = ttk.Checkbutton(
        foot_toggle_frame, text="Show Right Foot", variable=show_right_var,
        command=lambda: update_plot()
    )
    left_check.pack(side="left", padx=6)
    right_check.pack(side="left", padx=6)

    tk.Label(range_frame, text="Frame Range:", bg="#f2f2f2").pack(side="left", padx=(4, 4))
    frame_start_var = tk.StringVar(value="0")
    frame_end_var = tk.StringVar(value="")
    ttk.Entry(range_frame, textvariable=frame_start_var, width=8).pack(side="left")
    tk.Label(range_frame, text="to", bg="#f2f2f2").pack(side="left", padx=4)
    ttk.Entry(range_frame, textvariable=frame_end_var, width=8).pack(side="left", padx=(0, 6))
    ttk.Button(range_frame, text="Apply", command=lambda: update_plot()).pack(side="left", padx=4)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.set_facecolor("white")
    fig.patch.set_facecolor("#f2f2f2")
    canvas = FigureCanvasTkAgg(fig, master=viz_container)
    canvas.get_tk_widget().pack(fill="both", expand=True)

    # =========================================================
    # ====================== Calculations =====================
    # =========================================================
    tab_calc = ttk.Frame(nb)
    nb.add(tab_calc, text="Calculations")

    tab_calc.columnconfigure(0, weight=0)
    tab_calc.columnconfigure(1, weight=1)
    tab_calc.rowconfigure(0, weight=1)

    calc_left = tk.Frame(tab_calc, bg="#f2f2f2")
    calc_left.grid(row=0, column=0, sticky="nsw", padx=20, pady=20)
    calc_right = tk.Frame(tab_calc, bg="#f2f2f2")
    calc_right.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
    calc_right.columnconfigure(0, weight=1)

    ctrl = ttk.LabelFrame(calc_left, text="Live Parameters", padding=10)
    ctrl.pack(fill="x")
    fs_var = tk.DoubleVar(value=1.0)
    area_var = tk.DoubleVar(value=0.25)
    thr_var = tk.DoubleVar(value=20.0)
    bw_thr_var = tk.DoubleVar(value=0.05)
    mass_var = tk.DoubleVar(value=75.0)
    cal_var = tk.DoubleVar(value=1.0)
    smooth_var = tk.IntVar(value=3)

    def _row(parent, r, label, var, width=8):
        ttk.Label(parent, text=label).grid(row=r, column=0, sticky="w", pady=2)
        e = ttk.Entry(parent, textvariable=var, width=width)
        e.grid(row=r, column=1, sticky="w", pady=2)
        return e

    _row(ctrl, 0, "Sampling rate (Hz)", fs_var)
    _row(ctrl, 1, "Sensel area (cm²)", area_var)
    _row(ctrl, 2, "Contact thr (kPa)", thr_var)
    _row(ctrl, 3, "Stance thr (BW frac)", bw_thr_var)
    _row(ctrl, 4, "Body mass (kg)", mass_var)
    _row(ctrl, 5, "Calibration scale", cal_var)
    _row(ctrl, 6, "Smooth window (frames)", smooth_var)
    ttk.Button(ctrl, text="Recompute", command=lambda: refresh_calc()).grid(row=7, column=0, columnspan=2, pady=(8, 0))

    peak_matrix: Dict[tuple[int, int], Dict[str, float]] = {}

    # ---- Frame Range Selection ----
    frame_range_label = ttk.LabelFrame(calc_left, text="Peak Matrix Frame Range", padding=10)
    frame_range_label.pack(fill="x", pady=(10, 6))
    
    peak_start_var = tk.StringVar(value="0")
    peak_end_var = tk.StringVar(value="100")
    
    ttk.Label(frame_range_label, text="Start Frame:").grid(row=0, column=0, sticky="w", padx=(0, 6))
    ttk.Entry(frame_range_label, textvariable=peak_start_var, width=10).grid(row=0, column=1, sticky="w", padx=(0, 12))
    ttk.Label(frame_range_label, text="End Frame:").grid(row=0, column=2, sticky="w", padx=(0, 6))
    ttk.Entry(frame_range_label, textvariable=peak_end_var, width=10).grid(row=0, column=3, sticky="w")

    # ---- Sensor Peaks Frame Range ----
    def peak_pressure_frame_range(rows: list[dict], start_frame: int, end_frame: int) -> Dict[str, float]:
        if not rows:
            return {}
        peaks: Dict[str, float] = {}
        for r in rows[start_frame:end_frame]:
            sensor = r.get("Sensor")
            peak_str = r.get("Peak Pressure (kPa)")
            if sensor is None or peak_str is None:
                continue
            peak_str = str(peak_str).strip()
            if peak_str == "":
                continue
            try:
                val = float(peak_str)
            except (ValueError, TypeError):
                continue
            prev = peaks.get(sensor)
            if prev is None or val > prev:
                peaks[sensor] = val
        return peaks

    def calculate_and_store_peaks():
        try:
            start = int(peak_start_var.get())
            end = int(peak_end_var.get())
            if start < 0 or end <= start:
                messagebox.showwarning("Invalid Range", "End frame must be greater than start frame, and both must be >= 0.")
                return
            if not data_storage:
                messagebox.showwarning("No Data", "Load a CSV first.")
                return
            peaks = peak_pressure_frame_range(data_storage, start, end)
            peak_matrix[(start, end)] = peaks
            status_var.set(f"Stored peak matrix for frames {start}-{end}")
            display_peak_matrix()
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter valid integer values for frame range.")

    ttk.Button(frame_range_label, text="Calculate & Store", command=calculate_and_store_peaks).grid(row=1, column=0, columnspan=4, sticky="ew", pady=(8, 0))

    # ---- Peak Matrix Display ----
    matrix_frame = ttk.LabelFrame(calc_left, text="Peak Matrix Results", padding=(8, 6))
    matrix_frame.pack(fill="both", expand=True, pady=(6, 8))
    matrix_frame.columnconfigure(0, weight=1)
    matrix_frame.rowconfigure(0, weight=1)
    
    matrix_text = tk.Text(matrix_frame, wrap="none", state="disabled", height=8, width=1, font=("Courier", 9))
    matrix_text.grid(row=0, column=0, sticky="nsew")
    matrix_scroll = ttk.Scrollbar(matrix_frame, orient="vertical", command=matrix_text.yview)
    matrix_scroll.grid(row=0, column=1, sticky="ns")
    matrix_text.configure(yscrollcommand=matrix_scroll.set)

    def display_peak_matrix():
        matrix_text.config(state="normal")
        matrix_text.delete("1.0", "end")
        if not peak_matrix:
            matrix_text.insert("end", "No peak data stored yet.\n")
        else:
            matrix_text.insert("end", "Frame Range → Sensor → Peak Pressure (kPa)\n")
            matrix_text.insert("end", "=" * 50 + "\n\n")
            for (start, end) in sorted(peak_matrix.keys()):
                matrix_text.insert("end", f"Frames [{start}, {end}]:\n")
                peaks = peak_matrix[(start, end)]
                if peaks:
                    for sensor in sorted(peaks.keys()):
                        matrix_text.insert("end", f"  {sensor}: {peaks[sensor]:.2f}\n")
                else:
                    matrix_text.insert("end", "  (no peaks found)\n")
                matrix_text.insert("end", "\n")
        matrix_text.config(state="disabled")
        return peaks

    # ---- Sensor Peaks (moved here) ----
    def peak_pressure_per_sensor(rows: list[dict]) -> Dict[str, float]:
        if not rows:
            return {}
        peaks: Dict[str, float] = {}
        for r in rows[:5000]:
            sensor = r.get("Sensor")
            peak_str = r.get("Peak Pressure (kPa)")
            if sensor is None or peak_str is None:
                continue
            peak_str = str(peak_str).strip()
            if peak_str == "":
                continue
            try:
                val = float(peak_str)
            except (ValueError, TypeError):
                continue
            prev = peaks.get(sensor)
            if prev is None or val > prev:
                peaks[sensor] = val
        return peaks

    def calculate_summary():
        sensor_peaks = peak_pressure_per_sensor(data_storage)
        print("sensor_peaks:", sensor_peaks)
        status_var.set("Printed sensor_peaks to console")

    def _show_peaks(peaks):
        peaks_text.config(state="normal")
        peaks_text.delete("1.0", "end")
        if isinstance(peaks, dict):
            for k in sorted(peaks):
                peaks_text.insert("end", f"{k}: {peaks[k]}\n")
        elif isinstance(peaks, (list, tuple)):
            for i, v in enumerate(peaks):
                peaks_text.insert("end", f"{i}: {v}\n")
        else:
            peaks_text.insert("end", repr(peaks) + "\n")
        peaks_text.config(state="disabled")

    def _run_and_show():
        try:
            calculate_summary()
            peaks = peak_pressure_per_sensor(data_storage)
            _show_peaks(peaks)
            status_var.set("Sensor peaks updated")
        except Exception as e:
            messagebox.showwarning("Peaks Error", f"Failed to compute/display peaks: {e}")

    ttk.Button(calc_left, text="Calculate Peaks", command=_run_and_show).pack(pady=(10, 6), fill="x")

    peaks_frame = ttk.LabelFrame(calc_left, text="Sensor Peaks", padding=(8, 6))
    peaks_frame.pack(fill="both", expand=True, pady=(0, 8))
    peaks_frame.columnconfigure(0, weight=1)
    peaks_frame.rowconfigure(0, weight=1)
    peaks_text = tk.Text(peaks_frame, wrap="none", state="disabled", height=6, width=1)
    peaks_text.grid(row=0, column=0, sticky="nsew")
    peaks_scroll = ttk.Scrollbar(peaks_frame, orient="vertical", command=peaks_text.yview)
    peaks_scroll.grid(row=0, column=1, sticky="ns")
    peaks_text.configure(yscrollcommand=peaks_scroll.set)

    # ---- Key Results box ----
    res_box = ttk.LabelFrame(calc_left, text="Key Results", padding=10)
    res_box.pack(fill="x", pady=(6, 0))
    calc_summary_var = tk.StringVar(value="—")
    ttk.Label(res_box, textvariable=calc_summary_var, justify="left").pack(anchor="w")

    fig_calc, ax_calc = plt.subplots(figsize=(8, 4))
    fig_calc.patch.set_facecolor("#f2f2f2")
    canvas_calc = FigureCanvasTkAgg(fig_calc, master=calc_right)
    canvas_calc.get_tk_widget().grid(row=0, column=0, sticky="nsew")

    def export_calc():
        if not data_storage:
            messagebox.showwarning("No data", "Load a CSV first.")
            return
        export_dir = filedialog.askdirectory(title="Select export folder")
        if not export_dir:
            return
        base = (current_file or "export").replace(" ", "_")
        perf = current_calc_state.get("per_frame", {})
        cop = perf.get("cop_xy_cm", [])
        rows = []
        for i in range(len(perf.get("vgrf_N", []))):
            cx, cy = cop[i] if i < len(cop) else (float("nan"), float("nan"))
            rows.append({
                "frame": i,
                "vGRF_N": perf["vgrf_N"][i],
                "avg_pressure_kPa": perf["avg_pressure_kPa"][i],
                "contact_area_cm2": perf["contact_area_cm2"][i],
                "CoP_x_cm": cx,
                "CoP_y_cm": cy,
            })
        csv_path = os.path.join(export_dir, f"{base}_per_frame_extended.csv")
        cols = ["frame","vGRF_N","avg_pressure_kPa","contact_area_cm2","CoP_x_cm","CoP_y_cm"]
        try:
            write_table_csv(csv_path, cols, rows)
        except Exception as e:
            messagebox.showwarning("Export Warning", f"Extended per-frame CSV failed: {e}")
        png_path = os.path.join(export_dir, f"{base}_calc_plot.png")
        try:
            save_plot_png(fig_calc, png_path, dpi=150)
        except Exception as e:
            messagebox.showwarning("Export Warning", f"Calc plot export failed: {e}")
        messagebox.showinfo("Export Complete", f"Saved:\n- {csv_path}\n- {png_path}")

    ttk.Button(calc_left, text="Export (per-frame + plot)", command=export_calc).pack(pady=(10, 0), fill="x")

    current_calc_state: Dict[str, object] = {}

    def _params() -> CalcParams:
        return {
            "fs": float(fs_var.get() or 1.0),
            "sensel_area_cm2": float(area_var.get() or 0.25),
            "contact_kpa": float(thr_var.get() or 20.0),
            "stance_bw_frac": float(bw_thr_var.get() or 0.05),
            "body_mass_kg": float(mass_var.get() or 75.0),
            "calibration_scale": float(cal_var.get() or 1.0),
            "smooth_win": int(smooth_var.get() or 1),
        }

    def refresh_calc():
        ax_calc.clear()
        if not data_storage:
            ax_calc.text(0.5, 0.5, "No data loaded", ha="center", va="center")
            canvas_calc.draw()
            return

        sensor_keys = infer_sensor_keys(data_storage)
        pressures = extract_per_frame_pressures(data_storage, sensor_keys)
        sensel_xy = [(float(i), 0.0) for i in range(len(sensor_keys))]

        P = _params()
        per_frame = compute_per_frame_bundle(pressures, sensel_xy, P)
        vgrf = per_frame["vgrf_N"]
        spans = detect_stance_windows(vgrf, P)
        tempo = temporal_spatial_from_spans(spans, P)
        impulse = compute_impulse_Ns(vgrf, P)
        rates = compute_load_rate(vgrf, P)

        current_calc_state.clear()
        current_calc_state["per_frame"] = per_frame
        current_calc_state["spans"] = spans
        current_calc_state["tempo"] = tempo
        current_calc_state["impulse_Ns"] = impulse
        current_calc_state["rates"] = rates

        ax_calc.plot(range(len(vgrf)), vgrf, label="vGRF (N)", linewidth=1.8)
        for a, b in spans:
            ax_calc.axvspan(a, b, color="#2c7a57", alpha=0.12)
        ax_calc.set_title("vGRF with stance windows")
        ax_calc.set_xlabel("Frame")
        ax_calc.set_ylabel("Force (N)")
        ax_calc.grid(True, linestyle="--", alpha=0.4)
        ax_calc.legend()
        fig_calc.tight_layout()
        canvas_calc.draw()

        calc_summary_var.set(
            "Impulse: {:.2f} N·s\n"
            "Load rate (max dF/dt): {:.0f} N/s\n"
            "Load rate (avg→80% peak): {:.0f} N/s\n"
            "Stance time (mean): {:.3f} s\n"
            "Step time (est): {:.3f} s | Cadence: {:.1f} spm".format(
                impulse, rates["max_dFdt_Ns"], rates["avg_up_to_80pct_Ns"],
                tempo["stance_time_s"], tempo["step_time_s"], tempo["cadence_spm"]
            )
        )

    # ====================== Helpers ==========================
    def _read_csv_lines(file_path: str):
        tried = []
        for enc in ("utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "utf-8", "latin1"):
            try:
                with open(file_path, mode="r", encoding=enc, newline="") as f:
                    return f.readlines()
            except (UnicodeError, UnicodeDecodeError, LookupError):
                tried.append(enc)
                continue
            except Exception:
                tried.append(enc)
                continue
        try:
            with open(file_path, "rb") as fb:
                b = fb.read()
            return b.decode("latin1").splitlines(True)
        except Exception:
            return None

    def import_csv(file_path=None):
        nonlocal current_file, current_page
        if file_path is None:
            file_path = filedialog.askopenfilename(title="Select CSV", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return
        current_file = os.path.basename(file_path)

        lines = _read_csv_lines(file_path)
        if not lines:
            messagebox.showerror("Error", "Cannot read CSV (unknown encoding).")
            return

        # Detect header start
        start_index = 0
        for i, line in enumerate(lines):
            s = line.strip()
            if s.startswith("Frame") or s.startswith("Subject"):
                start_index = i
                break

        reader = csv.DictReader(lines[start_index:])
        data_storage.clear()
        data_storage.extend(reader)

        if not data_storage:
            messagebox.showwarning("Empty File", "No rows found after header detection.")
            return

        update_display_columns()
        current_page = 0

        status_var.set(f"Imported {len(data_storage)} rows from {current_file}")
        messagebox.showinfo("Import Complete", f"{len(data_storage)} rows imported")

        nb.select(tab_table)
        show_page(0)
        update_plot()

        # Auto-calc summary for export/panels
        dt_from_meta = infer_dt_from_metadata(lines[:start_index], default_dt=1.0)
        dt = infer_dt_from_time_column(data_storage, default_dt=dt_from_meta)
        contact_thr = infer_threshold_from_column(data_storage, default_thr=20.0)
        sensor_keys = infer_sensor_keys(data_storage)

        try:
            fs_var.set(1.0 / max(1e-9, dt))
        except Exception:
            fs_var.set(1.0)
        thr_var.set(contact_thr)

        s = compute_session_summary(
            data_storage=data_storage,
            sensor_keys=sensor_keys,
            contact_threshold=contact_thr,
            dt=dt
        )

        summary_panel.load(
            data_storage,
            sensor_keys,
            contact_threshold=contact_thr,
            dt=dt
        )

        nonlocal last_summary, last_base_name
        last_base_name = (current_file or "export").replace(" ", "_").replace("/", "_")
        last_summary = {
            "frames": s.frames,
            "sensors": s.sensors,
            "global_min": s.global_min,
            "global_max": s.global_max,
            "contact_time_frames": s.contact_time_frames,
            "contact_threshold": s.contact_threshold,
            "pti": s.pti,
            "dt": s.dt,
            "avg_pressure_per_frame": s.avg_pressure_per_frame,
            "estimated_vgrf_per_frame": s.estimated_vgrf_per_frame,
        }

        status_var.set(status_var.get() + f" | dt={dt:.3f}s, thr={contact_thr:.2f} kPa")
        refresh_calc()

    def _safe_float(s):
        try:
            return float(s)
        except Exception:
            return None

    def _update_status_peek():
        _recalc_height_cm()
        status_var.set(
            f"H: {metadata['height_ft']}ft {metadata['height_in']}in "
            f"({metadata['height_cm']} cm), "
            f"W: {metadata['weight_lb']} lb | "
            f"Gender: {metadata['gender']}, Dom: {metadata['dominance']} | "
            f"Zones: {', '.join(sorted(metadata['zones'])) if metadata['zones'] else 'None'}"
        )

    def refresh_info_labels():
        _recalc_height_cm()
        _update_status_peek()

    # ---------- Table helpers ----------
    def update_display_columns():
        display_columns.clear()
        if not data_storage:
            column_combo["values"] = ["All"]
            column_combo.set("All")
            return
        cols = list(data_storage[0].keys())
        main_cols = cols[:-341] if len(cols) > 341 else cols
        display_columns.extend(main_cols)
        column_combo["values"] = ["All"] + display_columns
        if not column_combo.get():
            column_combo.set("All")

    def _paginate_rows(rows: list[dict]):
        nonlocal current_page
        if not rows:
            current_page = 0
            return [], 0, 0
        max_page = max((len(rows) - 1) // ROWS_PER_PAGE, 0)
        current_page = max(0, min(current_page, max_page))
        start = current_page * ROWS_PER_PAGE
        end = start + ROWS_PER_PAGE
        return rows[start:end], current_page + 1, max_page + 1

    def _all_rows_for_table():
        return data_storage

    def show_page(page: int | None = None):
        nonlocal current_page
        if page is not None:
            current_page = page

        rows = _all_rows_for_table()

        if rows and not display_columns:
            update_display_columns()

        chosen = column_combo.get()
        if chosen in (None, "", "All"):
            cols_to_show = display_columns[:] if display_columns else (list(rows[0].keys()) if rows else [])
        else:
            cols_to_show = [chosen]

        page_rows, page_num, total_pages = _paginate_rows(rows)

        tree.delete(*tree.get_children())
        tree["columns"] = cols_to_show
        for col in cols_to_show:
            tree.heading(col, text=col)
            tree.column(col, width=80, stretch=False, anchor="center")

        for row in page_rows:
            tree.insert("", "end", values=[row.get(c, "") for c in cols_to_show])

        page_label.config(text=f"Page {page_num} of {total_pages}")

    # ---------- Visualization plot ----------
    def update_plot():
        rows = _all_rows_for_table()
        ax.clear()
        ax.set_facecolor("white")
        fig.patch.set_facecolor("#f2f2f2")

        if not rows:
            ax.text(0.5, 0.5, "No data loaded", ha="center", va="center")
            canvas.draw()
            return

        headers = {h.lower(): h for h in rows[0].keys()}
        frame_col = next((headers[h] for h in headers if "frame" in h), None)
        insole_col = next((headers[h] for h in headers if "insole" in h), None)
        peak_col = next((headers[h] for h in headers if "peak" in h and "pressure" in h), None)
        contact_col = next((headers[h] for h in headers if "contact" in h and "area" in h), None)
        avg_col = next((headers[h] for h in headers if "avg" in h and "pressure" in h), None)
        min_col = next((headers[h] for h in headers if "min" in h and "pressure" in h), None)
        contact_pct_col = next((headers[h] for h in headers if "%" in h or "percent" in h), None)
        load_col = next((headers[h] for h in headers if "load" in h or "vgrf" in h), None)

        selected_metric = metric_var.get()
        if selected_metric == "Contact Area":
            y_col = contact_col
        elif selected_metric == "Avg Pressure":
            y_col = avg_col
        elif selected_metric == "Minimum Pressure":
            y_col = min_col
        elif selected_metric == "Estimated Load":
            y_col = load_col
        elif selected_metric == "Contact %":
            y_col = contact_pct_col
        else:
            y_col = peak_col

        if not all([insole_col, y_col]):
            ax.text(0.5, 0.5, f"Columns 'Insole' and '{selected_metric}' not found", ha="center", va="center")
            canvas.draw()
            return

        start_idx = int(frame_start_var.get()) if frame_start_var.get().isdigit() else 0
        end_idx = int(frame_end_var.get()) if frame_end_var.get().isdigit() else None

        sides = {"Left": {"x": [], "y": []}, "Right": {"x": [], "y": []}}
        for r in rows:
            side = r.get(insole_col, "").strip().capitalize()
            y_val = _safe_float(r.get(y_col))
            f = _safe_float(r.get(frame_col)) if frame_col else None
            if side in sides and y_val is not None and math.isfinite(y_val):
                xval = f if f is not None else len(sides[side]["x"])
                sides[side]["x"].append(xval)
                sides[side]["y"].append(y_val)

        if end_idx is not None and end_idx > 0:
            for side in sides:
                sides[side]["x"] = sides[side]["x"][start_idx:end_idx]
                sides[side]["y"] = sides[side]["y"][start_idx:end_idx]
        else:
            for side in sides:
                sides[side]["x"] = sides[side]["x"][start_idx:]
                sides[side]["y"] = sides[side]["y"][start_idx:]

        colors = {"Left": "#169873", "Right": "#f06292"}
        plotted = False
        if show_left_var.get():
            data = sides["Left"]
            if data["x"]:
                ax.plot(data["x"], data["y"], label="Left Foot", linewidth=1.8, color=None)
                plotted = True
        if show_right_var.get():
            data = sides["Right"]
            if data["x"]:
                ax.plot(data["x"], data["y"], label="Right Foot", linewidth=1.8, color=None)
                plotted = True

        if plotted:
            ax.set_xlabel("Frame" if frame_col else "Sample Index")
            if selected_metric in ("Peak Pressure", "Avg Pressure"):
                ylabel_unit = "kPa"
            elif selected_metric == "Contact %":
                ylabel_unit = "%"
            elif selected_metric == "Estimated Load":
                ylabel_unit = "N"
            else:
                ylabel_unit = "cm²"
            ax.set_ylabel(f"{selected_metric} ({ylabel_unit})")
            ax.legend()
            ax.grid(True, linestyle="--", alpha=0.4)
            ax.set_title(f"{selected_metric} Comparison (Left vs Right Insole)", fontsize=12, weight="bold")
        else:
            ax.text(0.5, 0.5, f"No valid {selected_metric} values found", ha="center", va="center")

        fig.tight_layout()
        canvas.draw()
        _update_status_peek()

    # ---------- Compact + auto-collapse behavior ----------
    def apply_compact_styles():
        nonlocal current_top_left, current_top_right, current_middle_left, current_middle_right, current_bottom_left, current_bottom_right
        if compact_mode:
            import_hint.configure(text="Import CSV (click) / DnD")
            zone_canvas.configure(width=130, height=170)
            current_top_left     = base_top_left.subsample(2, 2)
            current_top_right    = base_top_right.subsample(2, 2)
            current_middle_left  = base_middle_left.subsample(2, 2)
            current_middle_right = base_middle_right.subsample(2, 2)
            current_bottom_left  = base_bottom_left.subsample(2, 2)
            current_bottom_right = base_bottom_right.subsample(2, 2)
            peaks_text.configure(height=5)
            tree.configure(height=10)
        else:
            import_hint.configure(text="Import CSV (click)\n—or—\nDrag & Drop a CSV")
            zone_canvas.configure(width=150, height=200)
            current_top_left     = base_top_left
            current_top_right    = base_top_right
            current_middle_left  = base_middle_left
            current_middle_right = base_middle_right
            current_bottom_left  = base_bottom_left
            current_bottom_right = base_bottom_right
            peaks_text.configure(height=6)
            tree.configure(height=12)
        draw_zone_grid()

    def auto_collapse_by_height(h_now: int):
        """
        Collapse from the top down as height shrinks.
        """
        if h_now < 720:
            filter_section.set_open(False)
        else:
            filter_section.set_open(True)

        if h_now < 690:
            colopts_section.set_open(False)
        else:
            colopts_section.set_open(True)

        if h_now < 660:
            info_section.set_open(False)
        else:
            info_section.set_open(True)

    def on_root_resize(_evt=None):
        nonlocal compact_mode
        h = root.winfo_height()
        want_compact = h < 760
        if want_compact != compact_mode:
            compact_mode = want_compact
            apply_compact_styles()
        auto_collapse_by_height(h)

    root.bind("<Configure>", on_root_resize)

    # initial draw
    draw_zone_grid()
    apply_compact_styles()
    auto_collapse_by_height(root.winfo_height())

    # ---- Bindings ----
    def on_column_change(_evt=None):
        set_current_page(0)
        show_page(0)

    column_combo.bind("<<ComboboxSelected>>", on_column_change)

    def on_prev():
        show_page(max(current_page - 1, 0))

    def on_next():
        show_page(current_page + 1)

    prev_btn.configure(command=on_prev)
    next_btn.configure(command=on_next)

    def set_current_page(val):
        nonlocal current_page
        current_page = val

    _recalc_height_cm()
    _update_status_peek()

    root.mainloop()


# ---------- Helper inference functions ----------
def infer_dt_from_metadata(lines: list[str], default_dt: float = 1.0) -> float:
    pat = re.compile(r"Target\s+framerate\s*:\s*([0-9]*\.?[0-9]+)\s*Hz", re.IGNORECASE)
    for line in lines:
        m = pat.search(line)
        if m:
            try:
                fps = float(m.group(1))
                if fps > 0:
                    return 1.0 / fps
            except Exception:
                pass
    return default_dt


def infer_dt_from_time_column(rows: list[dict], default_dt: float = 1.0) -> float:
    if not rows:
        return default_dt
    headers = {h.lower(): h for h in rows[0].keys()}
    time_col = headers.get("time") or headers.get("timestamp")
    if not time_col:
        return default_dt

    insole_col = next((headers[h] for h in headers if "insole" in h), None)
    groups: dict[str, list[float]] = {}

    for r in rows[:2000]:
        grp = r.get(insole_col, "global") if insole_col else "global"
        val = r.get(time_col)
        try:
            t = float(val)
        except (TypeError, ValueError):
            continue
        groups.setdefault(grp, []).append(t)

    deltas: list[float] = []
    for seq in groups.values():
        if len(seq) < 2:
            continue
        seq = sorted(seq)
        for i in range(1, len(seq)):
            d = seq[i] - seq[i - 1]
            if d > 0:
                deltas.append(d)

    return statistics.median(deltas) if len(deltas) >= 5 else default_dt


def infer_threshold_from_column(rows: list[dict], default_thr: float = 20.0) -> float:
    if not rows:
        return default_thr
    headers = {h.lower(): h for h in rows[0].keys()}
    thr_col = headers.get("threshold")
    if not thr_col:
        return default_thr

    vals: list[float] = []
    for r in rows[:5000]:
        raw = r.get(thr_col)
        try:
            v = float(raw)
        except (TypeError, ValueError):
            continue
        if v >= 0:
            vals.append(v)
    return statistics.median(vals) if vals else default_thr


if __name__ == "__main__":
    run_ui()
