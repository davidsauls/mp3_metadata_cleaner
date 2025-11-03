# ui/app.py
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import concurrent.futures
import os
import requests
from PIL import Image, ImageTk
from io import BytesIO

from metadata.mp3_reader import read_mp3_metadata
from metadata.apple_music import search_apple_music
from metadata.tag_updater import update_mp3_metadata
from utils.helpers import debug_log
from ui.components import create_metadata_panel, add_metadata_fields, add_confidence_badge


class MP3MetadataApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MP3 Apple Music Metadata Tool")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")

        self.file_list = []
        self.current_idx = 0
        self.is_folder_mode = False
        self.mp3_meta = None
        self.apple_results = []
        self.selected_apple = None
        self.content = None  # Will be set in setup_ui

        self.setup_ui()

    def setup_ui(self):
        # ==================== HEADER ====================
        header = tk.Frame(self.root, bg="#667eea", height=80)
        header.pack(fill="x", padx=20, pady=10)
        header.pack_propagate(False)

        title_frame = tk.Frame(header, bg="#667eea")
        title_frame.pack(side="left", expand=True, fill="both")
        tk.Label(title_frame, text="MP3 Metadata Tool", font=("Arial", 24, "bold"),
                 fg="white", bg="#667eea").pack(anchor="w", padx=20, pady=12)

        btns = tk.Frame(header, bg="#667eea")
        btns.pack(side="right", pady=10, padx=20)
        tk.Button(btns, text="Single File", command=self.select_single, bg="white", fg="#667eea").pack(side="left", padx=5)
        tk.Button(btns, text="Folder", command=self.select_folder, bg="white", fg="#667eea").pack(side="left", padx=5)
        tk.Button(btns, text="Batch", command=self.batch_process, bg="white", fg="#667eea").pack(side="left", padx=5)

        # ==================== MAIN CONTENT ====================
        self.content = tk.Frame(self.root, bg="white")
        self.content.pack(fill="both", expand=True, padx=20, pady=10)

        self.status = tk.Label(self.content, text="", bg="white", anchor="w", font=("Arial", 10))
        self.status.pack(fill="x", pady=5)

        # --- Search Results ---
        self.results_frame = tk.Frame(self.content, bg="white")
        self.results_frame.pack(fill="x", pady=10)

        self.results_label = tk.Label(self.results_frame, text="Select file(s) above",
                                      fg="#667eea", font=("Arial", 14, "bold"), bg="white")
        self.results_label.pack(anchor="w")

        tree_frame = tk.Frame(self.results_frame)
        tree_frame.pack(fill="both", expand=True)

        cols = ('confidence', 'title', 'artist', 'album', 'year', 'duration')
        self.tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=8)
        self.tree.heading('confidence', text='%')
        self.tree.column('confidence', width=50, anchor='center')
        for c in cols:
            w = 80 if c in ('year', 'duration') else 180
            self.tree.column(c, width=w, stretch=True)
            self.tree.heading(c, text=c.title())
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # --- Action Buttons ---
        self.action_frame = tk.Frame(self.content, bg="white")
        self.action_frame.pack(fill="x", pady=10)
        self.action_frame.pack_forget()

        # --- Comparison ---
        self.compare_frame = tk.Frame(self.content, bg="white")
        self.compare_frame.pack(fill="both", expand=True, pady=10)

        # --- Batch Results ---
        self.batch_frame = tk.Frame(self.content, bg="white")
        self.batch_tree = ttk.Treeview(self.batch_frame,
                                      columns=('File', 'Status'), show='headings', height=12)
        self.batch_tree.heading('File', text='File')
        self.batch_tree.heading('Status', text='Status')
        self.batch_tree.column('File', width=400)
        self.batch_tree.column('Status', width=150)
        self.batch_tree.pack(fill="both", expand=True)
        self.batch_frame.pack(fill="both", expand=True, pady=10)
        self.batch_frame.pack_forget()

    # ------------------------------------------------------------------
    def select_single(self):
        path = filedialog.askopenfilename(filetypes=[("MP3 files", "*.mp3")])
        if path:
            self.file_list = [path]
            self.is_folder_mode = False
            self.current_idx = 0
            self.process_file()

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.file_list = [
                os.path.join(r, f)
                for r, _, fs in os.walk(folder)
                for f in fs if f.lower().endswith('.mp3')
            ]
            self.is_folder_mode = True
            self.current_idx = 0
            if self.file_list:
                self.process_file()
            else:
                messagebox.showerror("Error", "No MP3 files found in the folder.")

    def process_file(self):
        if self.current_idx >= len(self.file_list):
            self.status.config(text="All files processed.") # Message for FOLDER scenario
            self.action_frame.pack_forget()
            # No button — just status
            return

        self.status.config(text="Loading MP3...")
        threading.Thread(target=self.load_mp3, daemon=True).start()

    def load_mp3(self):
        path = self.file_list[self.current_idx]
        try:
            self.mp3_meta = read_mp3_metadata(path)
            self.root.after(0, self.show_mp3_and_search)  # NEW combined
        except Exception as e:
            self.root.after(0, lambda: self.status.config(text=f"Error: {e}"))

    def show_mp3_and_search(self):  # NEW
        # ---- 1. RE-PACK the comparison area (was hidden in update()) ----
        self.compare_frame.pack(fill="both", expand=True, pady=10)

        # ---- 2. Clear old content ----
        for w in self.compare_frame.winfo_children():
            w.destroy()

        # ---- 3. Show MP3 side immediately ----
        right = create_metadata_panel(self.compare_frame, "MP3 File")
        add_metadata_fields(right, self.mp3_meta, is_apple=False)
        right.pack(side="right", fill="both", expand=True, padx=5)

        # ---- 4. Show placeholder on Apple side ----
        left = create_metadata_panel(self.compare_frame, "Apple Music")
        tk.Label(left, text="Searching...", fg="gray", font=("Arial", 10, "italic")).pack(pady=20)
        left.pack(side="left", fill="both", expand=True, padx=5)

        # ---- 5. Start search in background ----
        self.status.config(text="Searching Apple Music...")
        threading.Thread(target=self._do_search, daemon=True).start()

    def _do_search(self):  # NEW
        results = search_apple_music(
            self.mp3_meta['title'], self.mp3_meta['artist'], self.mp3_meta['duration_ms'],
            self.mp3_meta  # PASS FULL!
        )
        self.root.after(0, lambda: self.display_results(results))
        self.root.after(0, lambda: self.status.config(text=""))

    """
    def show_mp3_only(self):
        for w in self.compare_frame.winfo_children():
            w.destroy()
        left = create_metadata_panel(self.compare_frame, "Apple Music")
        tk.Label(left, text="Searching...", fg="gray", font=("Arial", 10, "italic")).pack(pady=20)
        left.pack(side="left", fill="both", expand=True, padx=5)

        right = create_metadata_panel(self.compare_frame, "MP3 File")
        add_metadata_fields(right, self.mp3_meta, is_apple=False)
        right.pack(side="right", fill="both", expand=True, padx=5)

    def search_apple(self):
        results = search_apple_music(
            self.mp3_meta['title'],
            self.mp3_meta['artist'],
            self.mp3_meta['duration_ms']
        )
        self.root.after(0, lambda: self.display_results(results))
    """

    def display_results(self, results):
        self.apple_results = results
        self.tree.delete(*self.tree.get_children())
        self.results_label.config(text=f"Found {len(results)} matches")
        for r in results:
            conf = r.get('confidence', 0)
            iid = self.tree.insert('', 'end', values=(
                conf, r['title'], r['artist'], r['album'], r['year'], r['duration']
            ))
            self.tree.item(iid, tags=('confidence',))

    def on_select(self, _):
        sel = self.tree.selection()
        if sel:
            idx = self.tree.index(sel[0])
            self.selected_apple = self.apple_results[idx]
            self.show_comparison()

    def show_comparison(self):
        self.action_frame.pack(fill="x")
        for w in self.action_frame.winfo_children():
            w.destroy()
        tk.Button(self.action_frame, text="Update Metadata",
                  command=self.update, bg="white", fg="#667eea",
                  font=("Arial", 10), padx=30, pady=5).pack(side="left", padx=10)
        if self.is_folder_mode:
            tk.Button(self.action_frame, text="Next File",
                      command=self.next_file, bg="white", fg="#667eea",
                      font=("Arial", 10), padx=20, pady=5).pack(side="left", padx=10)

        for w in self.compare_frame.winfo_children():
            w.destroy()

        left = create_metadata_panel(self.compare_frame, "Apple Music")
        add_metadata_fields(left, self.selected_apple, is_apple=True)

        from utils.confidence import calculate_confidence
        score, _ = calculate_confidence(self.mp3_meta, self.selected_apple)
        add_confidence_badge(left, score)
        left.pack(side="left", fill="both", expand=True, padx=5)

        mismatches = {
            k for k, v1, v2 in [
                ('title', self.mp3_meta['title'], self.selected_apple['title']),
                ('artist', self.mp3_meta['artist'], self.selected_apple['artist']),
                ('album', self.mp3_meta['album'], self.selected_apple['album']),
                ('year', self.mp3_meta['year'], self.selected_apple['year']),
                ('genre', self.mp3_meta['genre'], self.selected_apple['genre']),
                ('track', self.mp3_meta['track'], self.selected_apple['track']),
                ('duration', self.mp3_meta['duration'], self.selected_apple['duration']),
            ] if str(v1).strip().lower() != str(v2).strip().lower()
        }

        right = create_metadata_panel(self.compare_frame, "MP3 File")
        add_metadata_fields(right, self.mp3_meta, is_apple=False, mismatches=mismatches)
        right.pack(side="right", fill="both", expand=True, padx=5)

    def update(self):
        if update_mp3_metadata(self.mp3_meta['file_path'], self.selected_apple):
            messagebox.showinfo("Success", "Metadata updated!")

            # --- Clear everything ---
            for w in self.compare_frame.winfo_children():
                w.destroy()
            self.compare_frame.pack_forget()

            for w in self.action_frame.winfo_children():
                w.destroy()
            self.action_frame.pack_forget()

            self.tree.delete(*self.tree.get_children())
            self.results_label.config(text="Select file(s) above")
            self.apple_results = []
            self.selected_apple = None

            # --- Only show status ---
            self.status.config(text="Select a single file, folder or batch")

            # NO "Start Over" button!

        else:
            messagebox.showerror("Error", "Update failed.")

    def next_file(self):
        self.current_idx += 1
        self.process_file()

    def batch_process(self):
        if not self.file_list:
            messagebox.showerror("Error", "No files selected.")
            return
        self.batch_frame.pack(fill="both", expand=True, pady=10)
        self.batch_tree.delete(*self.batch_tree.get_children())
        self.status.config(text="Batch processing…")
        threading.Thread(target=self.run_batch, daemon=True).start()

    def run_batch(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as exe:
            futures = {exe.submit(self.batch_one, p): p for p in self.file_list}
            for f in concurrent.futures.as_completed(futures):
                path, status = f.result()
                self.root.after(0, lambda p=path, s=status: self.batch_tree.insert(
                    '', 'end', values=(os.path.basename(p), s)))
        self.root.after(0, lambda: self.status.config(text="Batch complete!"))

    def batch_one(self, path):
        try:
            mp3 = read_mp3_metadata(path)
            results = search_apple_music(
                mp3['title'], 
                mp3['artist'], 
                mp3['duration_ms'], 
                mp3  # ← Pass full metadata
            )
            if not results:
                return path, "No match"

            best = results[0]
            score, _ = calculate_confidence(mp3, best)
            if score >= 85:
                ok = update_mp3_metadata(path, best)
                return path, f"Updated ({score}%)" if ok else "Failed"
            else:
                return path, f"Skipped ({score}%)"
        except Exception as e:
            debug_log(f"Batch error {path}: {e}")
            return path, "Error"

    def reset(self):
        self.file_list = []
        self.current_idx = 0
        self.mp3_meta = None
        self.apple_results = []
        self.selected_apple = None
        self.is_folder_mode = False
        self.tree.delete(*self.tree.get_children())
        self.status.config(text="")
        self.results_label.config(text="Select file(s) above")
        self.compare_frame.pack_forget()
        self.action_frame.pack_forget()
        self.batch_frame.pack_forget()
        for w in self.compare_frame.winfo_children():
            w.destroy()
        for w in self.action_frame.winfo_children():
            w.destroy()