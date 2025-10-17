import tkinter as tk
from tkinter import ttk

from utils import validate_float_range, custom_messagebox


class MergePageGridDialog(tk.Toplevel):
    PAPER_FORMATS = {
        'A0': (841, 1189),
        'A1': (594, 841),
        'A2': (420, 594),
        'A3': (297, 420),
        'A4': (210, 297),
        'A5': (148, 210),
        'A6': (105, 148),
    }
    
    DEFAULTS = {
        'sheet_format': 'A4',
        'orientation': 'Pionowa',
        'margin_top_mm': '5',
        'margin_bottom_mm': '5',
        'margin_left_mm': '5',
        'margin_right_mm': '5',
        'spacing_x_mm': '10',
        'spacing_y_mm': '10',
        'dpi_var': '300',
    }

    def __init__(self, parent, page_count, prefs_manager=None):
        super().__init__(parent)
        self.title("Scalanie strony na arkuszu")
        self.transient(parent)
        self.result = None
        self.prefs_manager = prefs_manager
        
        # Pozycjonuj poza ekranem, aby uniknąć migotania
        self.geometry("+10000+10000")

        self.configure(bg=parent.cget('bg'))

        self.sheet_format = tk.StringVar(value=self._get_pref('sheet_format'))
        self.orientation = tk.StringVar(value=self._get_pref('orientation'))
        self.margin_top_mm = tk.StringVar(value=self._get_pref('margin_top_mm'))
        self.margin_bottom_mm = tk.StringVar(value=self._get_pref('margin_bottom_mm'))
        self.margin_left_mm = tk.StringVar(value=self._get_pref('margin_left_mm'))
        self.margin_right_mm = tk.StringVar(value=self._get_pref('margin_right_mm'))
        self.spacing_x_mm = tk.StringVar(value=self._get_pref('spacing_x_mm'))
        self.spacing_y_mm = tk.StringVar(value=self._get_pref('spacing_y_mm'))
        self.rows_var = tk.StringVar()
        self.cols_var = tk.StringVar()
        self.dpi_var = tk.StringVar(value=self._get_pref('dpi_var'))
        self.page_count = page_count

        self.vcmd_200 = (self.register(lambda v: validate_float_range(v, 0, 200)), "%P")
        self.grid_range = [str(i) for i in range(1, 11)]

        if page_count == 1:
            self.rows_var.set("1")
            self.cols_var.set("1")
        else:
            import math
            sq = min(max(math.ceil(page_count ** 0.5), 1), 10)
            if (sq - 1) * sq >= page_count:
                self.rows_var.set(str(min(max(sq - 1, 1), 10)))
                self.cols_var.set(str(min(max(sq, 1), 10)))
            else:
                self.rows_var.set(str(min(max(sq, 1), 10)))
                self.cols_var.set(str(min(max(sq, 1), 10)))

        self.build_ui()
        self._update_grid_preview()
        self.center_dialog(parent)
        self.grab_set()
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.resizable(False, False)
        self.bind("<Return>", lambda e: self.ok())
        self.bind("<KP_Enter>", lambda e: self.ok())
        self.bind("<Escape>", lambda e: self.cancel())
        self.wait_window(self)

    def _combo_key_num(self, combo, var, event):
        if event.char in "123456789":
            var.set(event.char)
            combo.event_generate('<<ComboboxSelected>>')
        elif event.char == "0":
            var.set("10")
            combo.event_generate('<<ComboboxSelected>>')

    def build_ui(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side="left", fill="y", expand=False, padx=(0, 10))
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side="left", fill="both", expand=True)

        format_frame = ttk.LabelFrame(left_frame, text="Arkusz docelowy")
        format_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(format_frame, text="Format:").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        format_combo = ttk.Combobox(
            format_frame,
            textvariable=self.sheet_format,
            values=list(self.PAPER_FORMATS.keys()),
            state="readonly",
            width=8
        )
        format_combo.grid(row=0, column=1, sticky="w", padx=4, pady=4)
        format_combo.bind("<<ComboboxSelected>>", lambda e: self._update_grid_preview())
        orient_label = ttk.Label(format_frame, text="Orientacja:")
        orient_label.grid(row=1, column=0, sticky="e", padx=4, pady=4)
        orient_radio_frame = ttk.Frame(format_frame)
        orient_radio_frame.grid(row=1, column=1, sticky="w", padx=4, pady=4)
        orient_pion = ttk.Radiobutton(orient_radio_frame, text="Pionowa", variable=self.orientation, value="Pionowa", command=self._update_grid_preview)
        orient_pion.pack(side="left", padx=(0,8))
        orient_poz = ttk.Radiobutton(orient_radio_frame, text="Pozioma", variable=self.orientation, value="Pozioma", command=self._update_grid_preview)
        orient_poz.pack(side="left")

        margin_frame = ttk.LabelFrame(left_frame, text="Marginesy [mm]")
        margin_frame.pack(fill="x", pady=8)
        ttk.Label(margin_frame, text="Górny:").grid(row=0, column=0, sticky="w", padx=4, pady=2)
        ttk.Entry(margin_frame, textvariable=self.margin_top_mm, width=6, validate="key", validatecommand=self.vcmd_200).grid(row=0, column=1, sticky="w", padx=2, pady=2)
        ttk.Label(margin_frame, text="Dolny:").grid(row=0, column=2, sticky="w", padx=4, pady=2)
        ttk.Entry(margin_frame, textvariable=self.margin_bottom_mm, width=6, validate="key", validatecommand=self.vcmd_200).grid(row=0, column=3, sticky="w", padx=2, pady=2)
        ttk.Label(margin_frame, text="Lewy:").grid(row=1, column=0, sticky="w", padx=4, pady=2)
        ttk.Entry(margin_frame, textvariable=self.margin_left_mm, width=6, validate="key", validatecommand=self.vcmd_200).grid(row=1, column=1, sticky="w", padx=2, pady=2)
        ttk.Label(margin_frame, text="Prawy:").grid(row=1, column=2, sticky="w", padx=4, pady=2)
        ttk.Entry(margin_frame, textvariable=self.margin_right_mm, width=6, validate="key", validatecommand=self.vcmd_200).grid(row=1, column=3, sticky="w", padx=2, pady=2)
        ttk.Label(margin_frame, text="Zakres: 0–200 mm", foreground="gray").grid(row=2, column=0, columnspan=4, sticky="w", padx=4, pady=(3,2))

        spacing_frame = ttk.LabelFrame(left_frame, text="Odstępy [mm]")
        spacing_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(spacing_frame, text="Między kolumnami:").grid(row=0, column=0, sticky="w", padx=4, pady=2)
        ttk.Entry(spacing_frame, textvariable=self.spacing_x_mm, width=6, validate="key", validatecommand=self.vcmd_200).grid(row=0, column=1, sticky="w", padx=2, pady=2)
        ttk.Label(spacing_frame, text="Między wierszami:").grid(row=1, column=0, sticky="w", padx=4, pady=2)
        ttk.Entry(spacing_frame, textvariable=self.spacing_y_mm, width=6, validate="key", validatecommand=self.vcmd_200).grid(row=1, column=1, sticky="w", padx=2, pady=2)
        ttk.Label(spacing_frame, text="Zakres: 0–200 mm", foreground="gray").grid(row=2, column=0, columnspan=2, sticky="w", padx=4, pady=(2,2))

        # NOWY WYBÓR DPI
        dpi_frame = ttk.LabelFrame(left_frame, text="Rozdzielczość eksportu (DPI)")
        dpi_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(dpi_frame, text="DPI:").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        dpi_combo = ttk.Combobox(
            dpi_frame,
            textvariable=self.dpi_var,
            values=["72", "150", "300", "600"],
            state="readonly",
            width=6
        )
        dpi_combo.grid(row=0, column=1, sticky="w", padx=2, pady=4)

        grid_frame = ttk.LabelFrame(left_frame, text="Siatka stron")
        grid_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(grid_frame, text="Wiersze:").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.rows_combo = ttk.Combobox(grid_frame, textvariable=self.rows_var, values=self.grid_range, width=5, state="readonly", justify="center")
        self.rows_combo.grid(row=0, column=1, sticky="w", padx=2, pady=4)
        self.rows_combo.bind("<Key>", lambda e: self._combo_key_num(self.rows_combo, self.rows_var, e))
        ttk.Label(grid_frame, text="Kolumny:").grid(row=0, column=2, sticky="w", padx=4, pady=4)
        self.cols_combo = ttk.Combobox(grid_frame, textvariable=self.cols_var, values=self.grid_range, width=5, state="readonly", justify="center")
        self.cols_combo.grid(row=0, column=3, sticky="w", padx=2, pady=4)
        self.cols_combo.bind("<Key>", lambda e: self._combo_key_num(self.cols_combo, self.cols_var, e))
        self.rows_var.trace_add("write", lambda *a: self._update_grid_preview())
        self.cols_var.trace_add("write", lambda *a: self._update_grid_preview())
        
        # Dodaj trace dla marginesów i odstępów, aby podgląd aktualizował się natychmiast
        self.margin_top_mm.trace_add("write", lambda *a: self._update_grid_preview())
        self.margin_bottom_mm.trace_add("write", lambda *a: self._update_grid_preview())
        self.margin_left_mm.trace_add("write", lambda *a: self._update_grid_preview())
        self.margin_right_mm.trace_add("write", lambda *a: self._update_grid_preview())
        self.spacing_x_mm.trace_add("write", lambda *a: self._update_grid_preview())
        self.spacing_y_mm.trace_add("write", lambda *a: self._update_grid_preview())

        preview_frame = ttk.LabelFrame(right_frame, text="Podgląd rozkładu stron")
        preview_frame.pack(fill="both", expand=True)
        self.PREVIEW_W = 320
        self.PREVIEW_H = 450
        self.PREVIEW_PAD = 20
        self.preview_canvas = tk.Canvas(
            preview_frame,
            width=self.PREVIEW_W,
            height=self.PREVIEW_H,
            bg=self.cget('bg'),
            highlightthickness=0
        )
        self.preview_canvas.pack(padx=0, pady=0, fill="both", expand=True)

        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", padx=16, pady=(0, 12), side="bottom")
        ttk.Button(button_frame, text="Zastosuj", command=self.ok).pack(side="left", expand=True, padx=5)
        ttk.Button(button_frame, text="Domyślne", command=self.restore_defaults).pack(side="left", expand=True, padx=5)
        ttk.Button(button_frame, text="Anuluj", command=self.cancel).pack(side="right", expand=True, padx=5)
    
    def _get_pref(self, key):
        """Pobiera preferencję dla tego dialogu"""
        if self.prefs_manager:
            return self.prefs_manager.get(f'MergePageGridDialog.{key}', self.DEFAULTS.get(key, ''))
        return self.DEFAULTS.get(key, '')
    
    def _save_prefs(self):
        """Zapisuje obecne wartości do preferencji"""
        if self.prefs_manager:
            self.prefs_manager.set('MergePageGridDialog.sheet_format', self.sheet_format.get())
            self.prefs_manager.set('MergePageGridDialog.orientation', self.orientation.get())
            self.prefs_manager.set('MergePageGridDialog.margin_top_mm', self.margin_top_mm.get())
            self.prefs_manager.set('MergePageGridDialog.margin_bottom_mm', self.margin_bottom_mm.get())
            self.prefs_manager.set('MergePageGridDialog.margin_left_mm', self.margin_left_mm.get())
            self.prefs_manager.set('MergePageGridDialog.margin_right_mm', self.margin_right_mm.get())
            self.prefs_manager.set('MergePageGridDialog.spacing_x_mm', self.spacing_x_mm.get())
            self.prefs_manager.set('MergePageGridDialog.spacing_y_mm', self.spacing_y_mm.get())
            self.prefs_manager.set('MergePageGridDialog.dpi_var', self.dpi_var.get())
    
    def restore_defaults(self):
        """Przywraca wartości domyślne"""
        self.sheet_format.set(self.DEFAULTS['sheet_format'])
        self.orientation.set(self.DEFAULTS['orientation'])
        self.margin_top_mm.set(self.DEFAULTS['margin_top_mm'])
        self.margin_bottom_mm.set(self.DEFAULTS['margin_bottom_mm'])
        self.margin_left_mm.set(self.DEFAULTS['margin_left_mm'])
        self.margin_right_mm.set(self.DEFAULTS['margin_right_mm'])
        self.spacing_x_mm.set(self.DEFAULTS['spacing_x_mm'])
        self.spacing_y_mm.set(self.DEFAULTS['spacing_y_mm'])
        self.dpi_var.set(self.DEFAULTS['dpi_var'])
        self._update_grid_preview()

    def _get_sheet_dimensions(self):
        sf = self.sheet_format.get()
        sheet_w, sheet_h = self.PAPER_FORMATS.get(sf, (210, 297))
        if self.orientation.get() == "Pozioma":
            return sheet_h, sheet_w
        return sheet_w, sheet_h

    def _update_grid_preview(self):
        try:
            num_pages = self.page_count
            margin_top = float(self.margin_top_mm.get().replace(",", "."))
            margin_bottom = float(self.margin_bottom_mm.get().replace(",", "."))
            margin_left = float(self.margin_left_mm.get().replace(",", "."))
            margin_right = float(self.margin_right_mm.get().replace(",", "."))
            spacing_x = float(self.spacing_x_mm.get().replace(",", "."))
            spacing_y = float(self.spacing_y_mm.get().replace(",", "."))
            rows = int(self.rows_var.get())
            cols = int(self.cols_var.get())
            sheet_w, sheet_h = self._get_sheet_dimensions()

            preview_area_w = self.PREVIEW_W - 2 * self.PREVIEW_PAD
            preview_area_h = self.PREVIEW_H - 2 * self.PREVIEW_PAD
            scale = min(preview_area_w / sheet_w, preview_area_h / sheet_h)
            width_px = sheet_w * scale
            height_px = sheet_h * scale
            offset_x = (self.PREVIEW_W - width_px) // 2
            offset_y = (self.PREVIEW_H - height_px) // 2
            margin_top_px = margin_top * scale
            margin_left_px = margin_left * scale
            margin_right_px = margin_right * scale
            margin_bottom_px = margin_bottom * scale
            spacing_x_px = spacing_x * scale
            spacing_y_px = spacing_y * scale

            self.preview_canvas.delete("all")
            self.preview_canvas.create_rectangle(
                offset_x, offset_y, offset_x + width_px, offset_y + height_px, fill="white", outline="#bbb", width=1
            )

            if cols == 1:
                cell_w = sheet_w - margin_left - margin_right
            else:
                cell_w = (sheet_w - margin_left - margin_right - (cols - 1) * spacing_x) / cols
            if rows == 1:
                cell_h = sheet_h - margin_top - margin_bottom
            else:
                cell_h = (sheet_h - margin_top - margin_bottom - (rows - 1) * spacing_y) / rows
            cell_w_px = cell_w * scale
            cell_h_px = cell_h * scale

            for r in range(rows):
                for c in range(cols):
                    x0 = offset_x + margin_left_px + c * (cell_w_px + spacing_x_px)
                    y0 = offset_y + margin_top_px + r * (cell_h_px + spacing_y_px)
                    x1 = x0 + cell_w_px
                    y1 = y0 + cell_h_px
                    idx = r * cols + c
                    color = "#d0e6f8" if idx < num_pages else "#f5f5f5"
                    self.preview_canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="#666", width=1)
                    if idx < num_pages:
                        self.preview_canvas.create_text((x0+x1)/2, (y0+y1)/2, text=str(idx + 1), fill="#345", font=("Arial", 11, "bold"))
        except Exception:
            self.preview_canvas.delete("all")

    def center_dialog(self, parent):
        self.update_idletasks()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        dialog_w = self.winfo_width()
        dialog_h = self.winfo_height()
        x = parent_x + (parent_w - dialog_w) // 2
        y = parent_y + (parent_h - dialog_h) // 2
        self.geometry(f"+{x}+{y}")

    def ok(self, event=None):
        try:
            margin_top = float(self.margin_top_mm.get().replace(",", "."))
            margin_bottom = float(self.margin_bottom_mm.get().replace(",", "."))
            margin_left = float(self.margin_left_mm.get().replace(",", "."))
            margin_right = float(self.margin_right_mm.get().replace(",", "."))
            spacing_x = float(self.spacing_x_mm.get().replace(",", "."))
            spacing_y = float(self.spacing_y_mm.get().replace(",", "."))
            if not validate_float_range(self.margin_top_mm.get(), 0, 200):
                raise ValueError("Margines górny musi być z zakresu 0–200 mm.")
            if not validate_float_range(self.margin_bottom_mm.get(), 0, 200):
                raise ValueError("Margines dolny musi być z zakresu 0–200 mm.")
            if not validate_float_range(self.margin_left_mm.get(), 0, 200):
                raise ValueError("Margines lewy musi być z zakresu 0–200 mm.")
            if not validate_float_range(self.margin_right_mm.get(), 0, 200):
                raise ValueError("Margines prawy musi być z zakresu 0–200 mm.")
            if not validate_float_range(self.spacing_x_mm.get(), 0, 200):
                raise ValueError("Odstęp poziomy musi być z zakresu 0–200 mm.")
            if not validate_float_range(self.spacing_y_mm.get(), 0, 200):
                raise ValueError("Odstęp pionowy musi być z zakresu 0–200 mm.")
            rows = int(self.rows_var.get())
            cols = int(self.cols_var.get())
            if not (1 <= rows <= 10 and 1 <= cols <= 10):
                raise ValueError("Liczba wierszy i kolumn musi być z zakresu 1–10.")
            if rows * cols < self.page_count:
                raise ValueError("Liczba komórek siatki musi być nie mniejsza niż liczba scalanych stron.")

            format_name = self.sheet_format.get()
            sheet_dims = self.PAPER_FORMATS[format_name]
            orientation = self.orientation.get()
            if orientation == "Pozioma":
                sheet_dims = (sheet_dims[1], sheet_dims[0])

            self.result = {
                "format_name": format_name,
                "sheet_width_mm": sheet_dims[0],
                "sheet_height_mm": sheet_dims[1],
                "margin_top_mm": margin_top,
                "margin_bottom_mm": margin_bottom,
                "margin_left_mm": margin_left,
                "margin_right_mm": margin_right,
                "spacing_x_mm": spacing_x,
                "spacing_y_mm": spacing_y,
                "rows": rows,
                "cols": cols,
                "orientation": orientation,
                "dpi": int(self.dpi_var.get())
            }
            # Zapisz preferencje przed zamknięciem
            self._save_prefs()
            self.destroy()
        except Exception as e:
            custom_messagebox(self, "Błąd", f"Nieprawidłowe dane: {e}", typ="error")

    def cancel(self, event=None):
        self.result = None
        self.destroy()


# ====================================================================
# DIALOG SCALANIA PLIKÓW PDF
# ====================================================================

