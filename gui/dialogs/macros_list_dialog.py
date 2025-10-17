import tkinter as tk
from tkinter import ttk

from utils import custom_messagebox


class MacrosListDialog(tk.Toplevel):
    """Okno dialogowe listy makr użytkownika"""
    
    def __init__(self, parent, prefs_manager, viewer):
        super().__init__(parent)
        self.parent = parent
        self.prefs_manager = prefs_manager
        self.viewer = viewer
        self.title("Lista makr użytkownika")
        self.transient(parent)
        # Don't grab_set() - we want non-blocking dialog
        self.resizable(True, True)
        self.geometry("300x400")
        self.minsize(300, 400)
        self.build_ui()
        self.center_dialog(parent)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.load_macros()
    
    def center_dialog(self, parent):
        """Ustaw okno obok okna głównego (np. po prawej stronie)"""
        self.update_idletasks()
        dialog_w = self.winfo_width()
        dialog_h = self.winfo_height()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        # Ustaw po prawej stronie z odstępem 30 pikseli
        x = parent_x + parent_w + 30
        y = parent_y
        # Jeśli nie mieści się na ekranie, przenieś po lewej
        screen_w = self.winfo_screenwidth()
        if x + dialog_w > screen_w:
            x = max(0, parent_x - dialog_w - 30)
        self.geometry(f"+{x}+{y}")
    
    def build_ui(self):
        main_frame = ttk.Frame(self, padding="12")
        main_frame.pack(fill="both", expand=True)
        
        # Horizontal layout: list on left, buttons on right
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True, pady=(0, 8))
        
        # Lista makr (left side)
        list_frame = ttk.Frame(content_frame)
        list_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.macros_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=15)
        self.macros_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.macros_listbox.yview)
        
        # Bind double-click to run macro
        self.macros_listbox.bind("<Double-Button-1>", lambda e: self.run_selected())
        
        # Przyciski akcji (right side, vertical layout)
        buttons_frame = ttk.Frame(content_frame)
        buttons_frame.pack(side="right", fill="y")
        
        ttk.Button(buttons_frame, text="Uruchom", command=self.run_selected, width=15).pack(pady=(0, 4))
        ttk.Button(buttons_frame, text="Nagraj makro...", command=self.record_macro, width=15).pack(pady=4)
        #ttk.Button(buttons_frame, text="Nowe makro", command=self.new_macro, width=15).pack(pady=4)
        ttk.Button(buttons_frame, text="Duplikuj", command=self.duplicate_selected, width=15).pack(pady=4)
        ttk.Button(buttons_frame, text="Edytuj...", command=self.edit_selected, width=15).pack(pady=4)
        ttk.Button(buttons_frame, text="Usuń", command=self.delete_selected, width=15).pack(pady=4)
        ttk.Button(buttons_frame, text="Zamknij", command=self.close, width=15).pack(pady=(4, 0))
    
    def load_macros(self):
        """Wczytaj listę makr"""
        self.macros_listbox.delete(0, tk.END)
        macros = self.prefs_manager.get_profiles('macros')
        for name, data in macros.items():
            self.macros_listbox.insert(tk.END, name)
    
    def record_macro(self):
        """Otwórz okno nagrywania makra"""
        MacroRecordingDialog(self, self.viewer, refresh_callback=self.load_macros)
    
    def new_macro(self):
        """Otwórz okno nagrywania nowego makra z pustą nazwą"""
        MacroRecordingDialog(self, self.viewer, refresh_callback=self.load_macros)
    
    def duplicate_selected(self):
        """Duplikuj wybrane makro pod nową nazwą"""
        selection = self.macros_listbox.curselection()
        if not selection:
            custom_messagebox(self, "Informacja", "Wybierz makro do duplikacji.", typ="info")
            return
        
        index = selection[0]
        macros = self.prefs_manager.get_profiles('macros')
        macro_name = list(macros.keys())[index]
        
        # Ask for new name using simpledialog
        from tkinter import simpledialog
        new_name = simpledialog.askstring(
            "Duplikuj makro",
            f"Wprowadź nową nazwę dla kopii makra '{macro_name}':",
            parent=self
        )
        
        if not new_name:
            return  # User cancelled
        
        new_name = new_name.strip()
        if not new_name:
            custom_messagebox(self, "Błąd", "Nazwa makra nie może być pusta.", typ="error")
            return
        
        # Check if macro with new name already exists
        if new_name in macros:
            custom_messagebox(self, "Błąd", f"Makro o nazwie '{new_name}' już istnieje.", typ="error")
            return
        
        # Create duplicate
        macros[new_name] = macros[macro_name].copy()
        self.prefs_manager.save_profiles('macros', macros)
        self.load_macros()
        self.viewer.refresh_macros_menu()
        
        custom_messagebox(self, "Sukces", f"Makro '{macro_name}' zostało zduplikowane jako '{new_name}'.", typ="info")
    
    def run_selected(self):
        """Uruchom wybrane makro"""
        selection = self.macros_listbox.curselection()
        if not selection:
            custom_messagebox(self, "Informacja", "Wybierz makro do uruchomienia.", typ="info")
            return
        
        index = selection[0]
        macros = self.prefs_manager.get_profiles('macros')
        macro_name = list(macros.keys())[index]
        
        self.viewer.run_macro(macro_name)
    
    def edit_selected(self):
        """Edytuj wybrane makro"""
        selection = self.macros_listbox.curselection()
        if not selection:
            custom_messagebox(self, "Informacja", "Wybierz makro do edycji.", typ="info")
            return
        
        index = selection[0]
        macros = self.prefs_manager.get_profiles('macros')
        macro_name = list(macros.keys())[index]
        
        # Open edit dialog
        MacroEditDialog(self, self.prefs_manager, macro_name, self.load_macros)
    
    def delete_selected(self):
        """Usuń wybrane makro"""
        selection = self.macros_listbox.curselection()
        if not selection:
            custom_messagebox(self, "Informacja", "Wybierz makro do usunięcia.", typ="info")
            return
        
        index = selection[0]
        macros = self.prefs_manager.get_profiles('macros')
        macro_name = list(macros.keys())[index]
        
        answer = custom_messagebox(
            self,
            "Potwierdzenie",
            f"Czy na pewno usunąć makro '{macro_name}'?",
            typ="question"
        )
        
        if answer:
            del macros[macro_name]
            self.prefs_manager.save_profiles('macros', macros)
            self.load_macros()
        self.viewer.refresh_macros_menu()
    def close(self):
        """Zamknij okno"""
        # Wyczyść referencję w viewerze przed zamknięciem
        if self.viewer.macros_list_dialog == self:
            self.viewer.macros_list_dialog = None
        self.destroy()


