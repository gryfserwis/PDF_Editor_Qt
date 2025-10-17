import tkinter as tk
from tkinter import ttk

from utils import custom_messagebox


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
        import json
        self.actions_text.delete("1.0", tk.END)
        # Pretty print JSON for readability
        json_str = json.dumps(self.actions, indent=2, ensure_ascii=False)
        self.actions_text.insert("1.0", json_str)
    
    def save(self):
        """Save modified macro"""
        import json
        
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


