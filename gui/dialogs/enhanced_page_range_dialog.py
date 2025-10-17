import tkinter as tk
from tkinter import ttk

from utils import validate_float_range, custom_messagebox


class EnhancedPageRangeDialog(tk.Toplevel):
    def __init__(self, parent, title, imported_doc):
        super().__init__(parent)
        self.transient(parent)
        self.title(title)
        self.imported_doc = imported_doc
        
        # Pozycjonuj poza ekranem, aby uniknąć migotania
        self.geometry("+10000+10000")

        try:
            self.max_pages = len(imported_doc)
        except ValueError:
            self.max_pages = 0
            custom_messagebox(self.master, "Błąd", "Dokument PDF został zamknięty przed otwarciem dialogu.", typ="error")
            self.destroy()
            self.result = None
            return

        self.result = None

        self.initial_focus = self.body()
        self.buttonbox()
        
        self.update_idletasks()
        
        dialog_width, dialog_height = 300, 155
        parent_x, parent_y = parent.winfo_rootx(), parent.winfo_rooty()
        parent_width, parent_height = parent.winfo_width(), parent.winfo_height()
        x = parent_x + parent_width // 2 - dialog_width // 2
        y = parent_y + parent_height // 2 - dialog_height // 2
        self.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        self.resizable(False, False)
        self.grab_set()

        if self.initial_focus:
            self.initial_focus.focus_set()

        self.wait_window(self)

    def body(self):
        main_frame = ttk.Frame(self, padding=(10, 10))
        main_frame.pack(fill="both")

        range_frame = ttk.LabelFrame(main_frame, text="Zakres stron do importu", padding=(10, 8))
        range_frame.pack(fill='x', pady=(0, 2))

        label = ttk.Label(
            range_frame,
            text=f"Podaj strony z zakresu [1 - {self.max_pages}]:",
            anchor="w"
        )
        label.grid(row=0, column=0, sticky="w", pady=(0, 2))

        self.entry = ttk.Entry(range_frame, width=18)
        self.entry.insert(0, f"1-{self.max_pages}")
        self.entry.grid(row=1, column=0, sticky="we", pady=(0, 0))

        helper = ttk.Label(
            range_frame,
            text="Format: 1, 3-5, 7",
            foreground="gray"
        )
        helper.grid(row=2, column=0, sticky="w", pady=(2, 0))

        range_frame.columnconfigure(0, weight=1)

        return self.entry

    def buttonbox(self):
        # Przycisk importuj/anuluj – tuż pod ramką, bez odstępu od dołu
        box = ttk.Frame(self)
        box.pack(fill=tk.X, pady=(4, 0))
        center = ttk.Frame(box)
        center.pack(anchor="center")
        ttk.Button(center, text="Importuj", width=12, command=self.ok).pack(side=tk.LEFT, padx=14)
        ttk.Button(center, text="Anuluj", width=12, command=self.cancel).pack(side=tk.LEFT, padx=14)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", lambda e: self.cancel())
    
    def ok(self, event=None):
        raw_range = self.entry.get().strip()
        if not raw_range:
            custom_messagebox(self, "Błąd", "Wprowadź zakres stron.", typ="error")
            self.entry.focus_set()
            return

        # 1. Sprawdzenie czy wpisane liczby są z zakresu 1-max_pages i czy zakresy nie są zbyt szerokie
        import re
        nums = []
        MAX_RANGE_LEN = 1000  # zabezpieczenie przed zbyt dużymi przedziałami
        for part in raw_range.split(','):
            part = part.strip()
            if not part:
                continue
            if '-' in part:
                try:
                    start, end = map(int, part.split('-'))
                    if start > end:
                        continue
                    # NOWOŚĆ: sprawdź długość zakresu
                    if end - start + 1 > MAX_RANGE_LEN:
                        custom_messagebox(
                            self, "Błąd zakresu",
                            f"Zakres {start}-{end} jest zbyt szeroki (max {MAX_RANGE_LEN} stron w jednym zakresie).",
                            typ="error"
                        )
                        self.entry.focus_set()
                        return
                    for n in range(start, end + 1):
                        nums.append(n)
                except Exception:
                    continue
            else:
                try:
                    nums.append(int(part))
                except Exception:
                    continue
        too_large = [n for n in nums if n < 1 or n > self.max_pages]
        if too_large:
            custom_messagebox(
                self, "Błąd zakresu",
            #    f"Podano numery spoza zakresu 1-{self.max_pages}: {', '.join(map(str, too_large))}",
                f"Podano numery spoza zakresu 1-{self.max_pages}",
                typ="error"
            )
            self.entry.focus_set()
            return

        page_indices = self._parse_range(raw_range)
        if page_indices is None or len(page_indices) == 0:
            custom_messagebox(self, "Błąd formatu", "Niepoprawny format zakresu. Użyj np. 1, 3-5, 7.", typ="error")
            self.entry.focus_set()
            return

        self.result = page_indices
        self.destroy()
    
    def cancel(self, event=None):
        self.result = None
        self.destroy()

    def _parse_range(self, raw_range: str) -> Optional[List[int]]:
        selected_pages = set()
        if not re.fullmatch(r'[\d,\-\s]+', raw_range):
            return None
        parts = raw_range.split(',')
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if '-' in part:
                try:
                    start, end = map(int, part.split('-'))
                    start = max(1, start)
                    end = min(self.max_pages, end)
                    if start > end:
                        continue
                    for page_num in range(start, end + 1):
                        selected_pages.add(page_num - 1)
                except ValueError:
                    return None
            else:
                try:
                    page_num = int(part)
                    if 1 <= page_num <= self.max_pages:
                        selected_pages.add(page_num - 1)
                except ValueError:
                    return None
        return sorted(list(selected_pages))

