#gaurd to stop tk errors in environments without tkinter
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, Entry, Label
    from tkinter import ttk  # if you use ttk
except Exception:  # ImportError or _tkinter missing, etc.
    tk = None
    filedialog = messagebox = Entry = Label = None
    ttk = None

import os

def run_ui():
    if tk is None:
        raise RuntimeError("Tkinter is not available in this environment.")
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

    root.mainloop()

if __name__ == "__main__":
    run_ui()
