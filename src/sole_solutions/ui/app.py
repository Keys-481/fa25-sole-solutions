import tkinter as tk
from tkinter import filedialog, messagebox, Entry, Label
from tkinter import ttk
import os

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
        else:
            print(f"CSV file selected: {os.path.basename(file_path)}")

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


    root.mainloop()

if __name__ == "__main__":
    run_ui()
