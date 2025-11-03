# main.py
import tkinter as tk
from ui.app import MP3MetadataApp

if __name__ == "__main__":
    root = tk.Tk()
    app = MP3MetadataApp(root)
    root.mainloop()