import tkinter as tk
from tkinter import ttk

from utils import custom_messagebox


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
        if self.viewer.macro_manager.macro_exists(name):
            custom_messagebox(self, "Błąd", f"Makro o nazwie '{name}' już istnieje. Wybierz inną nazwę.", typ="error")
            return
        
        self.macro_name = name
        self.recording = True
        
        # Update UI state
        self.name_entry.config(state=tk.DISABLED)
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text=f"Nagrywanie makra '{name}' w toku...", foreground="red")
        
        # Start recording in MacroManager
        self.viewer.macro_manager.start_recording(name)
        self.viewer._update_status(f"Nagrywanie makra '{name}'...")
    
    def on_stop(self):
        """Stop recording and save macro"""
        actions_count = self.viewer.macro_manager.get_actions_count()
        if actions_count == 0:
            custom_messagebox(self, "Informacja", "Makro nie zawiera żadnych akcji.", typ="info")
            self.on_cancel()
            return
        
        # Stop recording and get recorded actions
        macro_name, actions = self.viewer.macro_manager.stop_recording()
        
        # Save macro
        self.viewer.macro_manager.save_macro(macro_name, actions)
        
        custom_messagebox(
            self,
            "Sukces",
            f"Makro '{macro_name}' zostało zapisane z {actions_count} akcjami.",
            typ="info"
        )
        
        self.viewer._update_status(f"Makro '{macro_name}' zapisane.")
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


