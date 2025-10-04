import tkinter as tk
from tkinter import OptionMenu, filedialog, messagebox, Entry, Label, ttk
import os
import csv

def run_ui():
    root = tk.Tk()
    root.title("Sole Solutions")
    root.geometry("800x600")

    label = tk.Label(root, text="Welcome to Sole Solutions UI", font=("Arial", 16))
    label.pack(pady=20)

    def import_csv():
        file_path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not file_path:
            return  # user canceled
        if not file_path.lower().endswith(".csv"):
            messagebox.showerror("Invalid File", "Please select a valid .csv file.")
            return

        data = None

        # Try multiple encodings
        for enc in ("utf-8-sig", "utf-16", "latin1"):
            try:
                with open(file_path, newline="", encoding=enc) as f:
                    lines = f.readlines()
                break
            except UnicodeDecodeError:
                lines = None
                continue

        if not lines:
            messagebox.showerror("Error", "Could not read CSV file with common encodings.")
            return

        # Find where the real data starts (line beginning with "Frame")
        start_index = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("Frame"):
                start_index = i
                break

        if start_index == 0:
            messagebox.showerror("Error", "No valid data table found in CSV.")
            return

        # Parse the real data 
        reader = csv.DictReader(lines[start_index:])
        data = [row for row in reader]

        # Example output
        print(f"Parsed {len(data)} valid rows from {os.path.basename(file_path)}")
        for row in data[:3]:
            print(row)

        messagebox.showinfo("Success", "CSV imported and parsed successfully!")

    import_button = tk.Button(
        root,
        text="Import CSV Data",
        font=("Arial", 14),
        width=20,
        height=2,
        command=import_csv
    )
    import_button.pack(pady=10)

    height_label = Label(root, text='Height:', font=("Arial", 12))
    height_label.pack(pady=5)
    height_entry = Entry(root, font=("Arial", 12))
    height_entry.pack(pady=5)


        # --- Weight (lbs) ---
    weight_label = Label(root, text='Weight (lbs):', font=("Arial", 12))
    weight_label.pack(pady=5)
    weight_entry = Entry(root, font=("Arial", 12))
    weight_entry.pack(pady=5)

    # --- Gender (Male/Female) ---
    gender_label = Label(root, text='Gender:', font=("Arial", 12))
    gender_label.pack(pady=5)

    gender_var = tk.StringVar()
    gender_combo = ttk.Combobox(
        root,
        textvariable=gender_var,
        values=["Male", "Female"],
        state="readonly",
        font=("Arial", 12),
        width=22,
    )
    gender_combo.current(0)  # default to "Male" selection
    gender_combo.pack(pady=5)

    dominance = ["Left", "Right", "Both"]

    OptionMenu(root, tk.StringVar(value=dominance[0]), *dominance).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    run_ui()
