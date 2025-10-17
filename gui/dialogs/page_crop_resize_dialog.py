import tkinter as tk
from tkinter import ttk

from utils import validate_float_range, custom_messagebox


class PageCropResizeDialog(tk.Toplevel):
    PAPER_FORMATS = {
        'A0': (841, 1189),
        'A1': (594, 841),
        'A2': (420, 594),
        'A3': (297, 420),
        'A4': (210, 297),
        'A5': (148, 210),
        'A6': (105, 148),
        'Niestandardowy': (0, 0)
    }
    
    DEFAULTS = {
        'crop_mode': 'nocrop',
        'margin_top': '10',
        'margin_bottom': '10',
        'margin_left': '10',
        'margin_right': '10',
        'resize_mode': 'noresize',
        'target_format': 'A4',
        'custom_width': '',
        'custom_height': '',
        'position_mode': 'center',
        'offset_x': '0',
        'offset_y': '0',
    }

    def __init__(self, parent, prefs_manager=None):
        super().__init__(parent)
        self.title("Kadrowanie i zmiana rozmiaru stron")
        self.transient(parent)
        self.result = None
        self.prefs_manager = prefs_manager
        
        # Pozycjonuj poza ekranem, aby uniknąć migotania
        self.geometry("+10000+10000")

        # Wczytaj ostatnie wartości lub użyj domyślnych
        self.crop_mode = tk.StringVar(value=self._get_pref('crop_mode'))
        self.margin_top = tk.StringVar(value=self._get_pref('margin_top'))
        self.margin_bottom = tk.StringVar(value=self._get_pref('margin_bottom'))
        self.margin_left = tk.StringVar(value=self._get_pref('margin_left'))
        self.margin_right = tk.StringVar(value=self._get_pref('margin_right'))

        self.resize_mode = tk.StringVar(value=self._get_pref('resize_mode'))
        self.target_format = tk.StringVar(value=self._get_pref('target_format'))
        self.custom_width = tk.StringVar(value=self._get_pref('custom_width'))
        self.custom_height = tk.StringVar(value=self._get_pref('custom_height'))
        self.position_mode = tk.StringVar(value=self._get_pref('position_mode'))
        self.offset_x = tk.StringVar(value=self._get_pref('offset_x'))
        self.offset_y = tk.StringVar(value=self._get_pref('offset_y'))

        # Walidatory dla marginesów, rozmiarów i położenia
        self.vcmd_margin = (self.register(lambda v: validate_float_range(v, 0, 200)), "%P")
        self.vcmd_size = (self.register(lambda v: validate_float_range(v, 1, 4000)), "%P")
        self.vcmd_offset = (self.register(lambda v: validate_float_range(v, 0, 500)), "%P")

        self.build_ui()
        self.update_field_states()
        self.center_dialog(parent)
        self.grab_set()
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.resizable(False, False)

        self.bind("<Return>", lambda e: self.ok())
        self.bind("<KP_Enter>", lambda e: self.ok())
        self.bind("<Escape>", lambda e: self.cancel())

        self.wait_window(self)
    
    def _get_pref(self, key):
        """Pobiera preferencję dla tego dialogu"""
        if self.prefs_manager:
            return self.prefs_manager.get(f'PageCropResizeDialog.{key}', self.DEFAULTS.get(key, ''))
        return self.DEFAULTS.get(key, '')
    
    def _save_prefs(self):
        """Zapisuje obecne wartości do preferencji"""
        if self.prefs_manager:
            self.prefs_manager.set('PageCropResizeDialog.crop_mode', self.crop_mode.get())
            self.prefs_manager.set('PageCropResizeDialog.margin_top', self.margin_top.get())
            self.prefs_manager.set('PageCropResizeDialog.margin_bottom', self.margin_bottom.get())
            self.prefs_manager.set('PageCropResizeDialog.margin_left', self.margin_left.get())
            self.prefs_manager.set('PageCropResizeDialog.margin_right', self.margin_right.get())
            self.prefs_manager.set('PageCropResizeDialog.resize_mode', self.resize_mode.get())
            self.prefs_manager.set('PageCropResizeDialog.target_format', self.target_format.get())
            self.prefs_manager.set('PageCropResizeDialog.custom_width', self.custom_width.get())
            self.prefs_manager.set('PageCropResizeDialog.custom_height', self.custom_height.get())
            self.prefs_manager.set('PageCropResizeDialog.position_mode', self.position_mode.get())
            self.prefs_manager.set('PageCropResizeDialog.offset_x', self.offset_x.get())
            self.prefs_manager.set('PageCropResizeDialog.offset_y', self.offset_y.get())
    
    def restore_defaults(self):
        """Przywraca wartości domyślne"""
        self.crop_mode.set(self.DEFAULTS['crop_mode'])
        self.margin_top.set(self.DEFAULTS['margin_top'])
        self.margin_bottom.set(self.DEFAULTS['margin_bottom'])
        self.margin_left.set(self.DEFAULTS['margin_left'])
        self.margin_right.set(self.DEFAULTS['margin_right'])
        self.resize_mode.set(self.DEFAULTS['resize_mode'])
        self.target_format.set(self.DEFAULTS['target_format'])
        self.custom_width.set(self.DEFAULTS['custom_width'])
        self.custom_height.set(self.DEFAULTS['custom_height'])
        self.position_mode.set(self.DEFAULTS['position_mode'])
        self.offset_x.set(self.DEFAULTS['offset_x'])
        self.offset_y.set(self.DEFAULTS['offset_y'])
        self.update_field_states()

        self.wait_window(self)

    def build_ui(self):
        pad = {'padx': 8, 'pady': 4}
        pady_row1 = (0, 6)
        pady_row2 = (0, 0)

        # --- CROP SECTION ---
        crop_frame = ttk.LabelFrame(self, text="Przycinanie strony")
        crop_frame.pack(fill="x", padx=12, pady=(12, 4))

        crop_modes = [
            ("Nie przycinaj", "nocrop"),
            ("Przytnij obraz bez zmiany rozmiaru arkusza", "crop_only"),
            ("Przytnij obraz i dostosuj rozmiar arkusza", "crop_resize"),
        ]
        self.crop_radiobuttons = []
        for txt, val in crop_modes:
            rb = ttk.Radiobutton(crop_frame, text=txt, variable=self.crop_mode, value=val, command=self.update_field_states)
            rb.pack(anchor="w", **pad)
            self.crop_radiobuttons.append(rb)

        margin_frame = ttk.Frame(crop_frame)
        margin_frame.pack(fill="x", padx=12, pady=(4, 0))
        ttk.Label(margin_frame, text="Góra [mm]:").grid(row=0, column=0, sticky="w", padx=(0,6), pady=pady_row1)
        self.e_margin_top = ttk.Entry(margin_frame, textvariable=self.margin_top, width=6, validate="key", validatecommand=self.vcmd_margin)
        self.e_margin_top.grid(row=0, column=1, sticky="w", padx=(0,16), pady=pady_row1)
        ttk.Label(margin_frame, text="Dół [mm]:").grid(row=0, column=2, sticky="w", padx=(0,6), pady=pady_row1)
        self.e_margin_bottom = ttk.Entry(margin_frame, textvariable=self.margin_bottom, width=6, validate="key", validatecommand=self.vcmd_margin)
        self.e_margin_bottom.grid(row=0, column=3, sticky="w", padx=(0,0), pady=pady_row1)

        ttk.Label(margin_frame, text="Lewo [mm]:").grid(row=1, column=0, sticky="w", padx=(0,6), pady=pady_row2)
        self.e_margin_left = ttk.Entry(margin_frame, textvariable=self.margin_left, width=6, validate="key", validatecommand=self.vcmd_margin)
        self.e_margin_left.grid(row=1, column=1, sticky="w", padx=(0,16), pady=pady_row2)
        ttk.Label(margin_frame, text="Prawo [mm]:").grid(row=1, column=2, sticky="w", padx=(0,6), pady=pady_row2)
        self.e_margin_right = ttk.Entry(margin_frame, textvariable=self.margin_right, width=6, validate="key", validatecommand=self.vcmd_margin)
        self.e_margin_right.grid(row=1, column=3, sticky="w", padx=(0,0), pady=pady_row2)
        self.margin_entries = [self.e_margin_top, self.e_margin_bottom, self.e_margin_left, self.e_margin_right]
        # Komunikat zakresu marginesów
        ttk.Label(margin_frame, text="Zakres: 0–200 mm", foreground="gray").grid(row=2, column=0, columnspan=4, sticky="w", pady=(6,0))

        # --- RESIZE SECTION ---
        resize_frame = ttk.LabelFrame(self, text="Zmiana rozmiaru arkusza")
        resize_frame.pack(fill="x", padx=12, pady=8)

        resize_modes = [
            ("Nie zmieniaj rozmiaru", "noresize"),
            ("Zmień rozmiar i skaluj obraz", "resize_scale"),
            ("Zmień rozmiar i nie skaluj obrazu", "resize_noscale"),
        ]
        self.resize_radiobuttons = []
        for txt, val in resize_modes:
            rb = ttk.Radiobutton(resize_frame, text=txt, variable=self.resize_mode, value=val, command=self.update_field_states)
            rb.pack(anchor="w", **pad)
            self.resize_radiobuttons.append(rb)

        format_frame = ttk.Frame(resize_frame)
        format_frame.pack(fill="x", padx=12, pady=(4, 0))
        ttk.Label(format_frame, text="Format:").grid(row=0, column=0, sticky="w")
        self.format_combo = ttk.Combobox(format_frame, textvariable=self.target_format, values=list(self.PAPER_FORMATS.keys()), state="readonly", width=16)
        self.format_combo.grid(row=0, column=1, sticky="w", padx=(0,12))
        self.format_combo.bind("<<ComboboxSelected>>", lambda e: self.update_field_states())

        self.custom_size_frame = ttk.Frame(format_frame)
        self.custom_size_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=(8,0))
        ttk.Label(self.custom_size_frame, text="Szerokość [mm]:").grid(row=0, column=0, sticky="w", padx=(0,6), pady=pady_row1)
        self.e_custom_width = ttk.Entry(self.custom_size_frame, textvariable=self.custom_width, width=8, validate="key", validatecommand=self.vcmd_size)
        self.e_custom_width.grid(row=0, column=1, sticky="w", padx=(0,12), pady=pady_row1)
        ttk.Label(self.custom_size_frame, text="Wysokość [mm]:").grid(row=0, column=2, sticky="w", padx=(0,6), pady=pady_row1)
        self.e_custom_height = ttk.Entry(self.custom_size_frame, textvariable=self.custom_height, width=8, validate="key", validatecommand=self.vcmd_size)
        self.e_custom_height.grid(row=0, column=3, sticky="w", padx=(0,0), pady=pady_row1)
        # Komunikat zakresu rozmiaru niestandardowego
        ttk.Label(self.custom_size_frame, text="Zakres: 1–4000 mm", foreground="gray").grid(row=1, column=0, columnspan=4, sticky="w", pady=(0,0))
        self.custom_entries = [self.e_custom_width, self.e_custom_height]

        # --- POSITION SECTION (osobna ramka) ---
        self.position_frame = ttk.LabelFrame(self, text="Położenie obrazu")
        self.position_frame.pack(fill="x", padx=12, pady=(8, 0))
        position_modes = [
            ("Wyśrodkuj", "center"),
            ("Niestandardowe położenie", "custom")
        ]
        self.position_radiobuttons = []
        for txt, val in position_modes:
            rb = ttk.Radiobutton(self.position_frame, text=txt, variable=self.position_mode, value=val, command=self.update_field_states)
            rb.pack(anchor="w", **pad)
            self.position_radiobuttons.append(rb)

        self.offset_frame = ttk.Frame(self.position_frame)
        self.offset_frame.pack(fill="x", padx=18, pady=(0,0))
        ttk.Label(self.offset_frame, text="Od lewej [mm]:").grid(row=0, column=0, sticky="w", padx=(0,6), pady=pady_row1)
        self.e_offset_x = ttk.Entry(self.offset_frame, textvariable=self.offset_x, width=8, validate="key", validatecommand=self.vcmd_offset)
        self.e_offset_x.grid(row=0, column=1, sticky="w", padx=(0,16), pady=pady_row1)
        ttk.Label(self.offset_frame, text="Od dołu [mm]:").grid(row=0, column=2, sticky="w", padx=(0,6), pady=pady_row1)
        self.e_offset_y = ttk.Entry(self.offset_frame, textvariable=self.offset_y, width=8, validate="key", validatecommand=self.vcmd_offset)
        self.e_offset_y.grid(row=0, column=3, sticky="w", padx=(0,0), pady=pady_row1)
        ttk.Label(self.offset_frame, text="Zakres: 0–500 mm", foreground="gray").grid(row=1, column=0, columnspan=4, sticky="w", pady=(0,0))
        self.offset_entries = [self.e_offset_x, self.e_offset_y]

        # --- BUTTONS ---
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", padx=12, pady=(12,10))
        ttk.Button(button_frame, text="Zastosuj", command=self.ok).pack(side="left", expand=True, padx=5)
        ttk.Button(button_frame, text="Domyślne", command=self.restore_defaults).pack(side="left", expand=True, padx=5)
        ttk.Button(button_frame, text="Anuluj", command=self.cancel).pack(side="right", expand=True, padx=5)

    def update_field_states(self):
        crop_selected = self.crop_mode.get() != "nocrop"
        resize_selected = self.resize_mode.get() != "noresize"

        for rb in self.resize_radiobuttons:
            rb["state"] = tk.DISABLED if crop_selected else tk.NORMAL
        for rb in self.crop_radiobuttons:
            rb["state"] = tk.DISABLED if resize_selected else tk.NORMAL

        enable_crop = self.crop_mode.get() != "nocrop" and not resize_selected
        for entry in self.margin_entries:
            entry["state"] = tk.NORMAL if enable_crop else tk.DISABLED

        enable_format = self.resize_mode.get() != "noresize" and not crop_selected
        self.format_combo["state"] = "readonly" if enable_format else tk.DISABLED
        enable_custom = enable_format and self.target_format.get() == "Niestandardowy"
        for entry in self.custom_entries:
            entry["state"] = tk.NORMAL if enable_custom else tk.DISABLED

        enable_position = (
            (self.resize_mode.get() == "resize_noscale" and not crop_selected)
        )
        state_radio = tk.NORMAL if enable_position else tk.DISABLED
        for rb in self.position_radiobuttons:
            rb["state"] = state_radio

        enable_offsets = enable_position and self.position_mode.get() == "custom"
        for entry in self.offset_entries:
            entry["state"] = tk.NORMAL if enable_offsets else tk.DISABLED

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
            crop_mode = self.crop_mode.get()
            resize_mode = self.resize_mode.get()

            # Marginesy
            if crop_mode == "nocrop":
                top = bottom = left = right = 0.0
            else:
                top = float(self.margin_top.get().replace(",", "."))
                bottom = float(self.margin_bottom.get().replace(",", "."))
                left = float(self.margin_left.get().replace(",", "."))
                right = float(self.margin_right.get().replace(",", "."))
                for v in [top, bottom, left, right]:
                    if v < 0 or v > 200:
                        raise ValueError("Marginesy muszą być z zakresu 0–200 mm.")

            # Format i wymiary docelowe
            if resize_mode != "noresize":
                format_name = self.target_format.get()
                if format_name == "Niestandardowy":
                    w = float(self.custom_width.get().replace(",", "."))
                    h = float(self.custom_height.get().replace(",", "."))
                    if w < 1 or h < 1 or w > 4000 or h > 4000:
                        raise ValueError("Rozmiar niestandardowy musi być z zakresu 1–4000 mm.")
                    target_dims = (w, h)
                else:
                    target_dims = self.PAPER_FORMATS[format_name]
            else:
                format_name = None
                target_dims = (None, None)

            # Pozycjonowanie
            enable_position = (
                (self.resize_mode.get() == "resize_noscale" and not (self.crop_mode.get() != "nocrop"))
            )
            if enable_position:
                position_mode = self.position_mode.get()
                offset_x = offset_y = 0.0
                if position_mode == "custom":
                    offset_x = float(self.offset_x.get().replace(",", "."))
                    offset_y = float(self.offset_y.get().replace(",", "."))
                    if offset_x < 0 or offset_x > 500 or offset_y < 0 or offset_y > 500:
                        raise ValueError("Offset musi być z zakresu 0–500 mm.")
            else:
                position_mode = None
                offset_x = offset_y = None

            self.result = {
                "crop_mode": crop_mode,
                "crop_top_mm": top,
                "crop_bottom_mm": bottom,
                "crop_left_mm": left,
                "crop_right_mm": right,
                "resize_mode": resize_mode,
                "target_format": format_name,
                "target_width_mm": target_dims[0],
                "target_height_mm": target_dims[1],
                "position_mode": position_mode if enable_position else None,
                "offset_x_mm": offset_x if enable_position else None,
                "offset_y_mm": offset_y if enable_position else None,
            }
            # Zapisz preferencje przed zamknięciem
            self._save_prefs()
            self.destroy()
        except Exception as e:
            custom_messagebox(self, "Błąd", f"Nieprawidłowe dane: {e}", typ="error")

    def cancel(self, event=None):
        self.result = None
        self.destroy()
        
# === Tooltip class has been moved to utils/tooltip.py ===

