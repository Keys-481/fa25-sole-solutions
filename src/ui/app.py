import tkinter as tk

def run_ui():
    root = tk.Tk()
    root.title("Sole Solutions")
    root.geometry("800x600")

    label = tk.Label(root, text="Welcome to Sole Solutions UI", font=("Arial", 16))
    label.pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    run_ui()
