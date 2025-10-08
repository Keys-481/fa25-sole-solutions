import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import csv
import os
import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Drag & drop (graceful fallback if tkinterdnd2 is not present)
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except Exception:
    TkinterDnD = tk  # fallback to standard Tk
    DND_FILES = None
    DND_AVAILABLE = False


def run_ui():
    # Root window (DnD-enabled if available)
    root = TkinterDnD.Tk() if DND_AVAILABLE else tk.Tk()
    root.title("Sole Solutions: Data Visualizer")
    root.geometry("1920x1080")
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
    data_storage: list[dict] = []     # all imported rows (list of dicts)
    selected_zones: set[str] = set()
    metadata = {
        "height_ft": 0,
        "height_in": 0,
        "height_cm": 0.0,   # derived
        "weight_lb": 0,
        "gender": "Male",
        "dominance": "Left",
        "zones": selected_zones
    }
    # (from File 2)
    current_file: str | None = None
    ROWS_PER_PAGE = 100
    current_page = 0
    display_columns: list[str] = []

    def _recalc_height_cm():
        total_in = metadata["height_ft"] * 12 + metadata["height_in"]
        metadata["height_cm"] = round(total_in * 2.54, 1)

    # ---------- Header ----------
    header = ttk.Frame(root)
    header.pack(fill="x", padx=16, pady=(12, 0))
    ttk.Label(header, text="Sole Solutions: Data Visualizer", style="Header.TLabel").pack(side="left")

    status_var = tk.StringVar(value="Ready")
    ttk.Label(header, textvariable=status_var, style="Hint.TLabel").pack(side="right", padx=(8, 0))

    def do_export():
        if not tree.get_children():
            messagebox.showwarning("Nothing to Export", "No table rows to export yet.")
            return
        export_dir = filedialog.askdirectory(title="Select export folder")
        if not export_dir:
            return
        base = (current_file or "export").replace(" ", "_")

        # table csv
        csv_path = os.path.join(export_dir, f"{base}_table.csv")
        cols = tree["columns"]
        try:
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(cols)
                for iid in tree.get_children():
                    writer.writerow(tree.item(iid, "values"))
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to write CSV: {e}")
            return

        # plot png (Visualization tab figure)
        png_path = os.path.join(export_dir, f"{base}_plot.png")
        try:
            fig.savefig(png_path, dpi=150, bbox_inches="tight")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to save plot: {e}")
            return

        status_var.set(f"Exported CSV and PNG to {export_dir}")
        messagebox.showinfo("Export Complete", f"Saved:\n- {csv_path}\n- {png_path}")

    ttk.Button(header, text="Export…", command=do_export).pack(side="right")

    # ---------- Notebook ----------
    nb = ttk.Notebook(root)
    nb.pack(fill="both", expand=True, padx=16, pady=16)

    # Tabs order: Data Table (front page), Visualization (blank graph)
    tab_table  = ttk.Frame(nb)
    tab_visual = ttk.Frame(nb)
    nb.add(tab_table,  text="Data Table")
    nb.add(tab_visual, text="Visualization")

    # =========================================================
    # ==================== Data Table tab =====================
    # =========================================================
    # Make a two-column layout like File 2 (left controls, right table)
    tab_table.columnconfigure(0, weight=0)
    tab_table.columnconfigure(1, weight=1)
    tab_table.rowconfigure(0, weight=1)

    # ---- Left column (File 1 controls, no Subject/Trial filters) ----
    left_frame = tk.Frame(tab_table, bg="#f2f2f2")
    left_frame.grid(row=0, column=0, sticky="nsw", padx=20, pady=20)

    # Import card (click or DnD)
    import_container = ttk.Frame(left_frame, style="Import.TFrame")
    import_container.pack(fill="x", pady=(0, 12))
    import_hint = ttk.Label(
        import_container,
        text="Import CSV (click this card)\n—or—\nDrag & Drop a CSV here",
        anchor="center", style="Hint.TLabel", justify="center"
    )
    import_hint.pack(fill="x", padx=12, pady=16)

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

    # Participant info
    info_frame = tk.LabelFrame(left_frame, text="Participant Info", bg="#ffffff", padx=10, pady=10)
    info_frame.pack(fill="x", pady=10)

    # Column Options (Select Column) — from File 2 (replaces Subject/Trial filters)
    colopts_frame = tk.LabelFrame(left_frame, text="Column Options", bg="#ffffff", padx=10, pady=10)
    colopts_frame.pack(fill="x", pady=10)
    tk.Label(colopts_frame, text="Select Column:", bg="#ffffff").grid(row=0, column=0, sticky="w")
    column_combo = ttk.Combobox(colopts_frame, values=[], state="readonly", width=24)
    column_combo.grid(row=0, column=1, sticky="ew", padx=(6, 0))
    column_combo.set("All")

    # Insole Zones
    zones_frame = tk.LabelFrame(left_frame, text="Insole Zones (3×2)", bg="#ffffff", padx=10, pady=10)
    zones_frame.pack(fill="x", pady=10)
    zone_canvas = tk.Canvas(zones_frame, width=240, height=150, bg="#ffffff", highlightthickness=1, relief="ridge")
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

    # Validation helpers (integers only)
    def _only_int(P): return P == "" or P.isdigit()
    vcmd = (root.register(_only_int), "%P")

    # Height (ft/in)
    tk.Label(info_frame, text="Height:", bg="#ffffff").grid(row=0, column=0, sticky="w", pady=(2, 2))
    tk.Label(info_frame, text="ft",     bg="#ffffff").grid(row=0, column=2, sticky="w")
    tk.Label(info_frame, text="in",     bg="#ffffff").grid(row=0, column=4, sticky="w")
    height_ft_var = tk.StringVar(value=str(metadata["height_ft"]))
    height_in_var = tk.StringVar(value=str(metadata["height_in"]))
    height_ft_entry = ttk.Entry(info_frame, textvariable=height_ft_var, width=4, validate="key", validatecommand=vcmd)
    height_in_entry = ttk.Entry(info_frame, textvariable=height_in_var, width=4, validate="key", validatecommand=vcmd)
    height_ft_entry.grid(row=0, column=1, sticky="w", padx=(6, 6))
    height_in_entry.grid(row=0, column=3, sticky="w", padx=(6, 6))

    # Weight (lb)
    tk.Label(info_frame, text="Weight:", bg="#ffffff").grid(row=1, column=0, sticky="w", pady=(6, 2))
    tk.Label(info_frame, text="lb",      bg="#ffffff").grid(row=1, column=2, sticky="w")
    weight_lb_var = tk.StringVar(value=str(metadata["weight_lb"]))
    weight_lb_entry = ttk.Entry(info_frame, textvariable=weight_lb_var, width=6, validate="key", validatecommand=vcmd)
    weight_lb_entry.grid(row=1, column=1, sticky="w", padx=(6, 6))

    def _commit_height(_evt=None):
        ft = int(height_ft_var.get()) if height_ft_var.get().isdigit() else metadata["height_ft"]
        inch = int(height_in_var.get()) if height_in_var.get().isdigit() else metadata["height_in"]
        ft = max(3, min(ft, 8)); inch = max(0, min(inch, 11))
        metadata["height_ft"] = ft; metadata["height_in"] = inch
        height_ft_var.set(str(ft)); height_in_var.set(str(inch))
        _recalc_height_cm(); refresh_info_labels()

    def _commit_weight(_evt=None):
        lb = int(weight_lb_var.get()) if weight_lb_var.get().isdigit() else metadata["weight_lb"]
        lb = max(60, min(lb, 350))
        metadata["weight_lb"] = lb; weight_lb_var.set(str(lb)); refresh_info_labels()

    for w in (height_ft_entry, height_in_entry):
        w.bind("<FocusOut>", _commit_height); w.bind("<Return>", _commit_height)
    weight_lb_entry.bind("<FocusOut>", _commit_weight); weight_lb_entry.bind("<Return>", _commit_weight)

    # Gender / Dominance
    tk.Label(info_frame, text="Gender:", bg="#ffffff").grid(row=2, column=0, sticky="w", pady=(8, 0))
    gender_combo = ttk.Combobox(info_frame, values=["Male", "Female", "Unspecified"], state="readonly", width=16)
    gender_combo.grid(row=2, column=1, sticky="w", pady=(8, 0)); gender_combo.current(0)
    gender_combo.bind("<<ComboboxSelected>>", lambda *_: metadata.__setitem__("gender", gender_combo.get()))
    tk.Label(info_frame, text="Foot Dominance:", bg="#ffffff").grid(row=3, column=0, sticky="w", pady=(6, 0))
    dominance_combo = ttk.Combobox(info_frame, values=["Left", "Right", "Both"], state="readonly", width=16)
    dominance_combo.grid(row=3, column=1, sticky="w", pady=(6, 0)); dominance_combo.current(0)
    dominance_combo.bind("<<ComboboxSelected>>", lambda *_: metadata.__setitem__("dominance", dominance_combo.get()))

    def draw_zone_grid():
        zone_canvas.delete("all")
        w, h = 240, 150; cols, rows = 2, 3; cw, ch = w/cols, h/rows
        for r in range(rows):
            for c in range(cols):
                key = zone_keys[r][c]
                x0, y0 = c*cw, r*ch; x1, y1 = x0+cw, y0+ch
                is_sel = key in selected_zones
                fill = "#46c081" if is_sel else "#ffffff"
                outline = "#2c7a57" if is_sel else "#9aa3ab"
                rid = zone_canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline=outline, width=2)
                rect_ids[rid] = key
                zone_canvas.create_text((x0+x1)/2, (y0+y1)/2, text=zone_labels[r][c], font=("Arial", 10))
        zone_canvas.create_rectangle(1, 1, w-1, h-1, outline="#9aa3ab", width=1)

    def toggle_zone(event):
        item = zone_canvas.find_closest(event.x, event.y)
        if not item: return
        rid = item[0]
        if rid not in rect_ids:
            for cand in zone_canvas.find_overlapping(event.x, event.y, event.x, event.y):
                if cand in rect_ids: rid = cand; break
        key = rect_ids.get(rid)
        if not key: return
        if key in selected_zones: selected_zones.remove(key)
        else: selected_zones.add(key)
        metadata["zones"] = selected_zones
        draw_zone_grid()
        sel_var.set("Selected: " + (", ".join(sorted(selected_zones)) if selected_zones else "None"))
        _update_status_peek()

    zone_canvas.bind("<Button-1>", toggle_zone)
    sel_var = tk.StringVar(value="Selected: None")
    ttk.Label(left_frame, textvariable=sel_var, style="Hint.TLabel").pack(anchor="w", padx=4)
    draw_zone_grid()

    # ---- Right column (File 2 Data Table style) ----
    right_frame = tk.Frame(tab_table, bg="#f2f2f2")
    right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
    right_frame.columnconfigure(0, weight=1)

    # Compact, bordered table box
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

    # Pagination controls (bottom, with Page label at far right)
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
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.set_facecolor("white")
    fig.patch.set_facecolor("#f2f2f2")
    canvas = FigureCanvasTkAgg(fig, master=viz_container)
    canvas.get_tk_widget().pack(fill="both", expand=True)

    # =========================================================
    # ====================== Functions ========================
    # =========================================================
    def import_csv(file_path=None):
        nonlocal current_file, current_page
        if file_path is None:
            file_path = filedialog.askopenfilename(title="Select CSV", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return
        current_file = os.path.basename(file_path)

        lines = None
        for enc in ("utf-8-sig", "utf-16", "latin1"):
            try:
                with open(file_path, newline="", encoding=enc) as f:
                    lines = f.readlines()
                break
            except UnicodeDecodeError:
                continue
        if not lines:
            messagebox.showerror("Error", "Cannot read CSV")
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
        data_storage.extend([row for row in reader])

        if not data_storage:
            messagebox.showwarning("Empty File", "No rows found after header detection.")
            return

        update_display_columns()
        current_page = 0

        status_var.set(f"Imported {len(data_storage)} rows from {current_file}")
        messagebox.showinfo("Import Complete", f"{len(data_storage)} rows imported")

        nb.select(tab_table)   # show the Data Table front page
        show_page(0)
        update_plot()

    def _safe_float(s):
        try:
            return float(s)
        except Exception:
            return None

    def _update_status_peek():
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

    # ---------- Table helpers (File 2 behavior, adapted) ----------
    def update_display_columns():
        """Populate 'column_combo' and choose default visible columns."""
        display_columns.clear()
        if not data_storage:
            column_combo["values"] = ["All"]
            column_combo.set("All")
            return
        cols = list(data_storage[0].keys())
        # Keep File 2’s heuristic: hide last 341 sensor columns by default.
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
        """No Subject/Trial filters now—show all imported rows, paginated."""
        return data_storage

    def show_page(page: int | None = None):
        """Render the table like File 2, respecting column choice + pagination."""
        nonlocal current_page
        if page is not None:
            current_page = page

        rows = _all_rows_for_table()

        # init columns once data present
        if rows and not display_columns:
            update_display_columns()

        chosen = column_combo.get()
        if chosen in (None, "", "All"):
            cols_to_show = display_columns[:] if display_columns else (list(rows[0].keys()) if rows else [])
        else:
            cols_to_show = [chosen]

        page_rows, page_num, total_pages = _paginate_rows(rows)

        # draw table
        tree.delete(*tree.get_children())
        tree["columns"] = cols_to_show
        for col in cols_to_show:
            tree.heading(col, text=col)
            tree.column(col, width=80, stretch=False, anchor="center")

        for row in page_rows:
            tree.insert("", "end", values=[row.get(c, "") for c in cols_to_show])

        page_label.config(text=f"Page {page_num} of {total_pages}")

    # ---------- Plot (Visualization tab — blank/optional for now) ----------
    def update_plot():
        """Basic plot stub; draws Time vs PeakPressure_Left if present."""
        rows = _all_rows_for_table()
        ax.clear()
        time_col = "Time"; press_col = "PeakPressure_Left"
        if rows and time_col in rows[0] and press_col in rows[0]:
            xs, ys = [], []
            for r in rows:
                t = _safe_float(r.get(time_col)); p = _safe_float(r.get(press_col))
                if t is not None and p is not None and math.isfinite(t) and math.isfinite(p):
                    xs.append(t); ys.append(p)
            if xs and ys:
                ax.plot(xs, ys, label="PeakPressure_Left", linewidth=2, color="#169873")
                ax.set_facecolor("white"); ax.set_xlabel("Time"); ax.set_ylabel("Peak Pressure (kPa)"); ax.legend()
            else:
                ax.text(0.5, 0.5, "No numeric data to plot", ha="center", va="center")
        else:
            ax.text(0.5, 0.5, "No plot configured yet", ha="center", va="center")
        fig.tight_layout(); canvas.draw(); _update_status_peek()

    # ---- Bindings ----
    column_combo.bind("<<ComboboxSelected>>",  lambda *_: (set_current_page(0), show_page(0)))
    prev_btn.configure(command=lambda: show_page(max(current_page - 1, 0)))
    next_btn.configure(command=lambda: show_page(current_page + 1))

    def set_current_page(val):
        nonlocal current_page
        current_page = val

    # init labels
    _recalc_height_cm()
    _update_status_peek()

    root.mainloop()


if __name__ == "__main__":
    run_ui()
