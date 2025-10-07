import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import csv
from tkinterdnd2 import DND_FILES, TkinterDnD


def run_ui():
    root = TkinterDnD.Tk()
    root.title("Sole Solutions: Data Visualizer")
    root.geometry("1200x700")
    root.configure(bg="#f2f2f2")

    data_storage = []
    current_file = None
    ROWS_PER_PAGE = 100
    current_page = 0
    display_columns = []

    # ===== Left panel =====
    left_frame = tk.Frame(root, bg="#f2f2f2")
    left_frame.pack(side="left", fill="y", padx=20, pady=20)

    info_frame = tk.LabelFrame(left_frame, text="Participant Info", bg="#ffffff", padx=10, pady=10)
    info_frame.pack(fill="x", pady=10)

    tk.Label(info_frame, text="Height (cm):").grid(row=0, column=0, sticky="w")
    tk.Entry(info_frame).grid(row=0, column=1)

    tk.Label(info_frame, text="Weight (kg):").grid(row=1, column=0, sticky="w")
    tk.Entry(info_frame).grid(row=1, column=1)

    tk.Label(info_frame, text="Gender:").grid(row=2, column=0, sticky="w")
    gender_combo = ttk.Combobox(info_frame, values=["Male", "Female", "Unspecified"], state="readonly")
    gender_combo.grid(row=2, column=1)
    gender_combo.current(0)

    tk.Label(info_frame, text="Foot Dominance:").grid(row=3, column=0, sticky="w")
    dominance_combo = ttk.Combobox(info_frame, values=["Left", "Right", "Both"], state="readonly")
    dominance_combo.grid(row=3, column=1)
    dominance_combo.current(0)

    # Column selection
    filter_frame = tk.LabelFrame(left_frame, text="Column Options", bg="#ffffff", padx=10, pady=10)
    filter_frame.pack(fill="x", pady=10)

    tk.Label(filter_frame, text="Select Column:").grid(row=0, column=0, sticky="w")
    column_combo = ttk.Combobox(filter_frame, values=[], state="readonly")
    column_combo.grid(row=0, column=1)

    import_btn = tk.Button(left_frame, text="Import CSV", bg="#4CAF50", fg="white")
    import_btn.pack(pady=10, fill="x")

    drop_frame = tk.Label(
        left_frame,
        text="Or drag & drop CSV here",
        bg="#d9edf7",
        fg="#31708f",
        relief="ridge",
        width=25,
        height=5,
    )
    drop_frame.pack(pady=20)

    # ===== Right panel =====
    right_frame = tk.Frame(root, bg="#f2f2f2")
    right_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)

    # Smaller table toward top
    table_frame = tk.Frame(right_frame, bg="#ffffff", relief="groove", bd=2)
    table_frame.pack(fill="x", pady=5, anchor="n")

    # Treeview
    tree = ttk.Treeview(table_frame, show="headings", height=12)
    tree.grid(row=0, column=0, sticky="nsew")

    # Scrollbars
    v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    v_scrollbar.grid(row=0, column=1, sticky="ns")
    tree.configure(yscrollcommand=v_scrollbar.set)

    h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
    h_scrollbar.grid(row=1, column=0, sticky="ew")
    tree.configure(xscrollcommand=h_scrollbar.set)

    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)

    # Pagination controls
    pagination_frame = tk.Frame(right_frame, bg="#f2f2f2")
    pagination_frame.pack(fill="x", pady=5, anchor="n")

    prev_btn = tk.Button(pagination_frame, text="Previous")
    prev_btn.pack(side="left", padx=5)
    next_btn = tk.Button(pagination_frame, text="Next")
    next_btn.pack(side="left", padx=5)

    page_label = tk.Label(pagination_frame, text="Page 0 of 0", bg="#f2f2f2")
    page_label.pack(side="right")

    # ===== Functions =====
    def update_columns():
        """Remove last 341 sensor columns and populate combobox."""
        if not data_storage:
            return []

        all_cols = list(data_storage[0].keys())
        main_cols = all_cols[:-341] if len(all_cols) > 341 else all_cols
        column_combo["values"] = ["All"] + main_cols
        column_combo.current(0)
        return main_cols

    def show_page(page):
        nonlocal current_page, display_columns
        if not data_storage:
            page_label.config(text="Page 0 of 0")
            return

        if not display_columns:
            display_columns = update_columns() or []

        selected_col = column_combo.get()
        columns_to_show = display_columns if selected_col in ("", "All") else [selected_col]

        max_page = max((len(data_storage) - 1) // ROWS_PER_PAGE, 0)
        page = max(0, min(page, max_page))
        current_page = page

        start = page * ROWS_PER_PAGE
        end = start + ROWS_PER_PAGE
        page_data = data_storage[start:end]

        tree.delete(*tree.get_children())
        tree["columns"] = columns_to_show

        for col in columns_to_show:
            tree.heading(col, text=col)
            tree.column(col, width=80, stretch=False, anchor="center")

        for row in page_data:
            tree.insert("", "end", values=[row.get(c, "") for c in columns_to_show])

        page_label.config(text=f"Page {current_page + 1} of {max_page + 1}")

    def import_csv(file_path=None):
        nonlocal current_file, current_page, display_columns
        if file_path is None:
            file_path = filedialog.askopenfilename(title="Select CSV", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

        current_file = file_path.split("/")[-1].split("\\")[-1]

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

        # Find header line starting with "Frame"
        start_index = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("Frame"):
                start_index = i
                break

        reader = csv.DictReader(lines[start_index:])
        data_storage.clear()
        data_storage.extend(reader)

        messagebox.showinfo("Import Complete", f"{len(data_storage)} rows imported")

        current_page = 0
        display_columns = update_columns()
        show_page(0)

    # ===== Event bindings =====
    column_combo.bind("<<ComboboxSelected>>", lambda e: show_page(current_page))
    import_btn.configure(command=import_csv)
    prev_btn.configure(command=lambda: show_page(max(current_page - 1, 0)))
    next_btn.configure(command=lambda: show_page(current_page + 1))

    def drop(event):
        files = root.splitlist(event.data)
        if files:
            import_csv(files[0])

    drop_frame.drop_target_register(DND_FILES)
    drop_frame.dnd_bind("<<Drop>>", drop)

    root.mainloop()


if __name__ == "__main__":
    run_ui()
