import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import csv
import os


def run_ui():
    root = tk.Tk()
    root.title("Sole Solutions")
    root.geometry("900x600")
    root.configure(bg="#f2f2f2")

    # ===== Title =====
    title_label = tk.Label(
        root, 
        text="Sole Solutions: Gait Data Visualizer",
        font=("Segoe UI", 20, "bold"),
        bg="#f2f2f2",
        fg="#333"
    )
    title_label.pack(pady=20)

    # ===== Main container =====
    main_frame = tk.Frame(root, bg="#f2f2f2")
    main_frame.pack(fill="both", expand=True, padx=40, pady=20)

    # ===== Left panel: User Info =====
    user_frame = tk.LabelFrame(
        main_frame,
        text="Participant Information",
        font=("Segoe UI", 12, "bold"),
        bg="#ffffff",
        padx=20,
        pady=20,
        relief="groove",
        borderwidth=2
    )
    user_frame.pack(side="left", fill="y", padx=(0, 20), pady=10)

    # Height
    tk.Label(user_frame, text="Height (cm):", font=("Segoe UI", 11), bg="#ffffff").grid(row=0, column=0, sticky="w", pady=5)
    height_entry = tk.Entry(user_frame, font=("Segoe UI", 11), width=20)
    height_entry.grid(row=0, column=1, pady=5)

    # Weight
    tk.Label(user_frame, text="Weight (kg):", font=("Segoe UI", 11), bg="#ffffff").grid(row=1, column=0, sticky="w", pady=5)
    weight_entry = tk.Entry(user_frame, font=("Segoe UI", 11), width=20)
    weight_entry.grid(row=1, column=1, pady=5)

    # Gender
    tk.Label(user_frame, text="Gender:", font=("Segoe UI", 11), bg="#ffffff").grid(row=2, column=0, sticky="w", pady=5)
    gender_combo = ttk.Combobox(
        user_frame,
        values=["Male", "Female", "Unspecified"],
        state="readonly",
        width=17,
        font=("Segoe UI", 11)
    )
    gender_combo.grid(row=2, column=1, pady=5)
    gender_combo.current(0)

    # Foot dominance
    tk.Label(user_frame, text="Foot Dominance:", font=("Segoe UI", 11), bg="#ffffff").grid(row=3, column=0, sticky="w", pady=5)
    dominance_combo = ttk.Combobox(
        user_frame,
        values=["Left", "Right", "Both"],
        state="readonly",
        width=17,
        font=("Segoe UI", 11)
    )
    dominance_combo.grid(row=3, column=1, pady=5)
    dominance_combo.current(0)

    # ===== Right panel: Data Import =====
    data_frame = tk.LabelFrame(
        main_frame,
        text="Data Import",
        font=("Segoe UI", 12, "bold"),
        bg="#ffffff",
        padx=20,
        pady=20,
        relief="groove",
        borderwidth=2
    )
    data_frame.pack(side="right", fill="both", expand=True, pady=10)

    def import_csv():
        file_path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".csv"):
            messagebox.showerror("Invalid File", "Please select a valid .csv file.")
            return

        # Try multiple encodings
        lines = None
        for enc in ("utf-8-sig", "utf-16", "latin1"):
            try:
                with open(file_path, newline="", encoding=enc) as f:
                    lines = f.readlines()
                break
            except UnicodeDecodeError:
                continue

        if not lines:
            messagebox.showerror("Error", "Could not read CSV file with common encodings.")
            return

        # Find data start
        start_index = next((i for i, line in enumerate(lines) if line.strip().startswith("Frame")), None)
        if start_index is None:
            messagebox.showerror("Error", "No valid data table found in CSV.")
            return

        reader = csv.DictReader(lines[start_index:])
        data = [row for row in reader]

        messagebox.showinfo(
            "Import Complete",
            f"Successfully imported {len(data)} rows from {os.path.basename(file_path)}"
        )

        # Display in table
        update_table(data)

    def update_table(data):
        # Clear existing data
        for row in tree.get_children():
            tree.delete(row)
        # Insert new data (limit to first 20 for performance)
        for i, row in enumerate(data[:20]):
            tree.insert("", "end", values=list(row.values()))

    import_btn = tk.Button(
        data_frame,
        text="Import CSV File",
        font=("Segoe UI", 13, "bold"),
        bg="#4CAF50",
        fg="white",
        activebackground="#45a049",
        padx=10,
        pady=5,
        command=import_csv
    )
    import_btn.pack(pady=10)

    # Table area
    table_frame = tk.Frame(data_frame)
    table_frame.pack(fill="both", expand=True, pady=10)

    tree = ttk.Treeview(table_frame, show="headings")
    tree.pack(fill="both", expand=True)

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    scrollbar.pack(side="right", fill="y")
    tree.configure(yscroll=scrollbar.set)

    root.mainloop()


if __name__ == "__main__":
    run_ui()
