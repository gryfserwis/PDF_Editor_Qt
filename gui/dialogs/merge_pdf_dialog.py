import tkinter as tk
from tkinter import filedialog, ttk
import fitz

from utils import custom_messagebox


class MergePDFDialog(tk.Toplevel):
    """Okno dialogowe do scalania wielu plików PDF"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Scalanie plików PDF")
        self.transient(parent)
        self.grab_set()
        self.resizable(True, True)
        self.geometry("400x400")
        self.geometry
        self.minsize(400, 400)
        self.pdf_files = []  # Lista ścieżek do plików PDF
        
        self.build_ui()
        self.center_dialog(parent)
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        
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
        
        # Nagłówek
        #ttk.Label(main_frame, text="Dodaj pliki PDF do scalenia:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 8))
        
        # Frame dla listy i przycisków
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True, pady=(0, 8))
        
        # Lista plików (węższa - z lewej strony)
        list_frame = ttk.Frame(content_frame)
        list_frame.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.files_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=15)
        self.files_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.files_listbox.yview)
        
        # Przyciski zarządzania listą (w rzędzie po prawej)
        buttons_frame = ttk.Frame(content_frame)
        buttons_frame.pack(side="right", fill="y", padx=(8, 0))
        
        ttk.Button(buttons_frame, text="Dodaj pliki...", command=self.add_files, width=15).pack(pady=(0, 4))
        ttk.Button(buttons_frame, text="Usuń zaznaczony", command=self.remove_selected, width=15).pack(pady=4)
        ttk.Button(buttons_frame, text="Przesuń w górę", command=self.move_up, width=15).pack(pady=4)
        ttk.Button(buttons_frame, text="Przesuń w dół", command=self.move_down, width=15).pack(pady=4)
        
        # Przyciski akcji
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill="x")
        
        ttk.Button(action_frame, text="Scal i zapisz...", command=self.merge_and_save, width=15).pack(side="left", padx=(0, 4))
        ttk.Button(action_frame, text="Anuluj", command=self.cancel, width=15).pack(side="left", padx=4)
    
    def add_files(self):
        """Dodaj pliki PDF do listy"""
        files = filedialog.askopenfilenames(
            title="Wybierz pliki PDF do scalenia",
            filetypes=[("Pliki PDF", "*.pdf"), ("Wszystkie pliki", "*.*")]
        )
        for file in files:
            if file not in self.pdf_files:
                self.pdf_files.append(file)
                self.files_listbox.insert(tk.END, os.path.basename(file))
    
    def remove_selected(self):
        """Usuń zaznaczony plik z listy"""
        selection = self.files_listbox.curselection()
        if selection:
            index = selection[0]
            self.files_listbox.delete(index)
            self.pdf_files.pop(index)
    
    def move_up(self):
        """Przesuń zaznaczony plik w górę"""
        selection = self.files_listbox.curselection()
        if selection and selection[0] > 0:
            index = selection[0]
            # Zamień w liście
            self.pdf_files[index], self.pdf_files[index - 1] = self.pdf_files[index - 1], self.pdf_files[index]
            # Odśwież listbox
            self.refresh_listbox()
            self.files_listbox.selection_set(index - 1)
    
    def move_down(self):
        """Przesuń zaznaczony plik w dół"""
        selection = self.files_listbox.curselection()
        if selection and selection[0] < len(self.pdf_files) - 1:
            index = selection[0]
            # Zamień w liście
            self.pdf_files[index], self.pdf_files[index + 1] = self.pdf_files[index + 1], self.pdf_files[index]
            # Odśwież listbox
            self.refresh_listbox()
            self.files_listbox.selection_set(index + 1)
    
    def refresh_listbox(self):
        """Odśwież zawartość listbox"""
        self.files_listbox.delete(0, tk.END)
        for file in self.pdf_files:
            self.files_listbox.insert(tk.END, os.path.basename(file))
    
    def _ask_password_dialog(self, filepath):
        """Wyświetla dialog z prośbą o hasło do pliku PDF.
        Zwraca hasło lub None jeśli użytkownik anulował."""
        
        dialog = tk.Toplevel(self)
        dialog.title("Plik PDF wymaga hasła")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        main_frame = ttk.Frame(dialog, padding="12")
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text=f"Plik {os.path.basename(filepath)} jest zabezpieczony hasłem.").pack(anchor="w", pady=(0, 8))
        ttk.Label(main_frame, text="Wprowadź hasło:").pack(anchor="w", pady=(0, 4))
        
        password_var = tk.StringVar()
        password_entry = ttk.Entry(main_frame, textvariable=password_var, show="*", width=30)
        password_entry.pack(fill="x", pady=(0, 12))
        
        result = [None]
        
        def on_ok():
            result[0] = password_var.get()
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack()
        ttk.Button(button_frame, text="OK", command=on_ok, width=10).pack(side="left", padx=4)
        ttk.Button(button_frame, text="Anuluj", command=on_cancel, width=10).pack(side="left", padx=4)
        
        password_entry.focus_set()
        dialog.bind("<Return>", lambda e: on_ok())
        dialog.bind("<Escape>", lambda e: on_cancel())
        
        # Wyśrodkuj
        dialog.update_idletasks()
        dialog_w = dialog.winfo_width()
        dialog_h = dialog.winfo_height()
        parent_x = self.winfo_rootx()
        parent_y = self.winfo_rooty()
        parent_w = self.winfo_width()
        parent_h = self.winfo_height()
        x = parent_x + (parent_w - dialog_w) // 2
        y = parent_y + (parent_h - dialog_h) // 2
        dialog.geometry(f"+{x}+{y}")
        
        dialog.wait_window()
        
        return result[0]
    
    def merge_and_save(self):
        """Scal pliki PDF i zapisz"""
        if not self.pdf_files:
            custom_messagebox(self, "Błąd", "Dodaj przynajmniej jeden plik PDF.", typ="error")
            return
        
        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Pliki PDF", "*.pdf")],
            title="Zapisz scalony PDF"
        )
        
        if not output_path:
            return
        
        try:
            # Użyj PyMuPDF do scalania
            merged_doc = fitz.open()
            
            for pdf_path in self.pdf_files:
                try:
                    doc = fitz.open(pdf_path)
                    
                    # Sprawdź czy dokument jest zaszyfrowany
                    if doc.is_encrypted:
                        password = self._ask_password_dialog(pdf_path)
                        
                        if password is None:
                            # Użytkownik anulował
                            doc.close()
                            custom_messagebox(self, "Informacja", f"Pominięto plik {os.path.basename(pdf_path)} (anulowano wprowadzenie hasła).", typ="info")
                            continue
                        
                        # Spróbuj uwierzytelnić
                        if not doc.authenticate(password):
                            doc.close()
                            custom_messagebox(self, "Ostrzeżenie", f"Nieprawidłowe hasło dla pliku {os.path.basename(pdf_path)}. Pominięto.", typ="warning")
                            continue
                    
                    merged_doc.insert_pdf(doc)
                    doc.close()
                except Exception as e:
                    custom_messagebox(self, "Ostrzeżenie", f"Nie udało się dodać pliku {os.path.basename(pdf_path)}:\n{e}", typ="warning")
            
            merged_doc.save(output_path)
            merged_doc.close()
            
            custom_messagebox(self, "Sukces", f"Scalono {len(self.pdf_files)} plików PDF.\nZapisano do: {output_path}", typ="info")
            self.destroy()
        except Exception as e:
            custom_messagebox(self, "Błąd", f"Nie udało się scalić plików PDF:\n{e}", typ="error")
    
    def cancel(self):
        """Anuluj i zamknij okno"""
        self.destroy()