# ====================================================================
# KLASA: RAMKA MINIATURY (Bez zmian)
# ====================================================================

class ThumbnailFrame(tk.Frame):
    def __init__(self, parent, viewer_app, page_index, column_width):
        super().__init__(parent, bg="#F5F5F5") 
        self.page_index = page_index
        self.viewer_app = viewer_app
        self.column_width = column_width
        self.bg_normal = "#F5F5F5"
        self.bg_selected = "#B3E5FC"
        self.outer_frame = tk.Frame(
            self, 
            bg=self.bg_normal, 
            borderwidth=0, 
            relief=tk.FLAT,
            highlightthickness=FOCUS_HIGHLIGHT_WIDTH, 
            highlightbackground=self.bg_normal 
        )
        self.outer_frame.pack(fill="both", expand=True, padx=0, pady=0)
        self.img_label = None 
        self.setup_ui(self.outer_frame)

    def _bind_all_children(self, sequence, func):
        self.bind(sequence, func)
        self.outer_frame.bind(sequence, func)
        for child in self.outer_frame.winfo_children():
            child.bind(sequence, func)
            if child.winfo_class() == 'Frame':
                 for grandchild in child.winfo_children():
                     grandchild.bind(sequence, func)


    def setup_ui(self, parent_frame):
        img_tk = self.viewer_app._render_and_scale(self.page_index, self.column_width)
        # Cache is now handled inside _render_and_scale
        
        image_container = tk.Frame(parent_frame, bg="white") 
        image_container.pack(padx=5, pady=(5, 0))
        
        self.img_label = tk.Label(image_container, image=img_tk, bg="white")
        self.img_label.pack() 
        
        tk.Label(parent_frame, text=f"Strona {self.page_index + 1}", bg=self.bg_normal, font=("Helvetica", 10, "bold")).pack(pady=(5, 0))
        
        format_label = self.viewer_app._get_page_size_label(self.page_index)
        tk.Label(parent_frame, text=format_label, fg="gray", bg=self.bg_normal, font=("Helvetica", 9)).pack(pady=(0, 5))

        self._bind_all_children("<Button-1>", lambda event, idx=self.page_index: self.viewer_app._handle_lpm_click(idx, event))

        self._bind_all_children("<Button-3>", lambda event, idx=self.page_index: self._handle_ppm_click(event, idx))
       # parent_frame.bind("<Enter>", lambda event, idx=self.page_index: self.viewer_app._focus_by_mouse(idx))

    def _handle_ppm_click(self, event, page_index):
        self.viewer_app.active_page_index = page_index
        
        if page_index not in self.viewer_app.selected_pages:
             self.viewer_app.selected_pages.clear()
             self.viewer_app.selected_pages.add(page_index)
             self.viewer_app.update_selection_display()
        
        self.viewer_app.update_focus_display(hide_mouse_focus=False) 
        self.viewer_app.context_menu.tk_popup(event.x_root, event.y_root)

# ====================================================================
# DIALOG SCALANIA STRON NA ARKUSZU
# ====================================================================

