"""
MacroManager - System zarządzania makrami dla PDF Editor Qt

Ten moduł zawiera klasę MacroManager oraz związane z nią dialogi, które zarządzają
systemem makr w aplikacji PDF Editor. Makra umożliwiają nagrywanie i odtwarzanie
sekwencji operacji na dokumentach PDF.

Klasy:
    MacroManager: Główna klasa zarządzająca makrami
    MacroEditDialog: Dialog do edycji makr w formacie JSON
    MacroRecordingDialog: Dialog do nagrywania nowych makr
    MacrosListDialog: Dialog do przeglądania i zarządzania listą makr

Autor: PDF Editor Qt Team
Data: 2025-10-17
"""

import tkinter as tk
from tkinter import ttk, simpledialog
import json
import re
import io
from typing import Dict, List, Any, Optional, Callable, Set

# Import from utils
from utils.messagebox import custom_messagebox


class MacroEditDialog(tk.Toplevel):
    """Dialog for editing macro actions - reorder, delete, add"""
    
    def __init__(self, parent, prefs_manager, macro_name, refresh_callback):
        super().__init__(parent)
        self.parent = parent
        self.prefs_manager = prefs_manager
        self.macro_name = macro_name
        self.refresh_callback = refresh_callback
        
        self.title(f"Edytuj makro: {macro_name}")
        self.transient(parent)
        self.grab_set()
        self.resizable(True, True)
        self.geometry("600x500")
        self.minsize(600, 500)
        # Load macro data
        macros = self.prefs_manager.get_profiles('macros')
        self.actions = macros[macro_name].get('actions', []).copy()
        
        self.build_ui()
        self.center_dialog(parent)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.load_actions()
    
    def center_dialog(self, parent):
        """Wyśrodkuj okno względem rodzica"""
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
    
    def build_ui(self):
        main_frame = ttk.Frame(self, padding="12")
        main_frame.pack(fill="both", expand=True)
        
        # Info label
        ttk.Label(main_frame, text="Edytuj makro jako tekst JSON:", 
                 font=('TkDefaultFont', 9, 'bold')).pack(anchor="w", pady=(0, 4))
        
        info_label = ttk.Label(main_frame, text="Format: [{\"action\": \"nazwa_akcji\", \"params\": {\"parametr\": \"wartość\"}}, ...]", 
                              foreground="gray")
        info_label.pack(anchor="w", pady=(0, 8))
        
        # Text editor for manual editing
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill="both", expand=True, pady=(0, 8))
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.actions_text = tk.Text(text_frame, yscrollcommand=scrollbar.set, 
                                    wrap="none", font=('Courier', 9))
        self.actions_text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.actions_text.yview)
        
        # Save/Cancel buttons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x")
        
        ttk.Button(buttons_frame, text="Zapisz", command=self.save, width=15).pack(side="left", padx=(0, 4))
        ttk.Button(buttons_frame, text="Anuluj", command=self.close, width=15).pack(side="left", padx=4)
    
    def load_actions(self):
        """Load actions into text editor as JSON"""
        self.actions_text.delete("1.0", tk.END)
        # Pretty print JSON for readability
        json_str = json.dumps(self.actions, indent=2, ensure_ascii=False)
        self.actions_text.insert("1.0", json_str)
    
    def save(self):
        """Save modified macro"""
        # Get text from editor and parse as JSON
        json_str = self.actions_text.get("1.0", tk.END).strip()
        
        try:
            actions = json.loads(json_str)
            
            # Validate that it's a list
            if not isinstance(actions, list):
                custom_messagebox(self, "Błąd", "Makro musi być listą akcji (JSON array).", typ="error")
                return
            
            # Validate that it has at least one action
            if not actions:
                custom_messagebox(self, "Błąd", "Makro musi zawierać przynajmniej jedną akcję.", typ="error")
                return
            
            # Validate each action has required structure
            for i, action in enumerate(actions):
                if not isinstance(action, dict):
                    custom_messagebox(self, "Błąd", f"Akcja #{i+1} musi być obiektem JSON.", typ="error")
                    return
                if 'action' not in action:
                    custom_messagebox(self, "Błąd", f"Akcja #{i+1} musi mieć pole 'action'.", typ="error")
                    return
            
            # Save the validated actions
            macros = self.prefs_manager.get_profiles('macros')
            macros[self.macro_name]['actions'] = actions
            self.prefs_manager.save_profiles('macros', macros)
            
            custom_messagebox(self, "Sukces", "Makro zostało zaktualizowane.", typ="info")


            if self.refresh_callback:
                self.refresh_callback()
            
            self.destroy()
            
        except json.JSONDecodeError as e:
            custom_messagebox(self, "Błąd", f"Nieprawidłowy format JSON:\n{str(e)}", typ="error")
        except Exception as e:
            custom_messagebox(self, "Błąd", f"Błąd podczas zapisywania:\n{str(e)}", typ="error")
    
    def close(self):
        """Close without saving"""
        self.destroy()


