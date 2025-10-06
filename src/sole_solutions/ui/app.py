import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import csv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinterdnd2 import DND_FILES, TkinterDnD

def run_ui():
    root = TkinterDnD.Tk() 
    root.title("Sole Solutions: Gait Data Visualizer")
    root.geometry("1200x700")
    root.configure(bg="#f2f2f2")

    data_storage = []  # store imported CSV

    # ===== Left panel: User info + filters =====
    left_frame = tk.Frame(root, bg="#f2f2f2")
    left_frame.pack(side="left", fill="y", padx=20, pady=20)

    # Participant info
    info_frame = tk.LabelFrame(left_frame, text="Participant Info", bg="#ffffff", padx=10, pady=10)
    info_frame.pack(fill="x", pady=10)
    tk.Label(info_frame, text="Height (cm):").grid(row=0, column=0, sticky="w")
    height_entry = tk.Entry(info_frame)
    height_entry.grid(row=0, column=1)

    tk.Label(info_frame, text="Weight (kg):").grid(row=1, column=0, sticky="w")
    weight_entry = tk.Entry(info_frame)
    weight_entry.grid(row=1, column=1)

    tk.Label(info_frame, text="Gender:").grid(row=2, column=0, sticky="w")
    gender_combo = ttk.Combobox(info_frame, values=["Male", "Female", "Unspecified"], state="readonly")
    gender_combo.grid(row=2, column=1)
    gender_combo.current(0)

    tk.Label(info_frame, text="Foot Dominance:").grid(row=3, column=0, sticky="w")
    dominance_combo = ttk.Combobox(info_frame, values=["Left", "Right", "Both"], state="readonly")
    dominance_combo.grid(row=3, column=1)
    dominance_combo.current(0)

    # Filters
    filter_frame = tk.LabelFrame(left_frame, text="Filters", bg="#ffffff", padx=10, pady=10)
    filter_frame.pack(fill="x", pady=10)

    tk.Label(filter_frame, text="Select Subject:").grid(row=0, column=0, sticky="w")
    subject_combo = ttk.Combobox(filter_frame, values=[], state="readonly")
    subject_combo.grid(row=0, column=1)

    tk.Label(filter_frame, text="Select Trial:").grid(row=1, column=0, sticky="w")
    trial_combo = ttk.Combobox(filter_frame, values=[], state="readonly")
    trial_combo.grid(row=1, column=1)

    # ===== Right panel: Table + Visualization =====
    right_frame = tk.Frame(root, bg="#f2f2f2")
    right_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)

    # Table area
    table_frame = tk.Frame(right_frame)
    table_frame.pack(fill="both", expand=True, pady=10)

    tree = ttk.Treeview(table_frame, show="headings")
    tree.pack(side="left", fill="both", expand=True)

    # Scrollbars
    v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    v_scrollbar.pack(side="right", fill="y")
    tree.configure(yscroll=v_scrollbar.set)

    h_scrollbar = ttk.Scrollbar(right_frame, orient="horizontal", command=tree.xview)
    h_scrollbar.pack(fill="x")
    tree.configure(xscrollcommand=h_scrollbar.set)

    # Matplotlib figure for visualization
    fig, ax = plt.subplots(figsize=(5, 3))
    canvas = FigureCanvasTkAgg(fig, master=right_frame)
    canvas.get_tk_widget().pack(fill="both", expand=True, pady=20)

    # ===== Functions =====
    def update_subjects_trials():
        subjects = sorted(list(set(row["Subject"] for row in data_storage)))
        subject_combo["values"] = subjects
        if subjects:
            subject_combo.current(0)
            update_trials()

    def update_trials(*args):
        selected_subject = subject_combo.get()
        trials = sorted(list(set(row["Trial"] for row in data_storage if row["Subject"] == selected_subject)))
        trial_combo["values"] = trials
        if trials:
            trial_combo.current(0)
            update_table_and_plot()

    def import_csv(file_path=None):
        if file_path is None:  # only open file dialog if no path was provided
            file_path = filedialog.askopenfilename(title="Select CSV", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

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

        # detect header
        start_index = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("Frame") or line.strip().startswith("Subject"):
                start_index = i
                break

        reader = csv.DictReader(lines[start_index:])
        data_storage.clear()
        data_storage.extend([row for row in reader])

        messagebox.showinfo("Import Complete", f"{len(data_storage)} rows imported")
        update_subjects_trials()

    def update_table_and_plot(*args):
        selected_subject = subject_combo.get()
        selected_trial = trial_combo.get()
        filtered = [
            row for row in data_storage
            if row["Subject"] == selected_subject and row["Trial"] == selected_trial
        ]

        # Update table
        tree.delete(*tree.get_children())
        if filtered:
            tree["columns"] = list(filtered[0].keys())
            for col in tree["columns"]:
                tree.heading(col, text=col)
            for row in filtered[:20]:
                tree.insert("", "end", values=[row[c] for c in tree["columns"]])

        # Plot example: PeakPressure_Left vs Time
        ax.clear()
        if filtered:
            times = [float(row["Time"]) for row in filtered]
            pressures = [float(row["PeakPressure_Left"]) for row in filtered]
            ax.plot(times, pressures, label="PeakPressure_Left")
            ax.set_xlabel("Time")
            ax.set_ylabel("Peak Pressure (kPa)")
            ax.legend()
        canvas.draw()

    # Bind combobox changes
    subject_combo.bind("<<ComboboxSelected>>", update_trials)
    trial_combo.bind("<<ComboboxSelected>>", update_table_and_plot)

    # Buttons
    import_btn = tk.Button(left_frame, text="Import CSV", bg="#4CAF50", fg="white", command=import_csv)
    import_btn.pack(pady=10)

    
    drop_frame = tk.Label(
    left_frame,
    text="Or drag & drop CSV here",
    bg="#d9edf7",
    fg="#31708f",
    relief="ridge",
    width=25,
    height=5
)
    drop_frame.pack(pady=20)

    # Bind the drop event
    def drop(event):
        files = root.splitlist(event.data)  # handles multiple files
        if files:
            import_csv(files[0])  # call your existing import_csv function with the path

    drop_frame.drop_target_register(DND_FILES)
    drop_frame.dnd_bind("<<Drop>>", drop)


    root.mainloop()


if __name__ == "__main__":
    run_ui()
