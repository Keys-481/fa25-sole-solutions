import tkinter as tk
from tkinter import filedialog, messagebox
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

    root.mainloop()

if __name__ == "__main__":
    run_ui()
