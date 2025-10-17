import tkinter as tk
from tkinter import ttk

from utils import validate_float_range, custom_messagebox


class PageNumberMarginDialog(tk.Toplevel):
    """Okno dialogowe do określania wysokości marginesów (górnego i dolnego) do skanowania."""
    DEFAULTS = {
        'top_margin': '20',
        'bottom_margin': '20',
    }
    
    def __init__(self, parent, initial_margin_mm=20, prefs_manager=None):
        super().__init__(parent)
        self.prefs_manager = prefs_manager
        self.parent = parent
        self.transient(parent)
        self.title("Usuwanie numeracji stron")
        self.result = None
        
        # Pozycjonuj poza ekranem, aby uniknąć migotania
        self.geometry("+10000+10000")

        self.vcmd_margin = (self.register(lambda v: validate_float_range(v, 0, 200)), "%P")
        
        # Wczytaj ostatnie wartości lub użyj przekazanych/domyślnych
        if prefs_manager:
            initial_top = self._get_pref('top_margin')
            initial_bottom = self._get_pref('bottom_margin')
        else:
            initial_top = str(initial_margin_mm)
            initial_bottom = str(initial_margin_mm)
        
        self.create_widgets(initial_top, initial_bottom)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.cancel)

        # Ustawienia modalności
        self.grab_set()
        self.focus_force()
        self.bind('<Escape>', lambda e: self.cancel())
        self.bind('<Return>', lambda e: self.ok())

        self.center_window()
        self.wait_window(self)
    
    def _get_pref(self, key):
        """Pobiera preferencję dla tego dialogu"""
        if self.prefs_manager:
            return self.prefs_manager.get(f'PageNumberMarginDialog.{key}', self.DEFAULTS.get(key, ''))
        return self.DEFAULTS.get(key, '')
    
    def _save_prefs(self):
        """Zapisuje obecne wartości do preferencji"""
        if self.prefs_manager:
            self.prefs_manager.set('PageNumberMarginDialog.top_margin', self.top_margin_entry.get())
            self.prefs_manager.set('PageNumberMarginDialog.bottom_margin', self.bottom_margin_entry.get())
    
    def restore_defaults(self):
        """Przywraca wartości domyślne"""
        self.top_margin_entry.delete(0, tk.END)
        self.top_margin_entry.insert(0, self.DEFAULTS['top_margin'])
        self.bottom_margin_entry.delete(0, tk.END)
        self.bottom_margin_entry.insert(0, self.DEFAULTS['bottom_margin'])

    def center_window(self):
        self.update_idletasks()
        # Automatyczna szerokość (nie ustawiamy na sztywno)
        w = self.winfo_width()
        h = self.winfo_height()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - w) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - h) // 2
        self.geometry(f'{w}x{h}+{x}+{y}')

    def create_widgets(self, initial_top, initial_bottom):
        main_frame = ttk.Frame(self, padding="6")
        main_frame.pack(fill="both", expand=True)

        margin_frame = ttk.LabelFrame(
            main_frame, text="Wysokość pola z numerem [mm]", padding=(8, 4)
        )
        margin_frame.pack(fill="x", padx=4, pady=(6, 2))

        ENTRY_WIDTH = 4

        # Marginesy w jednym wierszu (etykiety i pola obok siebie)
        ttk.Label(margin_frame, text="Od góry (nagłówek):").grid(
            row=0, column=0, sticky="e", padx=(2, 6), pady=(2, 2)
        )
        self.top_margin_entry = ttk.Entry(margin_frame, width=ENTRY_WIDTH, validate="key", validatecommand=self.vcmd_margin)
        self.top_margin_entry.insert(0, initial_top)
        self.top_margin_entry.grid(row=0, column=1, sticky="w", padx=(0, 12), pady=(2, 2))

        ttk.Label(margin_frame, text="Od dołu (stopka):").grid(
            row=0, column=2, sticky="e", padx=(2, 6), pady=(2, 2)
        )
        self.bottom_margin_entry = ttk.Entry(margin_frame, width=ENTRY_WIDTH, validate="key", validatecommand=self.vcmd_margin)
        self.bottom_margin_entry.insert(0, initial_bottom)
        self.bottom_margin_entry.grid(row=0, column=3, sticky="w", padx=(0, 2), pady=(2, 2))

        # Komunikat pod polami
        info_label = ttk.Label(
            margin_frame,
            text="Zakres: 0–200 mm.\nSkrypt szuka nr stron w zadanym polu. Jeśli podasz zbyt duże wartości skrypt może usunąć np. nr rozdziału.",
            foreground="gray",
            justify="left",
            font=("Arial", 9),
            wraplength=300  # <-- ograniczenie szerokości komunikatu
        )
        info_label.grid(row=1, column=0, columnspan=4, sticky="w", padx=(2, 2), pady=(6, 2))

        # Przyciski
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', side='bottom', pady=(8, 4))
        ttk.Button(button_frame, text="Usuń", command=self.ok).pack(side='left', expand=True, padx=5)
        ttk.Button(button_frame, text="Domyślne", command=self.restore_defaults).pack(side='left', expand=True, padx=5)
        ttk.Button(button_frame, text="Anuluj", command=self.cancel).pack(side='right', expand=True, padx=5)

    def ok(self, event=None):
        try:
            top_mm = float(self.top_margin_entry.get().replace(',', '.'))
            bottom_mm = float(self.bottom_margin_entry.get().replace(',', '.'))

            if not (0 <= top_mm <= 200 and 0 <= bottom_mm <= 200):
                raise ValueError("Wartości marginesów muszą być z zakresu 0–200 mm.")

            self.result = {'top_mm': top_mm, 'bottom_mm': bottom_mm}
            # Zapisz preferencje przed zamknięciem
            self._save_prefs()
            self.destroy()
        except ValueError:
            custom_messagebox(self, "Błąd Wprowadzania", "Wprowadź prawidłowe, nieujemne liczby [w mm, max 200].", typ="error")

    def cancel(self, event=None):
        self.result = None
        self.destroy()

