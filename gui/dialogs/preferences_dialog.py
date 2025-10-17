import tkinter as tk
from tkinter import filedialog, ttk

from utils import custom_messagebox


class PreferencesDialog(tk.Toplevel):
    """Okno dialogowe preferencji programu"""
    
    def __init__(self, parent, prefs_manager):
        super().__init__(parent)
        self.parent = parent
        self.prefs_manager = prefs_manager
        self.title("Preferencje programu")
        self.transient(parent)
        self.result = None
        
        # Pozycjonuj poza ekranem, aby uniknąć migotania
        self.geometry("+10000+10000")
        
        self.build_ui()
        self.load_current_values()
        
        self.center_dialog(parent)
        self.grab_set()
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.resizable(False, False)
        self.bind("<Escape>", lambda e: self.cancel())
        self.wait_window(self)
    
    def build_ui(self):
        main_frame = ttk.Frame(self, padding="12")
        main_frame.pack(fill="both", expand=True)
        
        # Sekcja ogólna
        general_frame = ttk.LabelFrame(main_frame, text="Ustawienia ogólne", padding="8")
        general_frame.pack(fill="x", pady=(0, 8))
        
        # Domyślna ścieżka odczytu
        ttk.Label(general_frame, text="Domyślna ścieżka odczytu:").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.default_read_path_var = tk.StringVar()
        read_path_frame = ttk.Frame(general_frame)
        read_path_frame.grid(row=0, column=1, sticky="ew", padx=4, pady=4)
        ttk.Entry(read_path_frame, textvariable=self.default_read_path_var, width=30).pack(side="left", fill="x", expand=True)
        ttk.Button(read_path_frame, text="...", width=3, command=self.browse_read_path).pack(side="left", padx=(4, 0))
        
        # Domyślna ścieżka zapisu
        ttk.Label(general_frame, text="Domyślna ścieżka zapisu:").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        self.default_path_var = tk.StringVar()
        path_frame = ttk.Frame(general_frame)
        path_frame.grid(row=1, column=1, sticky="ew", padx=4, pady=4)
        ttk.Entry(path_frame, textvariable=self.default_path_var, width=30).pack(side="left", fill="x", expand=True)
        ttk.Button(path_frame, text="...", width=3, command=self.browse_path).pack(side="left", padx=(4, 0))
        
        # Jakość miniatur
        ttk.Label(general_frame, text="Jakość miniatur:").grid(row=2, column=0, sticky="w", padx=4, pady=4)
        self.thumbnail_quality_var = tk.StringVar()
        quality_combo = ttk.Combobox(general_frame, textvariable=self.thumbnail_quality_var, values=["Niska", "Średnia", "Wysoka"], state="readonly", width=10)
        quality_combo.grid(row=2, column=1, sticky="w", padx=4, pady=4)
        
        # Potwierdzenie przed usunięciem
        ttk.Label(general_frame, text="Potwierdzenie przed usunięciem:").grid(row=3, column=0, sticky="w", padx=4, pady=4)
        self.confirm_delete_var = tk.BooleanVar()
        confirm_check = ttk.Checkbutton(general_frame, variable=self.confirm_delete_var)
        confirm_check.grid(row=3, column=1, sticky="w", padx=4, pady=4)
        
        # DPI eksportowanych obrazów
        ttk.Label(general_frame, text="DPI eksportowanych obrazów:").grid(row=4, column=0, sticky="w", padx=4, pady=4)
        self.export_image_dpi_var = tk.StringVar()
        dpi_combo = ttk.Combobox(general_frame, textvariable=self.export_image_dpi_var, values=["150", "300", "600"], state="readonly", width=10)
        dpi_combo.grid(row=4, column=1, sticky="w", padx=4, pady=4)
        
        general_frame.columnconfigure(1, weight=1)
        
        # Sekcja wykrywania stron kolorowych
        color_detect_frame = ttk.LabelFrame(main_frame, text="Wykrywanie stron kolorowych", padding="8")
        color_detect_frame.pack(fill="x", pady=(0, 8))
        
        # Próg wykrywania koloru
        ttk.Label(color_detect_frame, text="Próg różnicy RGB:").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.color_threshold_var = tk.StringVar()
        threshold_entry = ttk.Entry(color_detect_frame, textvariable=self.color_threshold_var, width=10)
        threshold_entry.grid(row=0, column=1, sticky="w", padx=4, pady=4)
        ttk.Label(color_detect_frame, text="(1-255, domyślnie 5)", foreground="gray").grid(row=0, column=2, sticky="w", padx=4, pady=4)
        
        # Liczba próbkowanych pikseli
        ttk.Label(color_detect_frame, text="Liczba próbkowanych pikseli:").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        self.color_samples_var = tk.StringVar()
        samples_entry = ttk.Entry(color_detect_frame, textvariable=self.color_samples_var, width=10)
        samples_entry.grid(row=1, column=1, sticky="w", padx=4, pady=4)
        ttk.Label(color_detect_frame, text="(10-1000, domyślnie 300)", foreground="gray").grid(row=1, column=2, sticky="w", padx=4, pady=4)
        
        # Skala renderowania
        ttk.Label(color_detect_frame, text="Skala renderowania:").grid(row=2, column=0, sticky="w", padx=4, pady=4)
        self.color_scale_var = tk.StringVar()
        scale_entry = ttk.Entry(color_detect_frame, textvariable=self.color_scale_var, width=10)
        scale_entry.grid(row=2, column=1, sticky="w", padx=4, pady=4)
        ttk.Label(color_detect_frame, text="(0.1-2.0, domyślnie 0.2)", foreground="gray").grid(row=2, column=2, sticky="w", padx=4, pady=4)
        
        color_detect_frame.columnconfigure(2, weight=1)
        
        # Informacja
       # info_frame = ttk.Frame(main_frame)
       # info_frame.pack(fill="x", pady=8)
       # info_label = ttk.Label(info_frame, text="Program automatycznie zapamiętuje ostatnio użyte wartości\nw oknach dialogowych.", foreground="gray")
       # info_label.pack()
        
        # Ramka resetu
        reset_frame = ttk.LabelFrame(main_frame, text="Reset do ustawień domyślnych", padding="8")
        reset_frame.pack(fill="x", pady=(0, 8))
        ttk.Button(reset_frame, text="Resetuj", command=self.reset_all_defaults).pack()
        
        # Przyciski
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(8, 0))
        
        ttk.Button(button_frame, text="Zapisz", command=self.ok).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Anuluj", command=self.cancel).pack(side="right", padx=5)
    
    def browse_read_path(self):
        from tkinter import filedialog
        path = filedialog.askdirectory(title="Wybierz domyślną ścieżkę odczytu")
        if path:
            self.default_read_path_var.set(path)
    
    def browse_path(self):
        from tkinter import filedialog
        path = filedialog.askdirectory(title="Wybierz domyślną ścieżkę zapisu")
        if path:
            self.default_path_var.set(path)
    
    def load_current_values(self):
        """Wczytuje obecne wartości preferencji"""
        self.default_read_path_var.set(self.prefs_manager.get('default_read_path'))
        self.default_path_var.set(self.prefs_manager.get('default_save_path'))
        self.thumbnail_quality_var.set(self.prefs_manager.get('thumbnail_quality'))
        self.confirm_delete_var.set(self.prefs_manager.get('confirm_delete') == 'True')
        self.export_image_dpi_var.set(self.prefs_manager.get('export_image_dpi'))
        self.color_threshold_var.set(self.prefs_manager.get('color_detect_threshold'))
        self.color_samples_var.set(self.prefs_manager.get('color_detect_samples'))
        self.color_scale_var.set(self.prefs_manager.get('color_detect_scale'))
    
    def reset_all_defaults(self):
        """Przywraca domyślne wartości we wszystkich dialogach"""
        response = custom_messagebox(
            self, "Przywracanie domyślnych",
            "Czy na pewno chcesz przywrócić wszystkie domyślne wartości we wszystkich\noknach dialogowych i skasować wszytkie profile?",
            typ="question"
        )
        if response:
            self.prefs_manager.reset_to_defaults()
            self.load_current_values()
            custom_messagebox(self, "Informacja", "Przywrócono wszystkie domyślne wartości.", typ="info")
    
    def center_dialog(self, parent):
        """Wyśrodkowuje dialog względem rodzica"""
        self.update_idletasks()
        dialog_w = self.winfo_width()
        dialog_h = self.winfo_height()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        x = parent_x + (parent_w - dialog_w) // 2
        y = parent_y + (parent_h - dialog_h) // 2
        self.geometry(f"+{x}+{y}")
    
    def ok(self, event=None):
        """Zapisuje preferencje"""
        # Validate color detection settings
        try:
            threshold = int(self.color_threshold_var.get())
            if threshold < 1 or threshold > 255:
                custom_messagebox(self, "Błąd", "Próg różnicy RGB musi być z zakresu 1-255.", typ="error")
                return
        except ValueError:
            custom_messagebox(self, "Błąd", "Próg różnicy RGB musi być liczbą całkowitą.", typ="error")
            return
        
        try:
            samples = int(self.color_samples_var.get())
            if samples < 10 or samples > 1000:
                custom_messagebox(self, "Błąd", "Liczba próbkowanych pikseli musi być z zakresu 10-1000.", typ="error")
                return
        except ValueError:
            custom_messagebox(self, "Błąd", "Liczba próbkowanych pikseli musi być liczbą całkowitą.", typ="error")
            return
        
        try:
            scale = float(self.color_scale_var.get().replace(',', '.'))
            if scale < 0.1 or scale > 2.0:
                custom_messagebox(self, "Błąd", "Skala renderowania musi być z zakresu 0.1-2.0.", typ="error")
                return
        except ValueError:
            custom_messagebox(self, "Błąd", "Skala renderowania musi być liczbą.", typ="error")
            return
        
        self.prefs_manager.set('default_read_path', self.default_read_path_var.get())
        self.prefs_manager.set('default_save_path', self.default_path_var.get())
        self.prefs_manager.set('thumbnail_quality', self.thumbnail_quality_var.get())
        self.prefs_manager.set('confirm_delete', 'True' if self.confirm_delete_var.get() else 'False')
        self.prefs_manager.set('export_image_dpi', self.export_image_dpi_var.get())
        self.prefs_manager.set('color_detect_threshold', str(threshold))
        self.prefs_manager.set('color_detect_samples', str(samples))
        self.prefs_manager.set('color_detect_scale', str(scale))
        self.result = True
        self.destroy()
    
    def cancel(self, event=None):
        """Anuluje zmiany"""
        self.result = None
        self.destroy()


