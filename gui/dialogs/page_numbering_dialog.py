import tkinter as tk
from tkinter import ttk

from utils import validate_float_range, custom_messagebox


class PageNumberingDialog(tk.Toplevel):
    DEFAULTS = {
        'margin_left': '35',
        'margin_right': '25',
        'margin_vertical_mm': '15',
        'vertical_pos': 'dol',
        'alignment': 'prawa',
        'mode': 'normalna',
        'start_page': '1',
        'start_number': '1',
        'font_name': 'Times-Roman',
        'font_size': '12',
        'mirror_margins': 'False',
        'format_type': 'simple',
    }
    
    def __init__(self, parent, prefs_manager=None):
        super().__init__(parent)
        self.parent = parent
        self.prefs_manager = prefs_manager
        self.transient(parent)
        self.title("Dodawanie numeracji stron")
        self.result = None
        
        # Pozycjonuj poza ekranem, aby uniknąć migotania
        self.geometry("+10000+10000")

        # Walidatory
        self.vcmd_200 = (self.register(lambda v: validate_float_range(v, 1, 200)), "%P")
        self.vcmd_9999 = (self.register(lambda v: validate_float_range(v, 1, 9999)), "%P")

        self.create_variables()
        self.build_ui()

        self.resizable(False, False)
        self.grab_set()
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.bind('<Escape>', lambda e: self.cancel())
        self.bind('<Return>', lambda e: self.ok())
        self.center_window()
        self.wait_window(self)

    def create_variables(self):
        self.v_margin_left = tk.StringVar(value=self._get_pref('margin_left'))
        self.v_margin_right = tk.StringVar(value=self._get_pref('margin_right'))
        self.v_margin_vertical_mm = tk.StringVar(value=self._get_pref('margin_vertical_mm'))
        self.v_vertical_pos = tk.StringVar(value=self._get_pref('vertical_pos'))
        self.v_alignment = tk.StringVar(value=self._get_pref('alignment'))
        self.v_mode = tk.StringVar(value=self._get_pref('mode'))
        self.v_start_page = tk.StringVar(value=self._get_pref('start_page'))
        self.v_start_number = tk.StringVar(value=self._get_pref('start_number'))
        self.font_options = ["Helvetica", "Times-Roman", "Courier", "Arial"]
        self.size_options = ["6", "8", "10", "11", "12", "13", "14"]
        self.v_font_name = tk.StringVar(value=self._get_pref('font_name'))
        self.v_font_size = tk.StringVar(value=self._get_pref('font_size'))
        self.v_mirror_margins = tk.BooleanVar(value=self._get_pref('mirror_margins') == 'True')
        self.v_format_type = tk.StringVar(value=self._get_pref('format_type'))
    
    def _get_pref(self, key):
        """Pobiera preferencję dla tego dialogu"""
        if self.prefs_manager:
            return self.prefs_manager.get(f'PageNumberingDialog.{key}', self.DEFAULTS.get(key, ''))
        return self.DEFAULTS.get(key, '')
    
    def _save_prefs(self):
        """Zapisuje obecne wartości do preferencji"""
        if self.prefs_manager:
            self.prefs_manager.set('PageNumberingDialog.margin_left', self.v_margin_left.get())
            self.prefs_manager.set('PageNumberingDialog.margin_right', self.v_margin_right.get())
            self.prefs_manager.set('PageNumberingDialog.margin_vertical_mm', self.v_margin_vertical_mm.get())
            self.prefs_manager.set('PageNumberingDialog.vertical_pos', self.v_vertical_pos.get())
            self.prefs_manager.set('PageNumberingDialog.alignment', self.v_alignment.get())
            self.prefs_manager.set('PageNumberingDialog.mode', self.v_mode.get())
            self.prefs_manager.set('PageNumberingDialog.start_page', self.v_start_page.get())
            self.prefs_manager.set('PageNumberingDialog.start_number', self.v_start_number.get())
            self.prefs_manager.set('PageNumberingDialog.font_name', self.v_font_name.get())
            self.prefs_manager.set('PageNumberingDialog.font_size', self.v_font_size.get())
            self.prefs_manager.set('PageNumberingDialog.mirror_margins', str(self.v_mirror_margins.get()))
            self.prefs_manager.set('PageNumberingDialog.format_type', self.v_format_type.get())
    
    def restore_defaults(self):
        """Przywraca wartości domyślne"""
        self.v_margin_left.set(self.DEFAULTS['margin_left'])
        self.v_margin_right.set(self.DEFAULTS['margin_right'])
        self.v_margin_vertical_mm.set(self.DEFAULTS['margin_vertical_mm'])
        self.v_vertical_pos.set(self.DEFAULTS['vertical_pos'])
        self.v_alignment.set(self.DEFAULTS['alignment'])
        self.v_mode.set(self.DEFAULTS['mode'])
        self.v_start_page.set(self.DEFAULTS['start_page'])
        self.v_start_number.set(self.DEFAULTS['start_number'])
        self.v_font_name.set(self.DEFAULTS['font_name'])
        self.v_font_size.set(self.DEFAULTS['font_size'])
        self.v_mirror_margins.set(self.DEFAULTS['mirror_margins'] == 'True')
        self.v_format_type.set(self.DEFAULTS['format_type'])

    def center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - w) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - h) // 2
        self.geometry(f'+{x}+{y}')

    def build_ui(self):
        main_frame = ttk.Frame(self, padding="6")
        main_frame.pack(fill="both", expand=True)

        # Create left and right frames for two-column layout
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))
        
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side="right", fill="y")

        PADX_GROUP = 8
        PADY_GROUP = (8, 0)
        ENTRY_WIDTH = 4

        # 1. Marginesy poziome i lustrzane
        config_frame = ttk.LabelFrame(left_frame, text="Marginesy poziome [mm]")
        config_frame.pack(fill="x", padx=PADX_GROUP, pady=PADY_GROUP)
        config_inner = ttk.Frame(config_frame)
        config_inner.pack(anchor='w', padx=2, pady=(8, 2))
        ttk.Label(config_inner, text="Lewy:").pack(side='left', padx=(0,4))
        left_entry = ttk.Entry(config_inner, textvariable=self.v_margin_left, width=ENTRY_WIDTH, validate="key", validatecommand=self.vcmd_200)
        left_entry.pack(side='left', padx=(0,10))
        ttk.Label(config_inner, text="Prawy:").pack(side='left', padx=(0,4))
        right_entry = ttk.Entry(config_inner, textvariable=self.v_margin_right, width=ENTRY_WIDTH, validate="key", validatecommand=self.vcmd_200)
        right_entry.pack(side='left', padx=(0,10))
        # Wspólny komunikat w tej samej linii z polami marginesów
        #ttk.Label(config_inner, text="(zakres 1–200 mm)", foreground="gray").pack(side='left', padx=(8,0))
        ttk.Checkbutton(config_frame, text="Plik ma marginesy lustrzane", variable=self.v_mirror_margins).pack(anchor='w', padx=2, pady=(6,6))

        # 2. Położenie
        pos_frame = ttk.LabelFrame(left_frame, text="Położenie numeru strony")
        pos_frame.pack(fill="x", padx=PADX_GROUP, pady=PADY_GROUP)
        row_idx = 0
        ttk.Label(pos_frame, text="Od krawędzi:").grid(row=row_idx, column=0, sticky="w", padx=(2,4), pady=(2,2))
        vertical_entry = ttk.Entry(pos_frame, textvariable=self.v_margin_vertical_mm, width=ENTRY_WIDTH, validate="key", validatecommand=self.vcmd_200)
        vertical_entry.grid(row=row_idx, column=1, sticky="w", padx=(0,2), pady=(2,2))
        # Komunikat w tej samej linii
        #ttk.Label(pos_frame, text="(zakres 1–200 mm)", foreground="gray").grid(row=row_idx, column=2, sticky="w", padx=(8,2))
        row_idx += 1

        # Radiobuttony PION
        ttk.Label(pos_frame, text="Pion:").grid(row=row_idx, column=0, sticky="w", padx=(2,4), pady=(2,2))
        ttk.Radiobutton(pos_frame, text="Nagłówek", variable=self.v_vertical_pos, value='gora').grid(row=row_idx, column=1, sticky="w", padx=(0,4))
        ttk.Radiobutton(pos_frame, text="Stopka", variable=self.v_vertical_pos, value='dol').grid(row=row_idx, column=2, sticky="w", padx=(0,2))
        row_idx += 1

        # Radiobuttony POZIOM
        ttk.Label(pos_frame, text="Poziom:").grid(row=row_idx, column=0, sticky="w", padx=(2,4), pady=(2,2))
        ttk.Radiobutton(pos_frame, text="Lewo", variable=self.v_alignment, value='lewa').grid(row=row_idx, column=1, sticky="w", padx=(0,4))
        ttk.Radiobutton(pos_frame, text="Środek", variable=self.v_alignment, value='srodek').grid(row=row_idx, column=2, sticky="w", padx=(0,4))
        ttk.Radiobutton(pos_frame, text="Prawo", variable=self.v_alignment, value='prawa').grid(row=row_idx, column=3, sticky="w", padx=(0,2))
        row_idx += 1

        # Radiobuttony TRYB
        ttk.Label(pos_frame, text="Tryb:").grid(row=row_idx, column=0, sticky="w", padx=(2,4), pady=(2,2))
        ttk.Radiobutton(pos_frame, text="Normalna", variable=self.v_mode, value='normalna').grid(row=row_idx, column=1, sticky="w", padx=(0,4))
        ttk.Radiobutton(pos_frame, text="Lustrzana", variable=self.v_mode, value='lustrzana').grid(row=row_idx, column=2, sticky="w", padx=(0,2))
        row_idx += 1

        # 3. Liczniki startowe
        counter_frame = ttk.LabelFrame(left_frame, text="Wartość numeracji")
        counter_frame.pack(fill="x", padx=PADX_GROUP, pady=(8,0))
        counter_inner = ttk.Frame(counter_frame)
        counter_inner.pack(fill="x", padx=2, pady=(0,0))
        ttk.Label(counter_inner, text="Licznik numeracji zacznij od numeru:").grid(row=0, column=0, sticky="w", padx=(2,4), pady=(0,4))
        start_number_entry = ttk.Entry(counter_inner, textvariable=self.v_start_number, width=ENTRY_WIDTH, validate="key", validatecommand=self.vcmd_9999)
        start_number_entry.grid(row=0, column=1, sticky="w", padx=(0,2), pady=(0,4))
        # Brak komunikatu zakresu pod licznikiem!

        # 4. Czcionka i format
        style_frame = ttk.LabelFrame(left_frame, text="Czcionka i format numeracji")
        style_frame.pack(fill="x", padx=PADX_GROUP, pady=PADY_GROUP)
        font_row = ttk.Frame(style_frame)
        font_row.pack(anchor='w', padx=2, pady=(8, 2))
        ttk.Label(font_row, text="Czcionka:").pack(side='left', padx=(0,6))
        font_combo = ttk.Combobox(font_row, textvariable=self.v_font_name, values=self.font_options, state='readonly', width=16)
        font_combo.pack(side='left', padx=(0,10))
        ttk.Label(font_row, text="Rozmiar [pt]:").pack(side='left', padx=(0,6))
        size_combo = ttk.Combobox(font_row, textvariable=self.v_font_size, values=self.size_options, state='readonly', width=ENTRY_WIDTH)
        size_combo.pack(side='left', padx=(0,0))

        f_frame = ttk.Frame(style_frame)
        f_frame.pack(anchor='w', padx=2, pady=(8, 6))
        ttk.Label(f_frame, text="Format:").pack(side='left', padx=(0,6))
        ttk.Radiobutton(f_frame, text="Standardowy (1, 2...)", variable=self.v_format_type, value='simple').pack(side='left', padx=(0,6))
        ttk.Radiobutton(f_frame, text="Strona 1 z 99", variable=self.v_format_type, value='full').pack(side='left', padx=(0,0))

        # 5. Przyciski
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill='x', pady=(8,6))
        ttk.Button(button_frame, text="Wstaw", command=self.ok).pack(side='left', expand=True, padx=5)
        ttk.Button(button_frame, text="Domyślne", command=self.restore_defaults).pack(side='left', expand=True, padx=5)
        ttk.Button(button_frame, text="Anuluj", command=self.cancel).pack(side='right', expand=True, padx=5)
        
        # 6. Profile panel on the right
        profile_frame = ttk.LabelFrame(right_frame, text="Profile użytkownika")
        profile_frame.pack(fill="both", expand=True, padx=(0, 8), pady=PADY_GROUP)
        
        # Listbox with scrollbar
        listbox_frame = ttk.Frame(profile_frame)
        listbox_frame.pack(fill="both", expand=True, padx=4, pady=4)
        
        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.profile_listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, width=20, height=15)
        self.profile_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.profile_listbox.yview)
        self.profile_listbox.bind('<Double-Button-1>', lambda event: self.load_profile())
        
        # Profile buttons
        profile_btn_frame = ttk.Frame(profile_frame)
        profile_btn_frame.pack(fill="x", padx=4, pady=(0, 4))
        
        ttk.Button(profile_btn_frame, text="Zapisz", command=self.save_profile).pack(fill="x", pady=2)
        ttk.Button(profile_btn_frame, text="Wczytaj", command=self.load_profile).pack(fill="x", pady=2)
        ttk.Button(profile_btn_frame, text="Usuń", command=self.delete_profile).pack(fill="x", pady=2)
        
        # Load existing profiles
        self.refresh_profile_list()

    def ok(self, event=None):
        try:
            # Walidacja końcowa
            fields = [
                (self.v_margin_left.get(), 1, 200, "Lewy margines"),
                (self.v_margin_right.get(), 1, 200, "Prawy margines"),
                (self.v_margin_vertical_mm.get(), 1, 200, "Od krawędzi"),
                (self.v_start_number.get(), 1, 9999, "Licznik numeracji"),
            ]
            for val, minv, maxv, label in fields:
                if not validate_float_range(val, minv, maxv):
                    raise ValueError(f"{label}: dozwolony zakres to {minv}–{maxv}")

            start_page_val = int(self.v_start_page.get())
            if start_page_val < 1:
                raise ValueError("Numer początkowej strony musi być >= 1.")

            result = {
                'margin_left_mm': float(self.v_margin_left.get().replace(',', '.')),
                'margin_right_mm': float(self.v_margin_right.get().replace(',', '.')),
                'margin_vertical_mm': float(self.v_margin_vertical_mm.get().replace(',', '.')),
                'vertical_pos': self.v_vertical_pos.get(),
                'alignment': self.v_alignment.get(),
                'mode': self.v_mode.get(),
                'start_num': int(self.v_start_number.get()),
                'start_page_idx': start_page_val - 1,
                'font_name': self.v_font_name.get().strip(),
                'font_size': float(self.v_font_size.get().replace(',', '.')),
                'mirror_margins': self.v_mirror_margins.get(),
                'format_type': self.v_format_type.get()
            }
            self.result = result
            # Zapisz preferencje przed zamknięciem
            self._save_prefs()
            self.destroy()
        except Exception as e:
            custom_messagebox(self, "Błąd wprowadzania", f"Sprawdź wprowadzone wartości: {e}", typ="error")

    def cancel(self, event=None):
        self.result = None
        self.destroy()
    
    def get_current_settings(self):
        """Pobiera aktualne ustawienia dialogu jako słownik"""
        return {
            'margin_left': self.v_margin_left.get(),
            'margin_right': self.v_margin_right.get(),
            'margin_vertical_mm': self.v_margin_vertical_mm.get(),
            'vertical_pos': self.v_vertical_pos.get(),
            'alignment': self.v_alignment.get(),
            'mode': self.v_mode.get(),
            'start_page': self.v_start_page.get(),
            'start_number': self.v_start_number.get(),
            'font_name': self.v_font_name.get(),
            'font_size': self.v_font_size.get(),
            'mirror_margins': str(self.v_mirror_margins.get()),
            'format_type': self.v_format_type.get(),
        }
    
    def apply_settings(self, settings):
        """Ustawia wartości dialogu ze słownika ustawień"""
        self.v_margin_left.set(settings.get('margin_left', self.DEFAULTS['margin_left']))
        self.v_margin_right.set(settings.get('margin_right', self.DEFAULTS['margin_right']))
        self.v_margin_vertical_mm.set(settings.get('margin_vertical_mm', self.DEFAULTS['margin_vertical_mm']))
        self.v_vertical_pos.set(settings.get('vertical_pos', self.DEFAULTS['vertical_pos']))
        self.v_alignment.set(settings.get('alignment', self.DEFAULTS['alignment']))
        self.v_mode.set(settings.get('mode', self.DEFAULTS['mode']))
        self.v_start_page.set(settings.get('start_page', self.DEFAULTS['start_page']))
        self.v_start_number.set(settings.get('start_number', self.DEFAULTS['start_number']))
        self.v_font_name.set(settings.get('font_name', self.DEFAULTS['font_name']))
        self.v_font_size.set(settings.get('font_size', self.DEFAULTS['font_size']))
        self.v_mirror_margins.set(settings.get('mirror_margins', self.DEFAULTS['mirror_margins']) == 'True')
        self.v_format_type.set(settings.get('format_type', self.DEFAULTS['format_type']))
    
    def refresh_profile_list(self):
        """Odświeża listę profili w listbox"""
        self.profile_listbox.delete(0, tk.END)
        if self.prefs_manager:
            profiles = self.prefs_manager.get_profiles('PageNumberingDialogProfiles')
            for profile_name in sorted(profiles.keys()):
                self.profile_listbox.insert(tk.END, profile_name)
    
    def save_profile(self):
        """Zapisuje aktualny profil"""
        if not self.prefs_manager:
            return
        
        # Domyślna nazwa profilu: "margines_lewy - margines_prawy"
        default_name = f"{self.v_margin_left.get()} - {self.v_margin_right.get()}"
        
        # Dialog do podania nazwy profilu
        dialog = tk.Toplevel(self)
        dialog.title("Zapisz profil")
        dialog.transient(self)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Nazwa profilu:").pack(padx=10, pady=(10, 5))
        name_var = tk.StringVar(value=default_name)
        entry = ttk.Entry(dialog, textvariable=name_var, width=30)
        entry.pack(padx=10, pady=5)
        entry.select_range(0, tk.END)
        entry.focus()
        
        result = {'saved': False}
        
        def save():
            name = name_var.get().strip()
            if not name:
                custom_messagebox(dialog, "Błąd", "Nazwa profilu nie może być pusta", typ="warning")
                return
            
            profiles = self.prefs_manager.get_profiles('PageNumberingDialogProfiles')
            
            # Sprawdź czy profil już istnieje
            if name in profiles:
                if not custom_messagebox(dialog, "Potwierdzenie", f"Profil '{name}' już istnieje. Czy chcesz go nadpisać?", typ="question"):
                    return
            
            # Zapisz profil
            profiles[name] = self.get_current_settings()
            self.prefs_manager.save_profiles('PageNumberingDialogProfiles', profiles)
            result['saved'] = True
            dialog.destroy()
        
        def cancel_save():
            dialog.destroy()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Zapisz", command=save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Anuluj", command=cancel_save).pack(side="left", padx=5)
        
        dialog.bind('<Return>', lambda e: save())
        dialog.bind('<Escape>', lambda e: cancel_save())
        
        # Center dialog
        dialog.update_idletasks()
        w = dialog.winfo_width()
        h = dialog.winfo_height()
        x = self.winfo_x() + (self.winfo_width() - w) // 2
        y = self.winfo_y() + (self.winfo_height() - h) // 2
        dialog.geometry(f'+{x}+{y}')
        
        dialog.wait_window()
        
        if result['saved']:
            self.refresh_profile_list()
    
    def load_profile(self):
        """Wczytuje wybrany profil"""
        if not self.prefs_manager:
            return
        
        selection = self.profile_listbox.curselection()
        if not selection:
            custom_messagebox(self, "Informacja", "Wybierz profil z listy", typ="info")
            return
        
        profile_name = self.profile_listbox.get(selection[0])
        profiles = self.prefs_manager.get_profiles('PageNumberingDialogProfiles')
        
        if profile_name in profiles:
            self.apply_settings(profiles[profile_name])
        else:
            custom_messagebox(self, "Błąd", "Profil nie istnieje", typ="error")
            self.refresh_profile_list()
    
    def delete_profile(self):
        """Usuwa wybrany profil"""
        if not self.prefs_manager:
            return
        
        selection = self.profile_listbox.curselection()
        if not selection:
            custom_messagebox(self, "Informacja", "Wybierz profil do usunięcia", typ="info")
            return
        
        profile_name = self.profile_listbox.get(selection[0])
        
        if custom_messagebox(self, "Potwierdzenie", f"Czy na pewno chcesz usunąć profil '{profile_name}'?", typ="question"):
            profiles = self.prefs_manager.get_profiles('PageNumberingDialogProfiles')
            if profile_name in profiles:
                del profiles[profile_name]
                self.prefs_manager.save_profiles('PageNumberingDialogProfiles', profiles)
                self.refresh_profile_list()
        
import tkinter as tk
from tkinter import ttk, messagebox

