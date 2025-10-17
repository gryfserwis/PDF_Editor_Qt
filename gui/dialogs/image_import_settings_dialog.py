import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

from utils import validate_float_range, custom_messagebox


class ImageImportSettingsDialog(tk.Toplevel):
    DEFAULTS = {
        'scaling_mode': 'DOPASUJ',
        'alignment_mode': 'SRODEK',
        'scale_factor': 100.0,
        'page_orientation': 'PIONOWO',
        'custom_width': '',
        'custom_height': '',
        'keep_ratio': True
    }

    def __init__(self, parent, title, image_path, prefs_manager=None):
        super().__init__(parent)
        self.prefs_manager = prefs_manager
        self.transient(parent)
        self.title(title)
        self.image_path = image_path
        self.result = None

        # Pozycjonuj poza ekranem, aby uniknąć migotania
        self.geometry("+10000+10000")

        self.image_pixel_width, self.image_pixel_height = 0, 0
        self.image_dpi = 96

        try:
            img = Image.open(image_path)
            self.image_pixel_width, self.image_pixel_height = img.size
            dpi_info = img.info.get('dpi', (96, 96))
            self.image_dpi = dpi_info[0] if isinstance(dpi_info, tuple) else 96
            img.close()
        except Exception:
            pass

        # --- Preferencje / wartości pól ---
        self.scaling_mode = tk.StringVar(value=self._get_pref('scaling_mode'))
        self.alignment_mode = tk.StringVar(value=self._get_pref('alignment_mode'))
        self.scale_factor = tk.DoubleVar(value=float(self._get_pref('scale_factor')))
        self.page_orientation = tk.StringVar(value=self._get_pref('page_orientation'))
        self.custom_width = tk.StringVar(value=self._get_pref('custom_width'))
        self.custom_height = tk.StringVar(value=self._get_pref('custom_height'))
        self.keep_ratio = tk.BooleanVar(value=self._get_pref('keep_ratio') in ('1', 'True', True))

        self._block_update = False  # zabezpieczenie przed zapętleniem synchronizacji

        # === WALIDATORY ===
        self.vcmd_scale = (self.register(lambda v: validate_float_range(v, 1, 500)), "%P")
        self.vcmd_size = (self.register(lambda v: validate_float_range(v, 1, 4000)), "%P")

        self.initial_focus = self.body()
        self.buttonbox()
        self.update_scale_controls()

        self.update_idletasks()

        dialog_width = 420
        dialog_height = self.winfo_height()
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

    def _get_pref(self, key):
        if self.prefs_manager:
            return self.prefs_manager.get(f'ImageImportSettingsDialog.{key}', self.DEFAULTS.get(key, ''))
        return self.DEFAULTS.get(key, '')

    def _save_prefs(self):
        if self.prefs_manager:
            self.prefs_manager.set('ImageImportSettingsDialog.scaling_mode', self.scaling_mode.get())
            self.prefs_manager.set('ImageImportSettingsDialog.alignment_mode', self.alignment_mode.get())
            self.prefs_manager.set('ImageImportSettingsDialog.scale_factor', str(self.scale_factor.get()))
            self.prefs_manager.set('ImageImportSettingsDialog.page_orientation', self.page_orientation.get())
            self.prefs_manager.set('ImageImportSettingsDialog.custom_width', self.custom_width.get())
            self.prefs_manager.set('ImageImportSettingsDialog.custom_height', self.custom_height.get())
            self.prefs_manager.set('ImageImportSettingsDialog.keep_ratio', str(self.keep_ratio.get()))

    def restore_defaults(self):
        self.scaling_mode.set(self.DEFAULTS['scaling_mode'])
        self.alignment_mode.set(self.DEFAULTS['alignment_mode'])
        self.scale_factor.set(self.DEFAULTS['scale_factor'])
        self.page_orientation.set(self.DEFAULTS['page_orientation'])
        self.custom_width.set(self.DEFAULTS['custom_width'])
        self.custom_height.set(self.DEFAULTS['custom_height'])
        self.keep_ratio.set(self.DEFAULTS['keep_ratio'])
        self.update_scale_controls()

    def body(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Sekcja 1: Informacje o obrazie
        info_frame = ttk.LabelFrame(main_frame, text="Informacje o obrazie źródłowym", padding=(8, 4))
        info_frame.pack(fill='x', pady=(0, 8))
        ttk.Label(info_frame, text=f"Wymiary: {self.image_pixel_width} x {self.image_pixel_height} px", anchor="w").pack(fill='x')
        ttk.Label(info_frame, text=f"DPI: {self.image_dpi}", anchor="w").pack(fill='x')

        # Sekcja 2: Ustawienia skalowania
        scale_frame = ttk.LabelFrame(main_frame, text="Ustawienia importu", padding=(8, 4))
        scale_frame.pack(fill='x', pady=(0, 8))
        options = [
            ("Dopasuj do strony A4 [marginesy 25 mm]", "DOPASUJ"),
            ("Oryginalny rozmiar (100%)", "ORYGINALNY"),
            ("Skala niestandardowa", "SKALA"),
            ("Dopasuj rozmiar strony do obrazu", "PAGE_TO_IMAGE"),
            ("Dopasuj obraz do dokłanego rozmiaru strony", "CUSTOM_SIZE")
        ]
        for text, value in options:
            rb = ttk.Radiobutton(
                scale_frame, text=text, variable=self.scaling_mode, value=value,
                command=self.update_scale_controls
            )
            rb.pack(anchor="w", pady=2)
            if value == "SKALA":
                self.scale_entry_frame = ttk.Frame(scale_frame)
                self.scale_entry_frame.pack(fill='x', pady=2, padx=24)
                ttk.Label(self.scale_entry_frame, text="Skala [%]:").pack(side=tk.LEFT)
                self.scale_entry = ttk.Entry(
                    self.scale_entry_frame, textvariable=self.scale_factor, width=6, validate="key", validatecommand=self.vcmd_scale
                )
                self.scale_entry.pack(side=tk.LEFT, padx=5)
                ttk.Label(self.scale_entry_frame, text="(1–500)").pack(side=tk.LEFT)
            if value == "CUSTOM_SIZE":
                self.custom_size_frame = ttk.Frame(scale_frame)
                self.custom_size_frame.pack(fill='x', pady=2, padx=24)
                ttk.Label(self.custom_size_frame, text="Szerokość [mm]:").pack(side=tk.LEFT)
                self.custom_width_entry = ttk.Entry(self.custom_size_frame, textvariable=self.custom_width, width=8, validate="key", validatecommand=self.vcmd_size)
                self.custom_width_entry.pack(side=tk.LEFT, padx=5)
                ttk.Label(self.custom_size_frame, text="Wysokość [mm]:").pack(side=tk.LEFT)
                self.custom_height_entry = ttk.Entry(self.custom_size_frame, textvariable=self.custom_height, width=8, validate="key", validatecommand=self.vcmd_size)
                self.custom_height_entry.pack(side=tk.LEFT, padx=5)
                # Checkbox "Zachowaj proporcje" pod polami, równo z ramką
                self.ratio_check_frame = ttk.Frame(scale_frame)
                self.ratio_check_frame.pack(fill='x', pady=(0, 5), padx=24)
                self.ratio_check = ttk.Checkbutton(self.ratio_check_frame, text="Zachowaj proporcje", variable=self.keep_ratio)
                self.ratio_check.pack(anchor="w")

        # Sekcja 3: Orientacja strony (po skalowaniu, przed wyrównaniem)
        orient_frame = ttk.LabelFrame(main_frame, text="Orientacja strony docelowej (A4)", padding=(8, 4))
        orient_frame.pack(fill='x', pady=(0, 8))
        self.rb_pion = ttk.Radiobutton(orient_frame, text="Pionowo", variable=self.page_orientation, value="PIONOWO")
        self.rb_pion.pack(anchor="w")
        self.rb_poz = ttk.Radiobutton(orient_frame, text="Poziomo", variable=self.page_orientation, value="POZIOMO")
        self.rb_poz.pack(anchor="w")

        # Sekcja 4: Wyrównanie
        align_frame = ttk.LabelFrame(main_frame, text="Wyrównanie na stronie", padding=(8, 4))
        align_frame.pack(fill='x')
        self.align_rbs = []
        align_options = [
            ("Środek strony", "SRODEK"),
            ("Góra", "GORA"),
            ("Dół", "DOL")
        ]
        for text, value in align_options:
            rb = ttk.Radiobutton(align_frame, text=text, variable=self.alignment_mode, value=value)
            rb.pack(anchor="w", pady=2)
            self.align_rbs.append(rb)

        # Powiązania wpisów do zachowania proporcji
        if hasattr(self, "custom_width_entry") and hasattr(self, "custom_height_entry"):
            self.custom_width_entry.bind("<KeyRelease>", self.on_width_change)
            self.custom_height_entry.bind("<KeyRelease>", self.on_height_change)
            self.custom_width_entry.bind("<FocusOut>", self.on_width_change)
            self.custom_height_entry.bind("<FocusOut>", self.on_height_change)

        return self.scale_entry if hasattr(self, "scale_entry") else self.custom_width_entry

    def update_scale_controls(self):
        if hasattr(self, "scale_entry"):
            if self.scaling_mode.get() == "SKALA":
                self.scale_entry.config(state=tk.NORMAL)
            else:
                self.scale_entry.config(state=tk.DISABLED)
        custom_size_active = self.scaling_mode.get() == "CUSTOM_SIZE"
        if hasattr(self, "custom_width_entry") and hasattr(self, "custom_height_entry") and hasattr(self, "ratio_check"):
            state = tk.NORMAL if custom_size_active else tk.DISABLED
            self.custom_width_entry.config(state=state)
            self.custom_height_entry.config(state=state)
            self.ratio_check.config(state=state)
        if self.scaling_mode.get() in ("DOPASUJ", "ORYGINALNY", "SKALA"):
            self.rb_pion.config(state=tk.NORMAL)
            self.rb_poz.config(state=tk.NORMAL)
            for rb in getattr(self, "align_rbs", []):
                rb.config(state=tk.NORMAL)
        else:
            self.rb_pion.config(state=tk.DISABLED)
            self.rb_poz.config(state=tk.DISABLED)
            for rb in getattr(self, "align_rbs", []):
                rb.config(state=tk.DISABLED)

    def on_width_change(self, event=None):
        if self.scaling_mode.get() != "CUSTOM_SIZE" or not self.keep_ratio.get() or self._block_update:
            return
        try:
            w = float(self.custom_width.get().replace(",", "."))
            if w <= 0 or not self.image_pixel_width or not self.image_pixel_height:
                return
            prop = self.image_pixel_height / self.image_pixel_width
            h = round(w * prop, 2)
            self._block_update = True
            self.custom_height.set(str(h))
            self._block_update = False
        except Exception:
            pass

    def on_height_change(self, event=None):
        if self.scaling_mode.get() != "CUSTOM_SIZE" or not self.keep_ratio.get() or self._block_update:
            return
        try:
            h = float(self.custom_height.get().replace(",", "."))
            if h <= 0 or not self.image_pixel_width or not self.image_pixel_height:
                return
            prop = self.image_pixel_width / self.image_pixel_height
            w = round(h * prop, 2)
            self._block_update = True
            self.custom_width.set(str(w))
            self._block_update = False
        except Exception:
            pass

    def buttonbox(self):
        box = ttk.Frame(self)
        box.pack(fill=tk.X, pady=(8, 10))
        center = ttk.Frame(box)
        center.pack(anchor="center")
        ttk.Button(center, text="Importuj", width=12, command=self.ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(center, text="Domyślne", width=12, command=self.restore_defaults).pack(side=tk.LEFT, padx=10)
        ttk.Button(center, text="Anuluj", width=12, command=self.cancel).pack(side=tk.LEFT, padx=10)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", lambda e: self.cancel())

    def ok(self, event=None):
        custom_width = None
        custom_height = None
        if self.scaling_mode.get() == "SKALA":
            try:
                scale_val = self.scale_factor.get()
                if not (1 <= scale_val <= 500):
                    raise ValueError
            except Exception:
                custom_messagebox(self, "Błąd", "Skala musi być wartością liczbową od 1 do 500%.", typ="error")
                self.scale_entry.focus_set()
                return
        if self.scaling_mode.get() == "CUSTOM_SIZE":
            try:
                custom_width = float(self.custom_width.get().replace(",", "."))
                custom_height = float(self.custom_height.get().replace(",", "."))
                if not (1 <= custom_width <= 4000 and 1 <= custom_height <= 4000):
                    raise ValueError
            except Exception:
                custom_messagebox(self, "Błąd", "Podaj prawidłowe wymiary strony [1–4000 mm] dla opcji 'Dokładny wymiar strony'.", typ="error")
                return

        self.result = {
            'scaling_mode': self.scaling_mode.get(),
            'scale_factor': self.scale_factor.get() / 100,
            'alignment': self.alignment_mode.get(),
            'page_orientation': self.page_orientation.get(),
            'image_dpi': self.image_dpi,
            'custom_width_mm': custom_width,
            'custom_height_mm': custom_height,
            'keep_ratio': self.keep_ratio.get()
        }
        self._save_prefs()
        self.destroy()

    def cancel(self, event=None):
        self.result = None
        self.destroy()
# ====================================================================
# KLASA: OKNO DIALOGOWE WYBORU ZAKRESU STRON (Bez zmian)
# ====================================================================

import tkinter as tk
from tkinter import ttk, messagebox
import re
from typing import Optional, List

