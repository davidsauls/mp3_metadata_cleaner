# ui/components.py
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from io import BytesIO
import requests
import threading

def create_metadata_panel(parent, title, bg_color="#f8f9ff"):
    frame = tk.LabelFrame(parent, text=title, bg=bg_color, fg="#667eea",
                          font=("Arial", 14, "bold"), padx=10, pady=10)
    return frame

def load_artwork_async(parent, url):
    def fetch():
        try:
            resp = requests.get(url, timeout=8)
            img = Image.open(BytesIO(resp.content)).resize((200, 200), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            lbl = tk.Label(parent, image=photo, bg="#f8f9ff")
            lbl.image = photo
            lbl.pack(pady=8)
        except Exception:
            tk.Label(parent, text="(No image)", fg="gray").pack(pady=8)
    threading.Thread(target=fetch, daemon=True).start()

def add_metadata_fields(parent, metadata, is_apple, mismatches=None):
    fields = [
        ('Title', metadata['title']),
        ('Artist', metadata['artist']),
        ('Album', metadata['album']),
        ('Year', metadata['year']),
        ('Genre', metadata['genre']),
        ('Track Number', metadata['track']),
        ('Duration', metadata['duration'])
    ]

    for label, value in fields:
        key = label.lower().replace(' ', '_').replace('number', '')
        bg = "#f8d7da" if (not is_apple and mismatches and key in mismatches) else "white"
        row = tk.Frame(parent, bg=bg, relief="ridge", bd=1)
        row.pack(fill="x", pady=1)
        tk.Label(row, text=f"{label}:", font=("Arial", 9, "bold"), bg=bg, fg="black").pack(side="left", padx=5)
        tk.Label(row, text=str(value), font=("Arial", 9), bg=bg, fg="gray").pack(side="left", padx=5)

    # === ARTWORK ===
    art_data = metadata.get('cover_art_data') if not is_apple else None
    art_url = metadata.get('album_art_url') if is_apple else None

    artwork_frame = tk.Frame(parent, bg="#f8f9ff")
    artwork_frame.pack(pady=8, fill="x")

    if not is_apple and art_data:
        # --- MP3: Show embedded cover ---
        try:
            img = Image.open(BytesIO(art_data))
            # Validate image
            img.verify()
            img = Image.open(BytesIO(art_data))  # Re-open after verify
            img = img.convert("RGB")
            img = img.resize((200, 200), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            lbl = tk.Label(artwork_frame, image=photo, bg="#f8f9ff")
            lbl.image = photo
            lbl.pack()
        except Exception as e:
            debug_log(f"Failed to load MP3 cover art: {e}")
            tk.Label(artwork_frame, text="(Corrupted image)", fg="red", font=("Arial", 9)).pack()

    elif is_apple and art_url:
        # --- Apple: Load async ---
        load_artwork_async(artwork_frame, art_url)

    else:
        # --- No art ---
        tk.Label(artwork_frame, text="(No cover art)", fg="gray", font=("Arial", 9, "italic")).pack()

def add_confidence_badge(parent, score):
    color = "#2ecc71" if score >= 85 else "#f39c12" if score >= 70 else "#e74c3c"
    text = f"{score}% Match"
    badge = tk.Label(parent, text=text, bg=color, fg="white", font=("Arial", 9, "bold"), padx=6, pady=2)
    badge.pack(anchor="e", pady=2)
    return badge