class MacroRecordingDialog(tk.Toplevel):
    """Non-blocking dialog for macro recording with Start/Stop/Cancel buttons"""
    
    def __init__(self, parent, viewer, refresh_callback=None):
        super().__init__(parent)
        self.parent = parent
        self.viewer = viewer
        self.refresh_callback = refresh_callback
        self.title("Nagrywanie makra")
        self.transient(parent)
        # Don't grab_set() - we want non-blocking dialog
        self.resizable(False, False)
        
        self.recording = False
        self.macro_name = None
        
        self.build_ui()
        self.center_dialog(parent)
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
    
    def center_dialog(self, parent):
        """Wyśrodkuj okno względem rodzica"""
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
    
    def build_ui(self):
        main_frame = ttk.Frame(self, padding="12")
        main_frame.pack(fill="both", expand=True)
        
        # Name field
        ttk.Label(main_frame, text="Nazwa makra:").grid(row=0, column=0, sticky="w", pady=2)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(main_frame, textvariable=self.name_var, width=30)
        self.name_entry.grid(row=0, column=1, sticky="ew", pady=2, padx=(8, 0))
        
        # List of recordable functions
        ttk.Label(main_frame, text="Funkcje które mogą zostać nagrane:", 
                 font=('TkDefaultFont', 9)).grid(row=1, column=0, columnspan=2, sticky="w", pady=(12, 4))
        
        functions_text = tk.Text(main_frame, height=9, width=50, wrap="word", 
                                font=('TkDefaultFont', 9), state=tk.DISABLED, 
                                relief="flat", borderwidth=0, background="SystemButtonFace")
        functions_text.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(0, 8))
        
        recordable_functions = """• Zaznaczanie konkretnych stron
• Zaznacz wszystkie / nieparzyste / parzyste / pionowe / poziome
• Obróć w lewo / w prawo
• Przesuń zawartość strony (F5)
• Usuń numerację stron (F6)
• Dodaj numerację stron (F7)
• Kadruj / Zmień rozmiar strony (F8)"""
        
        functions_text.config(state=tk.NORMAL)
        functions_text.insert("1.0", recordable_functions)
        functions_text.config(state=tk.DISABLED)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="", foreground="blue")
        self.status_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(12, 0))
        
        self.start_button = ttk.Button(button_frame, text="Rozpocznij nagrywanie", 
                                       command=self.on_start, width=20)
        self.start_button.pack(side="left", padx=4)
        
        self.stop_button = ttk.Button(button_frame, text="Zatrzymaj nagrywanie", 
                                      command=self.on_stop, width=20, state=tk.DISABLED)
        self.stop_button.pack(side="left", padx=4)
        
        self.cancel_button = ttk.Button(button_frame, text="Anuluj", 
                                        command=self.on_cancel, width=10)
        self.cancel_button.pack(side="left", padx=4)
        
        # Configure grid weights for proper resizing
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        
        self.name_entry.focus_set()
    
    def on_start(self):
        """Start recording macro"""
        name = self.name_var.get().strip()
        if not name:
            custom_messagebox(self, "Błąd", "Nazwa makra nie może być pusta.", typ="error")
            return
        
        # Check if macro with this name already exists
        macros = self.viewer.prefs_manager.get_profiles('macros')
        if name in macros:
            custom_messagebox(self, "Błąd", f"Makro o nazwie '{name}' już istnieje. Wybierz inną nazwę.", typ="error")
            return
        
        self.macro_name = name
        self.recording = True
        
        # Update UI state
        self.name_entry.config(state=tk.DISABLED)
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text=f"Nagrywanie makra '{name}' w toku...", foreground="red")
        
        # Start recording in viewer - use macro_manager
        self.viewer.macro_manager.start_recording(name)
        self.viewer._update_status(f"Nagrywanie makra '{name}'...")
    
    def on_stop(self):
        """Stop recording and save macro"""
        if not self.viewer.macro_manager.current_macro_actions:
            custom_messagebox(self, "Informacja", "Makro nie zawiera żadnych akcji.", typ="info")
            self.on_cancel()
            return
        
        # Save macro
        macros = self.viewer.prefs_manager.get_profiles('macros')
        macros[self.macro_name] = {
            'actions': self.viewer.macro_manager.current_macro_actions,
            'shortcut': ''
        }
        self.viewer.prefs_manager.save_profiles('macros', macros)
        
        custom_messagebox(
            self,
            "Sukces",
            f"Makro '{self.macro_name}' zostało zapisane z {len(self.viewer.macro_manager.current_macro_actions)} akcjami.",
            typ="info"
        )
        
        # Stop recording
        self.viewer.macro_manager.stop_recording()
        self.viewer._update_status(f"Makro '{self.macro_name}' zapisane.")
        self.viewer.refresh_macros_menu()
        
        # Call refresh callback if provided
        if self.refresh_callback:
            self.refresh_callback()
        
        self.destroy()
    
    def on_cancel(self):
        """Cancel recording"""
        if self.recording:
            self.viewer.macro_manager.cancel_recording()
            self.viewer._update_status("Nagrywanie makra anulowane.")
        self.destroy()


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
        
        self.viewer.macro_manager.run_macro(macro_name)
    
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


