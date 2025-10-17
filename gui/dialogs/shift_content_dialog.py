import tkinter as tk
from tkinter import ttk

from utils import validate_float_range, custom_messagebox


class ShiftContentDialog(tk.Toplevel):
    """Okno dialogowe do określania przesunięcia zawartości strony, wyśrodkowane i modalne."""
    DEFAULTS = {
        'x_direction': 'P',
        'y_direction': 'G',
        'x_value': '0',
        'y_value': '0',
    }
    
    def __init__(self, parent, prefs_manager=None):
        super().__init__(parent)
        self.parent = parent
        self.prefs_manager = prefs_manager
        self.transient(parent)
        self.title("Przesuwanie zawartości stron")
        self.result = None
        
        # Pozycjonuj poza ekranem, aby uniknąć migotania
        self.geometry("+10000+10000")

        # WALIDATOR: tylko liczby/kropka/przecinek, zakres 0–1000
        self.vcmd_shift = (self.register(lambda v: validate_float_range(v, 0, 1000)), "%P")

        self.create_widgets()
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.grab_set()
        self.focus_force()
        self.bind('<Escape>', lambda event: self.cancel())
        self.bind('<Return>', lambda event: self.ok())

        self.center_window()
        self.wait_window(self)
    
    def _get_pref(self, key):
        """Pobiera preferencję dla tego dialogu"""
        if self.prefs_manager:
            return self.prefs_manager.get(f'ShiftContentDialog.{key}', self.DEFAULTS.get(key, ''))
        return self.DEFAULTS.get(key, '')
    
    def _save_prefs(self):
        """Zapisuje obecne wartości do preferencji"""
        if self.prefs_manager:
            self.prefs_manager.set('ShiftContentDialog.x_direction', self.x_direction.get())
            self.prefs_manager.set('ShiftContentDialog.y_direction', self.y_direction.get())
            self.prefs_manager.set('ShiftContentDialog.x_value', self.x_value.get())
            self.prefs_manager.set('ShiftContentDialog.y_value', self.y_value.get())
    
    def restore_defaults(self):
        """Przywraca wartości domyślne"""
        self.x_direction.set(self.DEFAULTS['x_direction'])
        self.y_direction.set(self.DEFAULTS['y_direction'])
        self.x_value.delete(0, tk.END)
        self.x_value.insert(0, self.DEFAULTS['x_value'])
        self.y_value.delete(0, tk.END)
        self.y_value.insert(0, self.DEFAULTS['y_value'])

    def center_window(self):
        self.update_idletasks()
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        position_x = parent_x + (parent_width // 2) - (dialog_width // 2)
        position_y = parent_y + (parent_height // 2) - (dialog_height // 2)
        self.geometry(f'+{position_x}+{position_y}')

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="8")
        main_frame.pack(fill="both", expand=True)

        xy_frame = ttk.LabelFrame(main_frame, text="Kierunek i wartość przesunięcia [mm]", padding=(8, 6))
        xy_frame.pack(fill='x', padx=4, pady=(8, 0))

        ENTRY_WIDTH = 4

        # Przesunięcie X (poziome)
        ttk.Label(xy_frame, text="Poziome:").grid(row=0, column=0, sticky="w", padx=(2, 8), pady=(4,2))
        self.x_value = ttk.Entry(xy_frame, width=ENTRY_WIDTH, validate="key", validatecommand=self.vcmd_shift)
        self.x_value.insert(0, self._get_pref('x_value'))
        self.x_value.grid(row=0, column=1, sticky="w", padx=(0,2), pady=(4,2))
        self.x_direction = tk.StringVar(value=self._get_pref('x_direction'))
        ttk.Radiobutton(xy_frame, text="Lewo", variable=self.x_direction, value='L').grid(row=0, column=2, sticky="w", padx=(8, 4))
        ttk.Radiobutton(xy_frame, text="Prawo", variable=self.x_direction, value='P').grid(row=0, column=3, sticky="w", padx=(0,2))

        # Przesunięcie Y (pionowe)
        ttk.Label(xy_frame, text="Pionowe:").grid(row=1, column=0, sticky="w", padx=(2, 8), pady=(8,2))
        self.y_value = ttk.Entry(xy_frame, width=ENTRY_WIDTH, validate="key", validatecommand=self.vcmd_shift)
        self.y_value.insert(0, self._get_pref('y_value'))
        self.y_value.grid(row=1, column=1, sticky="w", padx=(0,2), pady=(8,2))
        self.y_direction = tk.StringVar(value=self._get_pref('y_direction'))
        ttk.Radiobutton(xy_frame, text="Dół", variable=self.y_direction, value='D').grid(row=1, column=2, sticky="w", padx=(8, 4))
        ttk.Radiobutton(xy_frame, text="Góra", variable=self.y_direction, value='G').grid(row=1, column=3, sticky="w", padx=(0,2))

        # Komunikat informacyjny przeniesiony do ramki xy_frame
        info_label = ttk.Label(
            xy_frame,
            text="Zakres: 0–1000 mm.",
            foreground="gray",
            justify="left",
            font=("Arial", 9),
            wraplength=240
        )
        info_label.grid(row=2, column=0, columnspan=4, sticky="w", padx=(2, 2), pady=(10, 2))

        # Przyciski
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', side='bottom', pady=(10, 4))
        ttk.Button(button_frame, text="Przesuń", command=self.ok).pack(side='left', expand=True, padx=5)
        ttk.Button(button_frame, text="Domyślne", command=self.restore_defaults).pack(side='left', expand=True, padx=5)
        ttk.Button(button_frame, text="Anuluj", command=self.cancel).pack(side='right', expand=True, padx=5)

    def ok(self, event=None):
        try:
            x_mm = float(self.x_value.get().replace(',', '.'))
            y_mm = float(self.y_value.get().replace(',', '.'))
            if not (0 <= x_mm <= 1000 and 0 <= y_mm <= 1000):
                raise ValueError("Wartości przesunięcia muszą być z zakresu 0–1000 mm.")
            self.result = {
                'x_dir': self.x_direction.get(),
                'y_dir': self.y_direction.get(),
                'x_mm': x_mm,
                'y_mm': y_mm
            }
            # Zapisz preferencje przed zamknięciem
            self._save_prefs()
            self.destroy()
        except ValueError as e:
            custom_messagebox(
                self, "Błąd Wprowadzania", 
                f"Nieprawidłowa wartość: {e}. Użyj cyfr, kropki lub przecinka.",
                typ="error"
            )

    def cancel(self, event=None):
        self.result = None
        self.destroy()

