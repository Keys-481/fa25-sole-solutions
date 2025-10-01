import tkinter as tk

def run_ui():
    root = tk.Tk()
    root.title("Sole Solutions")
    root.geometry("800x600")

    label = tk.Label(root, text="Welcome to Sole Solutions UI", font=("Arial", 16))
    label.pack(pady=20)

    import_button = tk.Button(
        root,
        text="Import CSV Data",
        font=("Arial", 14),
        width=20,
        height=2,
        command=lambda: print("Import CSV button clicked!")  # placeholder action
    )
    import_button.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    run_ui()