class MacroManager:
    """
    Zarządza systemem makr w PDF Editor Qt.
    
    MacroManager odpowiada za:
    - Nagrywanie akcji użytkownika do makr
    - Zapisywanie i wczytywanie makr z preferencji
    - Wykonywanie nagranych makr
    - Zarządzanie dialogami makr (lista, nagrywanie, edycja)
    
    Atrybuty:
        viewer: Referencja do głównego okna aplikacji (SelectablePDFViewer)
        prefs_manager: Manager preferencji do zapisywania makr
        master: Główne okno Tk
        macro_recording (bool): Czy obecnie trwa nagrywanie makra
        current_macro_actions (list): Lista akcji w obecnie nagrywanymakrze
        macro_recording_name (str): Nazwa obecnie nagrywanego makra
        macros_list_dialog: Referencja do okna listy makr
    """
    
    def __init__(self, viewer, prefs_manager, master):
        """
        Inicjalizuje MacroManager.
        
        Args:
            viewer: Instancja SelectablePDFViewer
            prefs_manager: Instancja PreferencesManager
            master: Główne okno aplikacji (Tk)
        """
        self.viewer = viewer
        self.prefs_manager = prefs_manager
        self.master = master
        
        # Macro recording state
        self.macro_recording = False
        self.current_macro_actions = []
        self.macro_recording_name = None
        self.macros_list_dialog = None
    
    def record_action(self, action_name: str, **kwargs):
        """
        Nagrywa akcję do bieżącego makra.
        
        Args:
            action_name: Nazwa akcji do nagrania
            **kwargs: Parametry akcji
        """
        if self.macro_recording:
            self.current_macro_actions.append({
                'action': action_name,
                'params': kwargs
            })
    
    def start_recording(self, macro_name: str):
        """
        Rozpoczyna nagrywanie makra.
        
        Args:
            macro_name: Nazwa makra do nagrania
        """
        self.macro_recording = True
        self.current_macro_actions = []
        self.macro_recording_name = macro_name
    
    def stop_recording(self):
        """Zatrzymuje nagrywanie makra."""
        self.macro_recording = False
        self.macro_recording_name = None
        self.current_macro_actions = []
    
    def cancel_recording(self):
        """Anuluje nagrywanie makra."""
        self.macro_recording = False
        self.macro_recording_name = None
        self.current_macro_actions = []
    
    def open_recording_dialog(self):
        """Otwiera dialog nagrywania makra."""
        MacroRecordingDialog(self.master, self.viewer)
    
    def show_macros_list(self):
        """Wyświetla listę makr użytkownika."""
        # Jeśli okno już istnieje, sprowadź je na wierzch
        if self.macros_list_dialog and self.macros_list_dialog.winfo_exists():
            self.macros_list_dialog.lift()
            self.macros_list_dialog.focus_force()
        else:
            # Utwórz nowe okno i zapisz referencję
            self.macros_list_dialog = MacrosListDialog(self.master, self.prefs_manager, self.viewer)
    
    def run_macro(self, macro_name: str):
        """
        Uruchamia makro o podanej nazwie.
        
        Args:
            macro_name: Nazwa makra do uruchomienia
        """
        macros = self.prefs_manager.get_profiles('macros')
        if macro_name not in macros:
            custom_messagebox(self.master, "Błąd", f"Makro '{macro_name}' nie istnieje.", typ="error")
            return
        
        macro = macros[macro_name]
        actions = macro.get('actions', [])
        
        if not actions:
            custom_messagebox(self.master, "Informacja", "Makro nie zawiera żadnych akcji.", typ="info")
            return
        
        # Wyłącz nagrywanie podczas wykonywania makra
        was_recording = self.macro_recording
        self.macro_recording = False
        
        try:
            for action_data in actions:
                action = action_data.get('action')
                params = action_data.get('params', {})
                
                # Mapowanie akcji na metody - simple actions without params
                if action == 'rotate_left':
                    self.viewer.rotate_selected_page(-90)
                elif action == 'rotate_right':
                    self.viewer.rotate_selected_page(90)
                elif action == 'select_all':
                    self.viewer._select_all()
                elif action == 'select_odd':
                    self.viewer._select_odd_pages()
                elif action == 'select_even':
                    self.viewer._select_even_pages()
                elif action == 'select_portrait':
                    self.viewer._select_portrait_pages()
                elif action == 'select_landscape':
                    self.viewer._select_landscape_pages()
                elif action == 'select_custom' and params:
                    indices = params.get('indices', [])
                    if isinstance(indices, int):
                        indices = [indices]
                    source_page_count = params.get('source_page_count', None)
                    self.viewer._apply_selection_by_indices(indices, macro_source_page_count=source_page_count)
                # Parameterized actions - replay with saved parameters
                elif action == 'shift_page_content' and params:
                    self.viewer._replay_shift_page_content(params)
                elif action == 'insert_page_numbers' and params:
                    self.viewer._replay_insert_page_numbers(params)
                elif action == 'remove_page_numbers' and params:
                    self.viewer._replay_remove_page_numbers(params)
                elif action == 'apply_page_crop_resize' and params:
                    self.viewer._replay_apply_page_crop_resize(params)
            
            self.viewer._update_status(f"Wykonano makro '{macro_name}' ({len(actions)} akcji).")
        except Exception as e:
            custom_messagebox(self.master, "Błąd", f"Błąd podczas wykonywania makra:\n{e}", typ="error")
        finally:
            self.macro_recording = was_recording
