import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import fitz
from PIL import Image, ImageTk
import io
import math 
import os
import sys 
import re 
from typing import Optional, List, Set, Dict, Union
from datetime import date, datetime 
import pypdf
from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import RectangleObject, FloatObject, ArrayObject
# ArrayObject jest nadal potrzebne, jeśli użyjesz add_transformation, choć FloatObject 
# wystarczyłoby, jeśli pypdf je konwertuje. Zostawiam dla pełnej kompatybilności.
from pypdf.generic import NameObject # Dodaj import dla NameObject
import json

# Import from refactored modules
from utils import (
    BASE_DIR, ICON_FOLDER, FOCUS_HIGHLIGHT_COLOR, FOCUS_HIGHLIGHT_WIDTH,
    PROGRAM_TITLE, PROGRAM_VERSION, PROGRAM_DATE,
    A4_WIDTH_POINTS, A4_HEIGHT_POINTS, MM_TO_POINTS,
    BG_IMPORT, GRAY_FG, COPYRIGHT_INFO,
    BG_PRIMARY, BG_SECONDARY, BG_BUTTON_DEFAULT, FG_TEXT,
    mm2pt, validate_float_range, generate_unique_export_filename, resource_path,
    custom_messagebox, Tooltip
)
from core import PreferencesManager, PDFTools, MacroManager
from gui.dialogs import (
    PreferencesDialog, PageCropResizeDialog, PageNumberingDialog,
    PageNumberMarginDialog, ShiftContentDialog, ImageImportSettingsDialog,
    EnhancedPageRangeDialog, MergePageGridDialog, MacroEditDialog,
    MacroRecordingDialog, MacrosListDialog, MergePDFDialog, PDFAnalysisDialog
)

# === DIALOGS AND UI COMPONENTS ===
# PreferencesManager has been moved to core/preferences_manager.py

class SelectablePDFViewer:
    MM_TO_POINTS = 72 / 25.4 # ~2.8346
    # === NOWE STAŁE DLA MARGINESU ===
    # Określamy wysokość marginesu do skanowania w milimetrach [np. 20 mm]
    MARGIN_HEIGHT_MM = 20
    # Obliczamy wysokość w punktach, używając Twojej stałej konwersji
    MARGIN_HEIGHT_PT = MARGIN_HEIGHT_MM * MM_TO_POINTS 
    import io
    import fitz
    from pypdf import PdfReader, PdfWriter, Transformation
    from pypdf.generic import RectangleObject, FloatObject
    from tkinterdnd2 import DND_FILES, TkinterDnD

    MM_TO_POINTS = 72 / 25.4

    #def _focus_by_mouse(self, page_index):
    #   self.hovered_page_index = page_index
    #    self.update_focus_display(hide_mouse_focus=False)

    def run_compare_program(self):
        import subprocess
        import sys

        # Pobierz pełne ścieżki do ostatnio otwartego i zapisanego pliku (dla compare.exe)
        last_opened = self.prefs_manager.get('last_opened_file', '')
        last_saved = self.prefs_manager.get('last_saved_file', '')

        # Ścieżka do compare.exe w tym samym katalogu co PDFEditor.py
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
        else:
            exe_dir = os.path.dirname(os.path.abspath(__file__))
        compare_exe = os.path.join(exe_dir, 'compare.exe')

        # Skonstruuj listę argumentów
        args = [compare_exe]
        if last_opened and os.path.isfile(last_opened):
            args.append(last_opened)
            if last_saved and os.path.isfile(last_saved):
                args.append(last_saved)

        print("Wywołanie compare.exe z argumentami:", args)  # Wypisz w konsoli

        try:
            subprocess.Popen(args)
        except Exception as e:
            custom_messagebox(self.master, "Błąd", f"Nie udało się uruchomić compare.exe:\n{e}", typ="error")
            
    def _setup_drag_and_drop_file(self):
        # Rejestrujemy canvas do odbioru plików DND
        self.master.drop_target_register(self.DND_FILES)
        self.master.dnd_bind('<<Drop>>', self._on_drop_file)

    import re

    def _on_drop_file(self, event):
        filepath = event.data.strip()
        # Rozbij na ścieżki w klamrach lub bez klamr
        # Obsługuje: {ścieżka 1} {ścieżka 2} lub ścieżka1 ścieżka2
        # Działa też dla pojedynczego pliku ze spacją
        pattern = r'\{[^}]+\}|[^\s]+'
        paths = re.findall(pattern, filepath)
        paths = [p[1:-1] if p.startswith('{') and p.endswith('}') else p for p in paths]
        for path in paths:
            if path.lower().endswith('.pdf'):
                if self.pdf_document is None:
                    self.open_pdf(filepath=path)
                else:
                    self.import_pdf_after_active_page(filepath=path)
                return
            elif path.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff')):
                if self.pdf_document is None:
                    self.open_image_as_new_pdf(filepath=path)
                else:
                    self.import_image_to_new_page(filepath=path)
                return
        self._update_status(f"Można przeciągać tylko pliki PDF lub obrazy! Otrzymano: {filepath}")

    def _crop_pages(self, pdf_bytes, selected_indices, top_mm, bottom_mm, left_mm, right_mm, reposition=False, pos_mode="center", offset_x_mm=0, offset_y_mm=0):
        """Wrapper dla PDFTools.crop_pages z integracją GUI."""
        def progress_callback(current, total):
            if current == 0:
                self.show_progressbar(maximum=total)
            self.update_progressbar(current)
            if current == total:
                self.hide_progressbar()
        
        return self.pdf_tools.crop_pages(
            pdf_bytes, selected_indices, top_mm, bottom_mm, left_mm, right_mm,
            reposition, pos_mode, offset_x_mm, offset_y_mm,
            progress_callback=self._update_status,
            progressbar_callback=progress_callback
        )
        
    import fitz  # PyMuPDF

    def _mask_crop_pages(self, pdf_bytes, selected_indices, top_mm, bottom_mm, left_mm, right_mm):
        """Wrapper dla PDFTools.mask_crop_pages z integracją GUI."""
        def progress_callback(current, total):
            if current == 0:
                self.show_progressbar(maximum=total)
            self.update_progressbar(current)
            if current == total:
                self.hide_progressbar()
        
        return self.pdf_tools.mask_crop_pages(
            pdf_bytes, selected_indices, top_mm, bottom_mm, left_mm, right_mm,
            progress_callback=self._update_status,
            progressbar_callback=progress_callback
        )

    def _resize_scale(self, pdf_bytes, selected_indices, width_mm, height_mm):
        """Wrapper dla PDFTools.resize_pages_with_scale z integracją GUI."""
        def progress_callback(current, total):
            if current == 0:
                self.show_progressbar(maximum=total)
            self.update_progressbar(current)
            if current == total:
                self.hide_progressbar()
        
        return self.pdf_tools.resize_pages_with_scale(
            pdf_bytes, selected_indices, width_mm, height_mm,
            progress_callback=self._update_status,
            progressbar_callback=progress_callback
        )

    def _resize_noscale(self, pdf_bytes, selected_indices, width_mm, height_mm, pos_mode="center", offset_x_mm=0, offset_y_mm=0):
        """Wrapper dla PDFTools.resize_pages_without_scale z integracją GUI."""
        def progress_callback(current, total):
            if current == 0:
                self.show_progressbar(maximum=total)
            self.update_progressbar(current)
            if current == total:
                self.hide_progressbar()
        
        return self.pdf_tools.resize_pages_without_scale(
            pdf_bytes, selected_indices, width_mm, height_mm,
            pos_mode, offset_x_mm, offset_y_mm,
            progress_callback=self._update_status,
            progressbar_callback=progress_callback
        )

    def apply_page_crop_resize_dialog(self):
        """
        Wywołaj ten kod np. w obsłudze przycisku „Kadruj/Zmień rozmiar”.
        """
        if not self.pdf_document or not self.selected_pages:
            self._update_status("Musisz zaznaczyć przynajmniej jedną stronę PDF.")
            return

        dialog = PageCropResizeDialog(self.master, self.prefs_manager)
        result = dialog.result
        if not result:
            self._update_status("Anulowano operację.")
            return

        pdf_bytes_export = io.BytesIO()
        self.pdf_document.save(pdf_bytes_export)
        pdf_bytes_export.seek(0)
        pdf_bytes_val = pdf_bytes_export.read()
        indices = sorted(list(self.selected_pages))

        crop_mode = result["crop_mode"]
        resize_mode = result["resize_mode"]

        try:
            if crop_mode == "crop_only" and resize_mode == "noresize":
                new_pdf_bytes = self._mask_crop_pages(
                    pdf_bytes_val, indices,
                    result["crop_top_mm"], result["crop_bottom_mm"],
                    result["crop_left_mm"], result["crop_right_mm"],
                )
                msg = "Dodano białe maski zamiast przycinania stron."
            elif crop_mode == "crop_resize" and resize_mode == "noresize":
                new_pdf_bytes = self._crop_pages(
                    pdf_bytes_val, indices,
                    result["crop_top_mm"], result["crop_bottom_mm"],
                    result["crop_left_mm"], result["crop_right_mm"],
                    reposition=False
                )
                msg = "Zastosowano przycięcie i zmianę rozmiaru arkusza."
            elif resize_mode == "resize_scale":
                new_pdf_bytes = self._resize_scale(
                    pdf_bytes_val, indices,
                    result["target_width_mm"], result["target_height_mm"]
                )
                msg = "Zmieniono rozmiar i skalowano zawartość."
            elif resize_mode == "resize_noscale":
                new_pdf_bytes = self._resize_noscale(
                    pdf_bytes_val, indices,
                    result["target_width_mm"], result["target_height_mm"],
                    pos_mode=result.get("position_mode") or "center",
                    offset_x_mm=result.get("offset_x_mm") or 0,
                    offset_y_mm=result.get("offset_y_mm") or 0,
                )
                msg = "Zmieniono rozmiar strony (bez skalowania zawartości)."
            else:
                self._update_status("Nie wybrano żadnej operacji do wykonania.")
                return
            self._save_state_to_undo() 
            self.pdf_document.close()
            self.pdf_document = fitz.open("pdf", new_pdf_bytes)
            self._update_status(msg)
            
            # Optymalizacja: odśwież tylko zmienione miniatury (nie zmienia się liczba stron)
            self.show_progressbar(maximum=len(indices))
            for i, page_index in enumerate(indices):
                self._update_status("Operacja zakończona. Odświeżanie miniatur...")
                self.update_single_thumbnail(page_index)
                self.update_progressbar(i + 1)
            self.hide_progressbar()
            
            if hasattr(self, "update_selection_display"):
                self.update_selection_display()
            if hasattr(self, "update_focus_display"):
                self.update_focus_display()
            
            # Record action with all parameters
            self._record_action('apply_page_crop_resize', **result)

        except Exception as e:
            self._update_status(f"Błąd podczas przetwarzania PDF: {e}")
            import traceback; traceback.print_exc()
                
# Zakładamy, że ta funkcja jest metodą klasy PdfToolApp, 
# która ma atrybuty self.pdf_document, self.master, self.MM_TO_POINTS, 
# _save_state, _update_status i _reconfigure_grid.

    def insert_page_numbers(self):
        """
        Wstawia numerację stron, z uwzględnieniem tylko zaznaczonych stron 
        (self.selected_pages) oraz poprawnej logiki centrowania ('srodek').
        Obsługuje poprawnie pozycje lewa/prawa/środek dla wszystkich rotacji.
        """
        if not self.pdf_document:
            self._update_status("Musisz zaznaczyć przynajmniej jedną stronę PDF.")
            return

        if not hasattr(self, 'selected_pages') or not self.selected_pages:
             self._update_status("Musisz zaznaczyć przynajmniej jedną stronę PDF.")
             return
        
        dialog = PageNumberingDialog(self.master, self.prefs_manager)
        settings = dialog.result

        if settings is None:
            self._update_status("Wstawianie numeracji anulowane przez użytkownika.")
            return

        try:
            self._save_state_to_undo()
            
            selected_indices = sorted(self.selected_pages)
            
            # Deleguj do PDFTools
            def progress_callback(current, total):
                if current == 0:
                    self.show_progressbar(maximum=total)
                self.update_progressbar(current)
                if current == total:
                    self.hide_progressbar()
            
            self.pdf_tools.insert_page_numbers(
                self.pdf_document,
                selected_indices,
                settings,
                progress_callback=self._update_status,
                progressbar_callback=progress_callback
            )
            
            # Optymalizacja: odśwież tylko zmienione miniatury
            self.show_progressbar(maximum=len(selected_indices))
            for i, page_index in enumerate(selected_indices):
                self._update_status(f"Numeracja wstawiona na {len(selected_indices)} stronach. Odświeżanie miniatur...")
               
                self.update_single_thumbnail(page_index)
                self.update_progressbar(i + 1)
            self.hide_progressbar()
            
            self._update_status(f"Numeracja wstawiona na {len(selected_indices)} stronach.")
            self._record_action('insert_page_numbers', 
                start_num=settings['start_num'],
                mode=settings['mode'],
                alignment=settings['alignment'],
                vertical_pos=settings['vertical_pos'],
                mirror_margins=settings['mirror_margins'],
                format_type=settings['format_type'],
                margin_left_mm=settings['margin_left_mm'],
                margin_right_mm=settings['margin_right_mm'],
                top_mm=settings.get('top_mm', 20),
                bottom_mm=settings.get('bottom_mm', 20))

        except Exception as e:
            self.hide_progressbar()
            self._update_status(f"BŁĄD przy dodawaniu numeracji: {e}")
            custom_messagebox(self.master, "Błąd Numeracji", str(e), typ="error")
   
    def remove_page_numbers(self):
        """
        Usuwa numery stron z marginesów określonych przez użytkownika.
        """
        if not self.pdf_document or not self.selected_pages:
            self._update_status("Musisz zaznaczyć przynajmniej jedną stronę PDF.")
            return

        # Otwarcie dialogu i pobranie wartości od użytkownika
        dialog = PageNumberMarginDialog(self.master, initial_margin_mm=20, prefs_manager=self.prefs_manager)
        margins = dialog.result

        if margins is None:
            self._update_status("Usuwanie numerów stron anulowane.")
            return

        top_mm = margins['top_mm']
        bottom_mm = margins['bottom_mm']

        try:
            pages_to_process = sorted(list(self.selected_pages))
            if pages_to_process:     # Zapisz stan tylko jeśli są strony do modyfikacji
                self._save_state_to_undo()
            
            # Deleguj do PDFTools
            def progress_callback(current, total):
                if current == 0:
                    self.show_progressbar(maximum=total)
                self.update_progressbar(current)
                if current == total:
                    self.hide_progressbar()
            
            modified_count = self.pdf_tools.remove_page_numbers_by_pattern(
                self.pdf_document, pages_to_process, top_mm, bottom_mm,
                progress_callback=self._update_status,
                progressbar_callback=progress_callback
            )
            
            self.hide_progressbar()
            
            if modified_count > 0:
                # Optymalizacja: odśwież tylko zmienione miniatury
                self.show_progressbar(maximum=len(pages_to_process))
                for i, page_index in enumerate(pages_to_process):
                    self._update_status(f"Usunięto numery stron na {modified_count} stronach, używając marginesów: G={top_mm:.1f}mm, D={bottom_mm:.1f}mm. Odświeżanie miniatur...")
                    self.update_single_thumbnail(page_index)
                    self.update_progressbar(i + 1)
                self.hide_progressbar()
                
                self._update_status(f"Usunięto numery stron na {modified_count} stronach, używając marginesów: G={top_mm:.1f}mm, D={bottom_mm:.1f}mm.")
                self._record_action('remove_page_numbers', top_mm=top_mm, bottom_mm=bottom_mm)
            else:
                self._update_status(f"Nie znaleziono numerów stron w marginesach: G={top_mm:.1f}mm, D={bottom_mm:.1f}mm.")
                
        except Exception as e:
            self.hide_progressbar()
            self._update_status(f"BŁĄD: Nie udało się usunąć numerów stron: {e}")
            
    def show_shortcuts_dialog(self):
        shortcuts_left = [
            ("Otwórz PDF", "Ctrl+O"),
            ("Zapisz jako...", "Ctrl+S"),
            ("Zamknij plik", "Ctrl+Q"),
            ("Importuj PDF", "Ctrl+I"),
            ("Importuj obraz", "Ctrl+Shift+I"),
            ("Eksportuj PDF", "Ctrl+E"),
            ("Eksportuj obrazy", "Ctrl+Shift+E"),
            ("Cofnij", "Ctrl+Z"),
            ("Ponów", "Ctrl+Y"),
            ("Wytnij strony", "Ctrl+X"),
            ("Kopiuj strony", "Ctrl+C"),
            ("Wklej po", "Ctrl+V"),
            ("Wklej przed", "Ctrl+Shift+V"),
            ("Usuń strony", "Delete/Backspace"),
            ("Duplikuj strony", "Ctrl+D"),
            ("Zamień miejscami", "Ctrl+Tab"),
            ("Nowa strona po", "Ctrl+N"),
            ("Nowa strona przed", "Ctrl+Shift+N"),
        ]
        shortcuts_right = [
            ("Zaznacz wszystkie", "Ctrl+A / F4"),
            ("Nieparzyste strony", "F1"),
            ("Parzyste strony", "F2"),
            ("Pionowe strony", "Ctrl+F1"),
            ("Poziome strony", "Ctrl+F2"),
            ("Obróć w lewo", "Ctrl+Lewo"),
            ("Obróć w prawo", "Ctrl+Prawo"),
            ("Przesuń zawartość", "F5"),
            ("Usuń numery", "F6"),
            ("Wstaw numery", "F7"),
            ("Kadruj/zmień rozmiar", "F8"),
            ("Analiza PDF", "F11"),
            ("Lista makr", "F12"),
            ("Zoom +", "+"),
            ("Zoom -", "-"),
            ("Pierwsza strona", "Home"),
            ("Ostatnia strona", "End"),
            ("Poprzednia strona", "PageUp"),
            ("Następna strona", "PageDown"),
            ("Nawigacja", "Strzałki, Spacja, Esc"),
        ]

        import tkinter as tk
        dialog = tk.Toplevel(self.master)
        dialog.title("Skróty klawiszowe")
        dialog.transient(self.master)
        dialog.geometry("+10000+10000")

        bg = "white"
        grid_color = "#e3e3e3"
        screen_height = dialog.winfo_screenheight()
        max_height = int(screen_height * 0.8)
        width = 631

        outer_frame = tk.Frame(dialog, bg=bg)
        outer_frame.pack(fill="both", expand=True, padx=24, pady=24)

        canvas = tk.Canvas(outer_frame, bg=bg, highlightthickness=0)
        scrollbar = tk.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)

        scrollable_frame = tk.Frame(canvas, bg=bg, bd=1, relief="solid",
                                   highlightbackground=grid_color, highlightthickness=1)

        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.config(width=width)
        scrollable_frame.bind("<Configure>", _on_frame_configure)

        canvas.configure(yscrollcommand=scrollbar.set)

        max_rows = max(len(shortcuts_left), len(shortcuts_right))
        for i in range(max_rows):
            row_idx = i * 2
            # Lewa kolumna
            if i < len(shortcuts_left):
                op, key = shortcuts_left[i]
                l_op = tk.Label(scrollable_frame, text=op, bg=bg, anchor="w", font=("Arial", 10))
                l_key = tk.Label(scrollable_frame, text=key, bg=bg, anchor="e", font=("Arial", 10, "bold"), fg="#234")
                l_op.grid(row=row_idx, column=0, sticky="ew", padx=(10, 6), pady=(2,2))
                l_key.grid(row=row_idx, column=1, sticky="ew", padx=(2, 20), pady=(2,2))
            else:
                tk.Label(scrollable_frame, text="", bg=bg).grid(row=row_idx, column=0)
                tk.Label(scrollable_frame, text="", bg=bg).grid(row=row_idx, column=1)
            # Prawa kolumna
            if i < len(shortcuts_right):
                op, key = shortcuts_right[i]
                r_op = tk.Label(scrollable_frame, text=op, bg=bg, anchor="w", font=("Arial", 10))
                r_key = tk.Label(scrollable_frame, text=key, bg=bg, anchor="e", font=("Arial", 10, "bold"), fg="#234")
                r_op.grid(row=row_idx, column=2, sticky="ew", padx=(20, 6), pady=(2,2))
                r_key.grid(row=row_idx, column=3, sticky="ew", padx=(2, 10), pady=(2,2))
            else:
                tk.Label(scrollable_frame, text="", bg=bg).grid(row=row_idx, column=2)
                tk.Label(scrollable_frame, text="", bg=bg).grid(row=row_idx, column=3)
            if i < max_rows-1:
                for col in range(4):
                    frame = tk.Frame(scrollable_frame, bg=grid_color, height=1)
                    frame.grid(row=row_idx+1, column=col, sticky="ewns")

        for col in range(4):
            scrollable_frame.grid_columnconfigure(col, weight=1)

        dialog.update_idletasks()
        content_height = scrollable_frame.winfo_reqheight() + 48

        if content_height > max_height:
            height = max_height
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
        else:
            height = content_height
            canvas.pack(side="left", fill="both", expand=True)

        x = self.master.winfo_x() + (self.master.winfo_width() - width) // 2
        y = self.master.winfo_y() + (self.master.winfo_height() - height) // 2
        dialog.geometry(f"{width}x{height}+{x}+{y}")

        dialog.resizable(False, False)
        dialog.bind('<Escape>', lambda e: dialog.destroy())

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        dialog.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))

        dialog.focus_force()
 
    def shift_page_content(self):
        """
        Otwiera okno dialogowe i przesuwa zawartość zaznaczonych stron.
        Najpierw czyści/odświeża wybrane strony (resave przez PyMuPDF), potem wykonuje przesunięcie przez pypdf.
        Dzięki temu unika białych stron w trudnych PDF.
        """
        if not self.pdf_document or not self.selected_pages:
            self._update_status("Musisz zaznaczyć przynajmniej jedną stronę PDF.")
            return

        dialog = ShiftContentDialog(self.master, self.prefs_manager)
        result = dialog.result

        if not result or (result['x_mm'] == 0 and result['y_mm'] == 0):
            self._update_status("Anulowano lub zerowe przesunięcie.")
            return

        dx_pt = result['x_mm'] * self.MM_TO_POINTS
        dy_pt = result['y_mm'] * self.MM_TO_POINTS

        x_sign = 1 if result['x_dir'] == 'P' else -1
        y_sign = 1 if result['y_dir'] == 'G' else -1

        final_dx = dx_pt * x_sign
        final_dy = dy_pt * y_sign

        try:
            self._save_state_to_undo()

            import io
            from pypdf import PdfReader, PdfWriter, Transformation
            import fitz

            pages_to_shift = sorted(list(self.selected_pages))
            pages_to_shift_set = set(pages_to_shift)
            total_pages = len(self.pdf_document)
            
            # Update status first to ensure it's visible immediately
            self._update_status("Przesuwanie zawartości stron...")
            self.show_progressbar(maximum=total_pages * 2)  # 2 etapy: oczyszczanie i przesuwanie

            # --- 1. Resave wybranych stron przez PyMuPDF (oczyszczenie) ---
            original_pdf_bytes = self.pdf_document.tobytes()
            pymupdf_doc = fitz.open("pdf", original_pdf_bytes)
            cleaned_doc = fitz.open()
            for idx in range(len(pymupdf_doc)):
                if idx in pages_to_shift_set:
                    # Dodajemy nową stronę (oczyszczamy ją "zapisz i wczytaj")
                    temp = fitz.open()
                    temp.insert_pdf(pymupdf_doc, from_page=idx, to_page=idx)
                    cleaned_doc.insert_pdf(temp)
                    temp.close()
                else:
                    # Dodajemy oryginalną stronę bez zmian
                    cleaned_doc.insert_pdf(pymupdf_doc, from_page=idx, to_page=idx)
                self.update_progressbar(idx + 1)

            cleaned_pdf_bytes = cleaned_doc.write()
            pymupdf_doc.close()
            cleaned_doc.close()

            # --- 2. Przesuwanie przez PyPDF ---
            pdf_reader = PdfReader(io.BytesIO(cleaned_pdf_bytes))
            pdf_writer = PdfWriter()
            transform = Transformation().translate(tx=final_dx, ty=final_dy)

            for i, page in enumerate(pdf_reader.pages):
                if i in pages_to_shift_set:
                    page.add_transformation(transform)
                pdf_writer.add_page(page)
                self.update_progressbar(total_pages + i + 1)

            new_pdf_stream = io.BytesIO()
            pdf_writer.write(new_pdf_stream)
            new_pdf_bytes = new_pdf_stream.getvalue()

            # --- 3. Aktualizacja dokumentu w aplikacji przez PyMuPDF ---
            if self.pdf_document:
                self.pdf_document.close()
            import fitz
            self.pdf_document = fitz.open("pdf", new_pdf_bytes)

            self.hide_progressbar()
            
            # Optymalizacja: odśwież tylko zmienione miniatury (nie zmienia się liczba stron)
            self.show_progressbar(maximum=len(pages_to_shift))
            for i, page_index in enumerate(pages_to_shift):
                self._update_status(f"Przesunięto zawartość na {len(pages_to_shift)} stronach o {result['x_mm']} mm (X) i {result['y_mm']} mm (Y). Odświeżanie miniatur...")
                self.update_single_thumbnail(page_index)
                self.update_progressbar(i + 1)
            self.hide_progressbar()
            
            self._update_status(f"Przesunięto zawartość na {len(pages_to_shift)} stronach o {result['x_mm']} mm (X) i {result['y_mm']} mm (Y).")
            self._record_action('shift_page_content',
                x_mm=result['x_mm'],
                y_mm=result['y_mm'],
                x_dir=result['x_dir'],
                y_dir=result['y_dir'])

        except Exception as e:
            self.hide_progressbar()
            self._update_status(f"BŁĄD (pypdf): Nie udało się przesunąć zawartości: {e}")
                
    def _reverse_pages(self):
        """Odwraca kolejność wszystkich stron w bieżącym dokumencie PDF."""
        if not self.pdf_document:
            custom_messagebox(self.master, "Informacja", "Najpierw otwórz plik PDF.", typ="info")
            return

        # Zapisz obecny stan do historii przed zmianą
        self._save_state_to_undo() 
        
        try:
            # Deleguj do PDFTools
            def progress_callback(current, total):
                if current == 0:
                    self.show_progressbar(maximum=total)
                self.update_progressbar(current)
                if current == total:
                    self.hide_progressbar()
            
            new_doc = self.pdf_tools.reverse_pages(
                self.pdf_document,
                progress_callback=self._update_status,
                progressbar_callback=progress_callback
            )
            
            self.hide_progressbar()
            
            # Zastąpienie starego dokumentu nowym
            page_count = len(self.pdf_document)
            self.pdf_document.close()
            self.pdf_document = new_doc
            
            # Resetowanie stanu (wyzerowanie zaznaczenia)
            self.active_page_index = 0
            self.selected_pages.clear()
            
            # Czyszczenie i odświeżenie widoku
            self.tk_images.clear()
            for widget in list(self.scrollable_frame.winfo_children()): 
                widget.destroy()
            self.thumb_frames.clear()

            self._reconfigure_grid()
            self.update_tool_button_states()
            self.update_focus_display()
            
            self._update_status(f"Pomyślnie odwrócono kolejność {page_count} stron. Odswieżanie miniatur...")
            
        except Exception as e:
            self.hide_progressbar()
            custom_messagebox(self.master, "Błąd", f"Wystąpił błąd podczas odwracania stron: {e}", typ="error")
            # W przypadku błędu użytkownik może użyć przycisku Cofnij aby przywrócić stan
    
    def _apply_selection_by_indices(self, indices_to_select, macro_source_page_count=None):
        """
        Zaznacza strony zgodnie z podanymi indeksami do source_page_count-1,
        a następnie wszystkie strony powyżej source_page_count do końca dokumentu.
        """
        if not self.pdf_document:
            return

        max_index = len(self.pdf_document) - 1

        indices = set()
        if indices_to_select:
            if macro_source_page_count is not None:
                # Zaznacz tylko te, które są <= source_page_count - 1
                indices.update(i for i in indices_to_select if 0 <= i < macro_source_page_count)
                # Dodaj wszystkie strony powyżej source_page_count-1
                indices.update(range(macro_source_page_count, max_index + 1))
            else:
                # Standardowe zachowanie dla braku makra
                indices.update(i for i in indices_to_select if 0 <= i <= max_index)
        else:
            # Jeśli nie podano indeksów, ale jest source_page_count, zaznacz od source_page_count do końca
            if macro_source_page_count is not None:
                indices.update(range(macro_source_page_count, max_index + 1))

        current_selection = self.selected_pages.copy()
        new_selection = set(indices)
        self.selected_pages = new_selection

        if current_selection != self.selected_pages:
            self.update_selection_display()
            self.update_tool_button_states()
            
    def _select_odd_pages(self):
        """Zaznacza strony nieparzyste (indeksy 0, 2, 4...)."""
        if not self.pdf_document: return
        
        # Nagraj akcję
        self._record_action('select_odd')
        
        # W Pythonie indeksy są od 0, więc strony nieparzyste mają indeksy parzyste (0, 2, 4...)
        indices = [i for i in range(len(self.pdf_document)) if i % 2 == 0]
        self._apply_selection_by_indices(indices)

    def _select_even_pages(self):
        """Zaznacza strony parzyste (indeksy 1, 3, 5...)."""
        if not self.pdf_document: return
        
        # Nagraj akcję
        self._record_action('select_even')

        # Strony parzyste mają indeksy nieparzyste (1, 3, 5...)
        indices = [i for i in range(len(self.pdf_document)) if i % 2 != 0]
        self._apply_selection_by_indices(indices)

    def _select_portrait_pages(self):
        """Zaznacza strony pionowe (wysokość > szerokość)."""
        if not self.pdf_document: return
        
        indices = []
        for i in range(len(self.pdf_document)):
            page = self.pdf_document.load_page(i)
            # Sprawdzenie, czy wysokość bounding boxu jest większa niż szerokość
            if page.rect.height > page.rect.width:
                indices.append(i)
        self._apply_selection_by_indices(indices)
        self._record_action('select_portrait')
        
    def _select_landscape_pages(self):
        """Zaznacza strony poziome (szerokość >= wysokość)."""
        if not self.pdf_document: return
        
        indices = []
        for i in range(len(self.pdf_document)):
            page = self.pdf_document.load_page(i)
            # Sprawdzenie, czy szerokość bounding boxu jest większa lub równa wysokości
            if page.rect.width >= page.rect.height:
                indices.append(i)
        self._apply_selection_by_indices(indices)
        self._record_action('select_landscape')

    def export_selected_pages_to_image(self):
        """Eksportuje wybrane strony do plików PNG o wysokiej rozdzielczości."""
        
        selected_indices = sorted(list(self.selected_pages))
        
        if not selected_indices:
            custom_messagebox(self.master, "Informacja", "Wybierz strony do eksportu.", typ="info")
            return

        # Wybierz folder do zapisu (bez dialogu trybu - domyślnie każda strona osobno)
        output_dir = filedialog.askdirectory(
            title="Wybierz folder do zapisu wyeksportowanych obrazów"
        )
        
        if not output_dir:
            return

        try:
            # Ustawienia eksportu - pobierz DPI z preferencji
            export_dpi = int(self.prefs_manager.get('export_image_dpi', '600'))
            
            # Pobierz nazwę bazową pliku źródłowego
            if hasattr(self, 'file_path') and self.file_path:
                base_filename = os.path.splitext(os.path.basename(self.file_path))[0]
            else:
                base_filename = "dokument"
            
            self.master.config(cursor="wait")
            
            # Deleguj do PDFTools
            def progress_callback(current, total):
                if current == 0:
                    self.show_progressbar(maximum=total)
                self.update_progressbar(current)
                if current == total:
                    self.hide_progressbar()
            
            exported_files = self.pdf_tools.export_pages_to_images(
                self.pdf_document, selected_indices, output_dir,
                base_filename, export_dpi, 'png',
                progress_callback=self._update_status,
                progressbar_callback=progress_callback
            )
            
            self.hide_progressbar()
            self.master.config(cursor="")
            
            self._update_status(f"Pomyślnie wyeksportowano {len(exported_files)} stron do folderu: {output_dir}")   
        except Exception as e:
            self.hide_progressbar()
            self.master.config(cursor="")
            custom_messagebox(self.master, "Błąd Eksportu", f"Wystąpił błąd podczas eksportowania stron:\n{e}", typ="error")
            
            
    
    
    def __init__(self, master):
        self.master = master
        master.title(PROGRAM_TITLE) 
        
        master.protocol("WM_DELETE_WINDOW", self.on_close_window) 

        # Inicjalizacja managera preferencji
        self.prefs_manager = PreferencesManager()
        
        # Inicjalizacja narzędzi PDF
        self.pdf_tools = PDFTools()
        
        # Inicjalizacja systemu makr
        self._init_macro_system()

        self.pdf_document = None
        self.selected_pages: Set[int] = set()
        # Multi-width thumbnail cache: {page_index: {width: ImageTk.PhotoImage}}
        self.tk_images: Dict[int, Dict[int, ImageTk.PhotoImage]] = {}
        self.icons: Dict[str, Union[ImageTk.PhotoImage, str]] = {}
        
        self.thumb_frames: Dict[int, 'ThumbnailFrame'] = {}
        self.active_page_index = 0 

        self.clipboard: Optional[bytes] = None 
        self.pages_in_clipboard_count: int = 0 
        
        # Thumbnail zoom settings - now based on width, not column count
        self.thumb_width = 205          # Current thumbnail width (controlled by zoom)
        self.min_thumb_width = 205      # Minimum thumbnail width
        self.max_thumb_width = 410      # Maximum thumbnail width
        self.zoom_step = 1           # Zoom step (10% change)
        self.THUMB_PADDING = 0         # Padding between thumbnails
        self.min_cols = 2               # Minimum columns (for safety)
        self.max_cols = 8              # Maximum columns (for safety)
        self.MIN_WINDOW_WIDTH = 950
        self.render_dpi_factor = self._get_render_dpi_factor()
        
        self.undo_stack: List[bytes] = []
        self.redo_stack: List[bytes] = []
        self.max_stack_size = 50
        
        # Debouncing for window resize events
        self._resize_timer = None
        self._resize_delay = 300  # milliseconds
        
        self._set_initial_geometry()
        self._load_icons_or_fallback(size=28) 
        self._create_menu() 
        self._setup_context_menu() 
        self._setup_key_bindings() 
        self._setup_drag_and_drop_file()
        
        GRAY_BG = BG_BUTTON_DEFAULT    
        GRAY_FG = FG_TEXT
        
        self.BG_OPEN = GRAY_BG     
        self.BG_SAVE = GRAY_BG     
        self.BG_UNDO = GRAY_BG     
        self.BG_DELETE = GRAY_BG   
        self.BG_INSERT = GRAY_BG   
        self.BG_ROTATE = GRAY_BG
        self.BG_SHIFT = GRAY_BG
        self.BG_CLIPBOARD = GRAY_BG 
        
        self.BG_IMPORT = GRAY_BG
        self.BG_EXPORT = GRAY_BG

        main_control_panel = tk.Frame(master, bg=BG_SECONDARY, padx=10, pady=5) 
        main_control_panel.pack(side=tk.TOP, fill=tk.X)
        
        tools_frame = tk.Frame(main_control_panel, bg=BG_SECONDARY)
        tools_frame.pack(side=tk.LEFT, fill=tk.Y)

        ICON_WIDTH = 3
        ICON_FONT = ("Arial", 14)
        PADX_SMALL = 5
        PADX_LARGE = 15
        
        def create_tool_button(parent, key, command, bg_color, fg_color="#333", state=tk.NORMAL, padx=(0, PADX_SMALL)):
            icon = self.icons[key]
            
            # NOWA LOGIKA: Zwiększenie czytelności przycisku
            btn_text = ""
                        
            common_config = {
                'command': command,
                'state': state,
                'bg': bg_color,
                'relief': tk.RAISED,
                'bd': 1,
            }

            if isinstance(icon, ImageTk.PhotoImage):
                 # Jeśli używamy ikon graficznych, używamy ich
                 btn = tk.Button(parent, image=icon, **common_config)
                 btn.image = icon 
            else:
                 # Jeśli używamy emoji/tekstu zastępczego, używamy dłuższej formy dla czytelności
                 if btn_text:
                     btn = tk.Button(parent, text=btn_text, font=("Arial", 9, "bold"), fg=fg_color, **common_config)
                 else:
                     btn = tk.Button(parent, text=icon, width=ICON_WIDTH, font=ICON_FONT, fg=fg_color, **common_config)
            
            btn.pack(side=tk.LEFT, padx=padx)
            return btn

        # 1. PRZYCISKI PLIK/ZAPISZ/IMPORT/EKSPORT/COFNIJ
        self.open_button = create_tool_button(tools_frame, 'open', self.open_pdf, self.BG_OPEN, GRAY_FG, padx=(5, PADX_SMALL)) 
        
        self.save_button_icon = create_tool_button(tools_frame, 'save', self.save_document, self.BG_SAVE, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_LARGE)) 
        
        # PRZYCISK IMPORTU PDF 
        self.import_button = create_tool_button(tools_frame, 'import', self.import_pdf_after_active_page, self.BG_IMPORT, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_SMALL)) 
        self.extract_button = create_tool_button(tools_frame, 'export', self.extract_selected_pages, self.BG_EXPORT, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_LARGE)) 
        
        # PRZYCISK IMPORTU OBRAZU 
        self.image_import_button = create_tool_button(tools_frame, 'image_import', self.import_image_to_new_page, self.BG_IMPORT, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_SMALL)) 
        self.export_image_button = create_tool_button(tools_frame, 'export_image', self.export_selected_pages_to_image, self.BG_EXPORT, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_LARGE))
        
        self.undo_button = create_tool_button(tools_frame, 'undo', self.undo, self.BG_UNDO, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_SMALL))
        self.redo_button = create_tool_button(tools_frame, 'redo', self.redo, self.BG_UNDO, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_LARGE))
        
        # 2. PRZYCISKI EDYCJI STRON
        self.delete_button = create_tool_button(tools_frame, 'delete', self.delete_selected_pages, self.BG_DELETE, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_SMALL)) 
        
        # 3. PRZYCISKI WYCINAJ/KOPIUJ/WKLEJ
        self.cut_button = create_tool_button(tools_frame, 'cut', self.cut_selected_pages, self.BG_CLIPBOARD, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_SMALL)) 
        self.copy_button = create_tool_button(tools_frame, 'copy', self.copy_selected_pages, self.BG_CLIPBOARD, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_SMALL)) 
        
        self.paste_before_button = create_tool_button(tools_frame, 'paste_b', self.paste_pages_before, self.BG_CLIPBOARD, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_SMALL)) 
        self.paste_after_button = create_tool_button(tools_frame, 'paste_a', self.paste_pages_after, self.BG_CLIPBOARD, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_LARGE)) 
        
        self.insert_before_button = create_tool_button(tools_frame, 'insert_b', self.insert_blank_page_before, self.BG_INSERT, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_SMALL)) 
        self.insert_after_button = create_tool_button(tools_frame, 'insert_a', self.insert_blank_page_after, self.BG_INSERT, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_LARGE)) 
        
        self.rotate_left_button = create_tool_button(tools_frame, 'rotate_l', lambda: self.rotate_selected_page(-90), self.BG_ROTATE, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_SMALL)) 
        self.rotate_right_button = create_tool_button(tools_frame, 'rotate_r', lambda: self.rotate_selected_page(90), self.BG_ROTATE, GRAY_FG, state=tk.DISABLED, padx=(0, 20)) 

        self.shift_content_btn = create_tool_button(tools_frame, 'shift', self.shift_page_content, self.BG_SHIFT, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_LARGE))
        self.remove_nums_btn = create_tool_button(tools_frame, 'page_num_del', self.remove_page_numbers, self.BG_DELETE, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_SMALL))
        self.add_nums_btn = create_tool_button(tools_frame, 'add_nums', self.insert_page_numbers, self.BG_INSERT, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_LARGE))
        
        
        Tooltip(self.open_button, "Otwórz plik PDF.")
        Tooltip(self.save_button_icon, "Zapisz całość do nowego pliku PDF.")
        
        Tooltip(self.import_button, "Importuj strony z pliku PDF.\n" "Strony zostaną wstawione po bieżącej, a przy braku zazanczenia - na końcu pliku.")
        Tooltip(self.extract_button, "Eksportuj strony do pliku PDF.\n" "Wymaga zaznaczenia przynajniej jednej strony.")
        
        Tooltip(self.image_import_button, "Importuj strony z pliku obrazu.\n" "Strony zostaną wstawione po bieżącej, a przy braku zazanczenia - na końcu pliku.")
        Tooltip(self.export_image_button, "Eksportuj strony do plików PNG.\n" "Wymaga zaznaczenia przynajniej jednej strony.")
        
        Tooltip(self.undo_button, "Cofnij ostatnią zmianę.\n" "Obsługuje do 50 kroków wstecz.")
        Tooltip(self.redo_button, "Ponów cofniętą zmianę.\n" "Obsługuje do 50 kroków do przodu.")
        
        Tooltip(self.delete_button, "Usuń zaznaczone strony.\n" "Wymaga zaznaczenia przynajniej jednej strony.")
        Tooltip(self.cut_button, "Wytnij zaznaczone strony.\n" "Wymaga zaznaczenia przynajniej jednej strony.")
        Tooltip(self.copy_button, "Skopiuj zaznaczone strony.\n" "Wymaga zaznaczenia przynajniej jednej strony.")
        
        Tooltip(self.paste_before_button, "Wklej stronę przed bieżącą.\n" "Wymaga wcześniejszego skopiowania/wycięcia prznajmniej jednej strony.")
        Tooltip(self.paste_after_button, "Wklej stronę po bieżącej.\n" "Wymaga wcześniejszego skopiowania/wycięcia prznajmniej jednej strony.")
        
        Tooltip(self.insert_before_button, "Wstaw pustą stronę przed bieżącą.\n" "Wymaga zaznaczenia jednej strony.")
        Tooltip(self.insert_after_button, "Wstaw pustą stronę po bieżącej.\n" "Wymaga zaznaczenia jednej strony.")

        Tooltip(self.rotate_left_button, "Obróć w lewo - prawidłowy obrót dla druku stron poziomych.\n" "Wymaga zaznaczenia przynajniej jednej strony.")
        Tooltip(self.rotate_right_button, "Obróć w prawo.\n" "Wymaga zaznaczenia przynajniej jednej strony.")
        Tooltip(self.shift_content_btn, "Zmiana marginesów (przesuwanie obrazu).\n" "Wymaga zaznaczenia przynajniej jednej strony.")
        Tooltip(self.remove_nums_btn, "Usuwanie numeracji. \n" "Wymaga zaznaczenia przynajniej jednej strony.")
        Tooltip(self.add_nums_btn, "Wstawianie numeracji. \n" "Wymaga zaznaczenia przynajniej jednej strony.")

        # ZOOM 
        zoom_frame = tk.Frame(main_control_panel, bg=BG_SECONDARY)
        zoom_frame.pack(side=tk.RIGHT, padx=10)
        
        ZOOM_BG = GRAY_BG 
        ZOOM_FONT = ("Arial", 14, "bold") 
        ZOOM_WIDTH = 2
        
        self.zoom_in_button = create_tool_button(zoom_frame, 'zoom_in', self.zoom_in, ZOOM_BG, fg_color=GRAY_FG, padx=(2, 2), state=tk.DISABLED) 
        if not isinstance(self.icons['zoom_in'], ImageTk.PhotoImage):
             self.zoom_in_button.config(width=ZOOM_WIDTH, height=1, font=ZOOM_FONT)

        self.zoom_out_button = create_tool_button(zoom_frame, 'zoom_out', self.zoom_out, ZOOM_BG, fg_color=GRAY_FG, padx=(2, 5), state=tk.DISABLED) 
        if not isinstance(self.icons['zoom_out'], ImageTk.PhotoImage):
             self.zoom_out_button.config(width=ZOOM_WIDTH, height=1, font=ZOOM_FONT)
        
        
        # Pasek statusu z paskiem postępu
        status_frame = tk.Frame(master, bd=1, relief=tk.SUNKEN, bg="#f0f0f0")
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_bar = tk.Label(status_frame, text="Gotowy. Otwórz plik PDF.", anchor=tk.W, bg="#f0f0f0", fg="black")
        self.status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Pasek postępu (początkowo ukryty)
        self.progress_bar = ttk.Progressbar(status_frame, orient="horizontal", length=200, mode="determinate")
        self.progress_bar.pack(side=tk.RIGHT, padx=(5, 5))
        self.progress_bar.pack_forget()  # Ukryj na starcie


        self.canvas = tk.Canvas(master, bg="#F5F5F5") 
        self.scrollbar = tk.Scrollbar(master, orient="vertical", command=self.canvas.yview)
        
        self.scrollable_frame = tk.Frame(self.canvas, bg="#F5F5F5") 
        
        self.canvas_window_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        self.canvas.bind("<Configure>", self._reconfigure_grid) 
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True) 

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel) 
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)
        
        self.update_tool_button_states() 
        self._setup_drag_and_drop_file()

    # --- Metody obsługi GUI i zdarzeń (Bez zmian) ---
    def _get_render_dpi_factor(self):
        """Zwraca współczynnik DPI dla miniatur na podstawie ustawienia jakości"""
        quality = self.prefs_manager.get('thumbnail_quality', 'Średnia')
        quality_map = {
            'Niska': 0.4,
            'Średnia': 0.8,
            'Wysoka': 1.2
        }
        return quality_map.get(quality, 0.8)
    
    def on_close_window(self):
        # Sprawdź czy są niezapisane zmiany (niepusty stos undo)
        if self.pdf_document is not None and len(self.undo_stack) > 0:
            response = custom_messagebox(
                self.master, "Niezapisane zmiany",
                "Czy chcesz zapisać zmiany w dokumencie przed zamknięciem programu?",
                typ="yesnocancel"
            )
            if response is None:
                return
            elif response is True: 
                self.save_document() 
                if len(self.undo_stack) > 0:
                    return 
                self.master.quit() 
            else: 
                self.master.quit()
        else:
            self.master.quit()

    def _set_initial_geometry(self):
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        initial_width = self.MIN_WINDOW_WIDTH
        initial_height = int(screen_height * 0.50)  
        self.master.minsize(self.MIN_WINDOW_WIDTH, initial_height)
        x_cordinate = int((screen_width / 2) - (initial_width / 2))
        y_cordinate = int((screen_height / 2) - (initial_height / 2))
        self.master.geometry(f"{initial_width}x{initial_height}+{x_cordinate}+{y_cordinate}")

    def _load_icons_or_fallback(self, size=28):
        icon_map = {
            'open': ('📂', "open.png"),
            'save': ('💾', "save.png"),
            'undo': ('↩️', "undo.png"),
            'redo': ('↪️', "redo.png"),
            'delete': ('🗑️', "delete.png"),
            'cut': ('✂️', "cut.png"),  
            'copy': ('📋', "copy.png"),  
            'paste_b': ('⬆️📄', "paste_before.png"),  
            'paste_a': ('⬇️📄', "paste_after.png"),  
            'insert_b': ('⬆️➕', "insert_before.png"),  
            'insert_a': ('⬇️➕', "insert_after.png"),  
            'rotate_l': ('↺', "rotate_left.png"),
            'rotate_r': ('↻', "rotate_right.png"),
            'zoom_in': ('➖', "zoom_in.png"),  
            'zoom_out': ('➕', "zoom_out.png"),
            'export': ('📤', "export.png"), 
            'export_image': ('🖼️', "export_image.png"),
            'import': ('📥', "import.png"), # Import PDF
            'image_import': ('🖼️', "import_image.png"), # Import Obrazu
            'shift': ('↔️', "shift.png"), 
            'page_num_del': ('#️⃣❌', "del_nums.png"), 
            'add_nums': ('#️⃣➕', "add_nums.png"), 

        }
        for key, (emoji, filename) in icon_map.items():
            try:
                path = os.path.join(ICON_FOLDER, filename)
                img = Image.open(path).convert("RGBA")
                self.icons[key] = ImageTk.PhotoImage(img.resize((size, size), Image.LANCZOS))
            except Exception:
                self.icons[key] = emoji
    def refresh_macros_menu(self):
        """Odświeża menu główne Makra – dynamicznie dodaje wszystkie makra użytkownika."""
        self.macros_menu.delete(0, "end")  # Wyczyść stare wpisy
        self.macros_menu.add_command(label="Lista makr użytkownika...", command=self.show_macros_list,accelerator="F12")
        macros = self.macro_manager.get_all_macros()
        if macros:  # separator tylko jeśli jest przynajmniej jedno makro
            self.macros_menu.add_separator()
            for macro_name in macros:
                self.macros_menu.add_command(
                    label=f"Uruchom: {macro_name}",
                    command=lambda name=macro_name: self.run_macro(name)
                )

    def _create_menu(self):
        menu_bar = tk.Menu(self.master)
        self.master.config(menu=menu_bar)

        self.file_menu = tk.Menu(menu_bar, tearoff=0)  
        menu_bar.add_cascade(label="Plik", menu=self.file_menu)
        self.file_menu.add_command(label="Otwórz PDF...", command=self.open_pdf, accelerator="Ctrl+O")
        self.file_menu.add_command(label="Otwórz obraz jako PDF...", command=self.open_image_as_new_pdf, accelerator="Ctrl+Shift+O")
        self.file_menu.add_command(label="Zapisz jako...", command=self.save_document, state=tk.DISABLED, accelerator="Ctrl+S")
        self.file_menu.add_command(label="Zapisz jako plik z hasłem...", command=self.set_pdf_password, state=tk.DISABLED)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Importuj strony z PDF...", command=self.import_pdf_after_active_page, state=tk.DISABLED, accelerator="Ctrl+I") 
        self.file_menu.add_command(label="Eksportuj strony do PDF...", command=self.extract_selected_pages, state=tk.DISABLED,accelerator="Ctrl+E") 
        self.file_menu.add_separator() 
        self.file_menu.add_command(label="Importuj obraz na nową stronę...", command=self.import_image_to_new_page, state=tk.DISABLED, accelerator="Ctrl+Shift+I") 
        self.file_menu.add_command(label="Eksportuj strony jako obrazy PNG...", command=self.export_selected_pages_to_image, state=tk.DISABLED, accelerator="Ctrl+Shift+E")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Scalanie plików PDF...", command=self.merge_pdf_files)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Preferencje...", command=self.show_preferences_dialog)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Zamknij plik", command=self.close_pdf, accelerator="Ctrl+Q")
        self.file_menu.add_command(label="Zamknij program", command=self.on_close_window)

        select_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Zaznacz", menu=select_menu)
        select_menu.add_command(label="Wszystkie strony", command=self._select_all, accelerator="Ctrl+A, F4")
        select_menu.add_separator()
        select_menu.add_command(label="Strony nieparzyste", command=self._select_odd_pages, state=tk.DISABLED, accelerator="F1")
        select_menu.add_command(label="Strony parzyste", command=self._select_even_pages, state=tk.DISABLED, accelerator="F2")
        select_menu.add_separator()
        select_menu.add_command(label="Strony pionowe", command=self._select_portrait_pages, state=tk.DISABLED, accelerator="Ctrl+F1")
        select_menu.add_command(label="Strony poziome", command=self._select_landscape_pages, state=tk.DISABLED, accelerator="Ctrl+F2")
        self.select_menu = select_menu
        
        self.edit_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Edycja", menu=self.edit_menu)
        self._populate_edit_menu(self.edit_menu)
        
        self.modifications_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Modyfikacje", menu=self.modifications_menu)
        self._populate_modifications_menu(self.modifications_menu) # Wypełniamy nową metodą
        
        # === MENU MAKRA ===
        self.macros_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Makra", menu=self.macros_menu)
        self.refresh_macros_menu()  # dodaj to tu!
        
        self.external_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Programy", menu=self.external_menu)
        self.external_menu.add_command(label="Analiza PDF", command=self.show_pdf_analysis, state=tk.DISABLED, accelerator="F11")
        self.external_menu.add_command(label="Porównianie PDF", command=self.run_compare_program)
        
        
        self.help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Pomoc", menu=self.help_menu)
        self.help_menu.add_command(label="Skróty klawiszowe...", command=self.show_shortcuts_dialog)
        self.help_menu.add_command(label="O programie", command=self.show_about_dialog)
        
    def show_preferences_dialog(self):
        """Wyświetla okno dialogowe preferencji"""
        PreferencesDialog(self.master, self.prefs_manager)
    
    def show_about_dialog(self):
        PROGRAM_LOGO_PATH = resource_path(os.path.join('icons', 'logo.png'))
        # STAŁE WYMIARY OKNA
        DIALOG_WIDTH = 280
        DIALOG_HEIGHT = 260

        # 1. Inicjalizacja i Ustawienia Okna
        dialog = tk.Toplevel(self.master)
        dialog.title("O programie")
        dialog.geometry(f"{DIALOG_WIDTH}x{DIALOG_HEIGHT}") # Ustawienie stałego rozmiaru
        dialog.resizable(False, False) # Zablokowanie zmiany rozmiaru
        
        # Ustawienia modalne
        dialog.transient(self.master)
        dialog.grab_set()
        dialog.focus_set()
        
        # 2. Centralizacja Okna (Matematyczna, używając stałych)
        dialog.update_idletasks() # Wymuś odświeżenie dla bezpieczeństwa
        
        self.master.update_idletasks()
        dialog.update_idletasks()
        master_x = self.master.winfo_rootx()
        master_y = self.master.winfo_rooty()
        master_w = self.master.winfo_width()
        master_h = self.master.winfo_height()
        dialog_w = DIALOG_WIDTH
        dialog_h = DIALOG_HEIGHT
        position_right = master_x + (master_w - dialog_w) // 2
        position_top = master_y + (master_h - dialog_h) // 2
        dialog.geometry(f"+{position_right}+{position_top}")
                
        
        # --- Ramka Centrująca Treść ---
        main_frame = ttk.Frame(dialog)
        # Pack bez expand/fill sprawia, że treść jest mała i wyśrodkowana w stałym oknie
        main_frame.pack(padx=10, pady=10) 

        # 3. Dodanie Grafiki
        logo_path = PROGRAM_LOGO_PATH 
        self.tk_image = None 

        if logo_path:
            try:
                pil_image = Image.open(logo_path)
                pil_image = pil_image.resize((60, 60), Image.Resampling.LANCZOS)
                
                self.tk_image = ImageTk.PhotoImage(pil_image)
                
                logo_label = ttk.Label(main_frame, image=self.tk_image)
                logo_label.pack(pady=(0, 5))
            except Exception as e:
                print(f"Błąd ładowania logo: {e}") 

        # 4. Dodanie Treści
        
        # Tytuł
        title_label = ttk.Label(main_frame, text=PROGRAM_TITLE, font=("Helvetica", 12, "bold"))
        title_label.pack(pady=(2, 1))
        
        # Wersja
        version_label = ttk.Label(main_frame, text=f"Wersja: {PROGRAM_VERSION} (Data: {PROGRAM_DATE})", font=("Helvetica", 8))
        version_label.pack(pady=1)

        separator_frame = tk.Frame(main_frame, height=1, bg='lightgray')
        separator_frame.pack(fill='x', padx=15, pady=15)
        # Prawa Autorskie (Zmodyfikowano: czcionka 10, bez pogrubienia, dodano zawijanie)
        copy_label = ttk.Label(
        main_frame, 
        text=COPYRIGHT_INFO, 
        font=("Helvetica", 8),              # Czcionka 10, bez pogrubienia
        foreground="black",
        wraplength=250                       # Zawijanie tekstu po osiągnięciu 300 pikseli szerokości
        )
        copy_label.pack(pady=(5, 0))
        
        # 5. Blokowanie
        dialog.bind('<Escape>', lambda e: dialog.destroy())
        dialog.focus_force()
        dialog.wait_window()
    
    def _setup_context_menu(self):
        self.context_menu = tk.Menu(self.master, tearoff=0)
        self._populate_edit_menu(self.context_menu)
    
    def _populate_edit_menu(self, menu_obj):
        menu_obj.add_command(label="Cofnij", command=self.undo, accelerator="Ctrl+Z")
        menu_obj.add_command(label="Ponów", command=self.redo, accelerator="Ctrl+Y")
        menu_obj.add_separator()
        menu_obj.add_command(label="Usuń zaznaczone", command=self.delete_selected_pages, accelerator="Delete/Backspace")
        menu_obj.add_command(label="Wytnij zaznaczone", command=self.cut_selected_pages, accelerator="Ctrl+X")
        menu_obj.add_command(label="Kopiuj zaznaczone", command=self.copy_selected_pages, accelerator="Ctrl+C")
        menu_obj.add_command(label="Wklej przed", command=self.paste_pages_before, accelerator="Ctrl+Shift+V")
        menu_obj.add_command(label="Wklej po", command=self.paste_pages_after, accelerator="Ctrl+V")
        menu_obj.add_separator()
        menu_obj.add_command(label="Duplikuj stronę", command=self.duplicate_selected_page, accelerator="Ctrl+D")
        menu_obj.add_command(label="Zamień strony miejscami", command=self.swap_pages, accelerator="Ctrl+Tab")
        menu_obj.add_separator()
        menu_obj.add_command(label="Wstaw nową stronę przed", command=self.insert_blank_page_before, accelerator="Ctrl+Shift+N")
        menu_obj.add_command(label="Wstaw nową stronę po", command=self.insert_blank_page_after, accelerator="Ctrl+N")
        #menu_obj.add_separator()
        #menu_obj.add_command(label="Obróć w lewo (-90°)", command=lambda: self.rotate_selected_page(-90))
        #menu_obj.add_command(label="Obróć w prawo (+90°)", command=lambda: self.rotate_selected_page(90))

    def _populate_modifications_menu(self, menu_obj):
        
        # OBRACANIE
        menu_obj.add_command(label="Obróć w lewo (-90°)", command=lambda: self.rotate_selected_page(-90), state=tk.DISABLED, accelerator="Ctrl+Lewo")
        menu_obj.add_command(label="Obróć w prawo (+90°)", command=lambda: self.rotate_selected_page(90), state=tk.DISABLED, accelerator="Ctrl+Prawo")
        menu_obj.add_separator()
    
        # === NOWA OPCJA: USUWANIE NUMERÓW STRON ===
        menu_obj.add_command(label="Przesuń zawartość stron...",command=self.shift_page_content, state=tk.DISABLED, accelerator="F5")
        menu_obj.add_command(label="Usuń numery stron...", command=self.remove_page_numbers, state=tk.DISABLED, accelerator="F6")
        menu_obj.add_command(label="Wstaw numery stron...", command=self.insert_page_numbers, state=tk.DISABLED, accelerator="F7")
     
    # ... (resztę modyfikacji) ...
    
        # ODRACANIE KOLEJNOŚCI

        menu_obj.add_command(label="Kadruj / zmień rozmiar...", command=self.apply_page_crop_resize_dialog, state=tk.DISABLED, accelerator="F8")
        menu_obj.add_separator()
        menu_obj.add_command(label="Scal strony na arkuszu...", command=self.merge_pages_to_grid, state=tk.DISABLED)
        menu_obj.add_separator()
        menu_obj.add_command(label="Odwróć kolejność wszystkich stron", command=self._reverse_pages, state=tk.DISABLED)
        
        # === USUWANIE PUSTYCH STRON ===
        menu_obj.add_command(label="Usuń puste strony", command=self.remove_empty_pages, state=tk.DISABLED)
    
    def _check_action_allowed(self, action_name):
        """Check if an action is allowed based on current button/menu state"""
        doc_loaded = self.pdf_document is not None
        has_selection = len(self.selected_pages) > 0
        has_single_selection = len(self.selected_pages) == 1
        has_undo = len(self.undo_stack) > 0
        has_redo = len(self.redo_stack) > 0
        has_clipboard_content = self.clipboard is not None
        
        # Map action names to their conditions
        conditions = {
            'delete': doc_loaded and has_selection,
            'cut': doc_loaded and has_selection,
            'copy': doc_loaded and has_selection,
            'paste': has_clipboard_content and doc_loaded and has_selection,
            'undo': has_undo,
            'redo': has_redo,
            'rotate': doc_loaded and has_selection,
            'insert': doc_loaded and has_selection,
            'duplicate': doc_loaded and has_selection,
            'swap': doc_loaded and len(self.selected_pages) == 2,
            'import': doc_loaded,
            'export': doc_loaded and has_selection,
            'select': doc_loaded,
            'shift': doc_loaded and has_selection,
            'remove_numbers': doc_loaded and has_selection,
            'add_numbers': doc_loaded and has_selection,
            'crop': doc_loaded and has_selection,
            'zoom_in': doc_loaded and self.thumb_width < self.max_thumb_width,
            'zoom_out': doc_loaded and self.thumb_width > self.min_thumb_width,
        }
        
        return conditions.get(action_name, True)
    
    def _setup_key_bindings(self):
        # With Caps Lock support - bind both lowercase and uppercase variants
        self.master.bind('<Control-x>', lambda e: self._check_action_allowed('cut') and self.cut_selected_pages())
        self.master.bind('<Control-X>', lambda e: self._check_action_allowed('cut') and self.cut_selected_pages())
        self.master.bind('<Control-Shift-O>', lambda e: self.open_image_as_new_pdf())
        self.master.bind('<Control-c>', lambda e: self._check_action_allowed('copy') and self.copy_selected_pages())
        self.master.bind('<Control-C>', lambda e: self._check_action_allowed('copy') and self.copy_selected_pages())
        self.master.bind('<Control-d>', lambda e: self._check_action_allowed('duplicate') and self.duplicate_selected_page())
        self.master.bind('<Control-D>', lambda e: self._check_action_allowed('duplicate') and self.duplicate_selected_page())
        self.master.bind('<Control-Tab>', lambda e: self._check_action_allowed('swap') and self.swap_pages())
        self.master.bind('<Control-z>', lambda e: self._check_action_allowed('undo') and self.undo())
        self.master.bind('<Control-Z>', lambda e: self._check_action_allowed('undo') and self.undo())
        self.master.bind('<Control-y>', lambda e: self._check_action_allowed('redo') and self.redo())
        self.master.bind('<Control-Y>', lambda e: self._check_action_allowed('redo') and self.redo())
        self.master.bind('<Delete>', lambda e: self._check_action_allowed('delete') and self.delete_selected_pages())
        self.master.bind('<BackSpace>', lambda e: self._check_action_allowed('delete') and self.delete_selected_pages())
        self.master.bind('<Control-a>', lambda e: self._check_action_allowed('select') and self._select_all())
        self.master.bind('<Control-A>', lambda e: self._check_action_allowed('select') and self._select_all())
        self.master.bind('<F4>', lambda e: self._check_action_allowed('select') and self._select_all())
        self.master.bind('<F1>', lambda e: self._check_action_allowed('select') and self._select_odd_pages())
        self.master.bind('<F2>', lambda e: self._check_action_allowed('select') and self._select_even_pages())
        self.master.bind('<Control-Left>', lambda e: self._check_action_allowed('rotate') and self.rotate_selected_page(-90))
        self.master.bind('<Control-Right>', lambda e: self._check_action_allowed('rotate') and self.rotate_selected_page(+90))
        self.master.bind('<F5>', lambda e: self._check_action_allowed('shift') and self.shift_page_content())
        self.master.bind('<F6>', lambda e: self._check_action_allowed('remove_numbers') and self.remove_page_numbers())
        self.master.bind('<F7>', lambda e: self._check_action_allowed('add_numbers') and self.insert_page_numbers())
        self.master.bind('<F8>', lambda e: self._check_action_allowed('crop') and self.apply_page_crop_resize_dialog())
        self.master.bind('<plus>', lambda e: self._check_action_allowed('zoom_in') and self.zoom_in())
        self.master.bind('<minus>', lambda e: self._check_action_allowed('zoom_out') and self.zoom_out())
        self.master.bind('<KP_Add>', lambda e: self._check_action_allowed('zoom_in') and self.zoom_in())
        self.master.bind('<KP_Subtract>', lambda e: self._check_action_allowed('zoom_out') and self.zoom_out())
        self.master.bind('<Control-q>', lambda e: self.close_pdf())
        self.master.bind('<Control-Q>', lambda e: self.close_pdf())
                     
        self.master.bind('<Control-F1>', lambda e: self._check_action_allowed('select') and self._select_portrait_pages())
        self.master.bind('<Control-F2>', lambda e: self._check_action_allowed('select') and self._select_landscape_pages())
        self.master.bind('<Control-v>', lambda e: self._check_action_allowed('paste') and self.paste_pages_after())
        self.master.bind('<Control-V>', lambda e: self._check_action_allowed('paste') and self.paste_pages_after())
        self.master.bind('<Control-Shift-V>', lambda e: self._check_action_allowed('paste') and self.paste_pages_before())
        self.master.bind('<Control-n>', lambda e: self._check_action_allowed('insert') and self.insert_blank_page_after())
        self.master.bind('<Control-N>', lambda e: self._check_action_allowed('insert') and self.insert_blank_page_after())
        self.master.bind('<Control-Shift-N>', lambda e: self._check_action_allowed('insert') and self.insert_blank_page_before())
        # === SKRÓTY DLA EKSPORTU ===
        # Ctrl+E dla Eksportu stron do nowego PDF
        self.master.bind('<Control-e>', lambda e: self._check_action_allowed('export') and self.extract_selected_pages())
        self.master.bind('<Control-E>', lambda e: self._check_action_allowed('export') and self.extract_selected_pages())
        # Ctrl+Shift+E dla Eksportu stron jako obrazów PNG
        self.master.bind('<Control-Shift-E>', lambda e: self._check_action_allowed('export') and self.export_selected_pages_to_image())
        # ===========================
        self._setup_focus_logic()
        self.master.bind('<Control-o>', lambda e: self.open_pdf())
        self.master.bind('<Control-O>', lambda e: self.open_pdf())
        self.master.bind('<Control-s>', lambda e: self.save_document())
        self.master.bind('<Control-S>', lambda e: self.save_document())
        # Zmienione skróty
        self.master.bind('<Control-Shift-I>', lambda e: self._check_action_allowed('import') and self.import_image_to_new_page()) # Ctrl+K dla obrazu
        self.master.bind('<Control-i>', lambda e: self._check_action_allowed('import') and self.import_pdf_after_active_page()) # Ctrl+I dla PDF
        self.master.bind('<Control-I>', lambda e: self._check_action_allowed('import') and self.import_pdf_after_active_page()) # Ctrl+I dla PDF
        
        # F11 - Open PDF Analysis (tylko gdy PDF załadowany)
        self.master.bind('<F11>', lambda e: self.pdf_document is not None and self.show_pdf_analysis())
        
        # F12 - Open Macros List (tylko gdy PDF załadowany)
        self.master.bind('<F12>', lambda e: self.pdf_document is not None and self.show_macros_list())
        
    def _setup_focus_logic(self):
        self.master.bind('<Escape>', lambda e: self._clear_all_selection())
        self.master.bind('<space>', lambda e: self._toggle_selection_space())
        self.master.bind('<Left>', lambda e: self._move_focus_and_scroll(-1))
        self.master.bind('<Right>', lambda e: self._move_focus_and_scroll(1))
        self.master.bind('<Up>', lambda e: self._move_focus_and_scroll(-self._get_current_num_cols()))
        self.master.bind('<Down>', lambda e: self._move_focus_and_scroll(self._get_current_num_cols()))
        self.master.bind('<Home>', lambda e: self._jump_to_first_page())
        self.master.bind('<End>', lambda e: self._jump_to_last_page())
        self.master.bind('<Prior>', lambda e: self._page_up())  # PageUp
        self.master.bind('<Next>', lambda e: self._page_down())  # PageDown

    def _select_all(self):
        if self.pdf_document:
            all_pages = set(range(len(self.pdf_document)))
            # Zawsze zaznaczaj wszystkie strony, bez przełączania!
            self._record_action('select_all')
            self.selected_pages = all_pages
            self._update_status(f"Zaznaczono wszystkie strony ({len(self.pdf_document)}).")
            if self.pdf_document.page_count > 0:
                self.active_page_index = 0
            self.update_selection_display()
            self.update_focus_display()
                
    def _select_range(self, start_index, end_index):
        if not self.pdf_document:
            return
        if start_index > end_index:
            start_index, end_index = end_index, start_index
        self.selected_pages = set(range(start_index, end_index + 1))
        self.update_selection_display()
        self.active_page_index = end_index
        
    def _clear_all_selection(self):
        if self.pdf_document:
            self.active_page_index = 0
        if self.selected_pages:
            self.selected_pages.clear()
            self.update_selection_display()
            self.update_focus_display()
            self._update_status("Anulowano zaznaczenie wszystkich stron (ESC).")
            
    def _toggle_selection_space(self):
        if self.pdf_document and self.pdf_document.page_count > 0:
            if self.active_page_index in self.selected_pages:
                self.selected_pages.remove(self.active_page_index)
            else:
                self.selected_pages.add(self.active_page_index)
            self.update_selection_display()

    def _get_page_frame(self, index) -> Optional['ThumbnailFrame']:
        return self.thumb_frames.get(index)

    def _move_focus_and_scroll(self, delta: int):
        if not self.pdf_document: return
        new_index = self.active_page_index + delta
        max_index = len(self.pdf_document) - 1
        if 0 <= new_index <= max_index:
            self.active_page_index = new_index
            self.update_focus_display(hide_mouse_focus=False)  
            frame = self._get_page_frame(self.active_page_index)
            if frame:
                self.canvas.update_idletasks()
                y1 = frame.winfo_y()
                y2 = frame.winfo_y() + frame.winfo_height()
                bbox = self.canvas.bbox("all")
                total_height = bbox[3] if bbox is not None else 1
                norm_top = y1 / total_height
                norm_bottom = y2 / total_height
                current_top, current_bottom = self.canvas.yview()
                if norm_top < current_top:
                    self.canvas.yview_moveto(norm_top)
                elif norm_bottom > current_bottom:
                    scroll_pos = norm_bottom - (current_bottom - current_top)
                    self.canvas.yview_moveto(scroll_pos)
    
    def _jump_to_first_page(self):
        """Przejdź do pierwszej strony (Home)"""
        if not self.pdf_document or len(self.pdf_document) == 0:
            return
        self.active_page_index = 0
        self.update_focus_display(hide_mouse_focus=False)
        frame = self._get_page_frame(0)
        if frame:
            self.canvas.yview_moveto(0)
    
    def _jump_to_last_page(self):
        """Przejdź do ostatniej strony (End)"""
        if not self.pdf_document or len(self.pdf_document) == 0:
            return
        self.active_page_index = len(self.pdf_document) - 1
        self.update_focus_display(hide_mouse_focus=False)
        frame = self._get_page_frame(self.active_page_index)
        if frame:
            self.canvas.yview_moveto(1.0)
    
    def _page_up(self):
        """Przewiń w górę o jedną 'stronę' miniatur (PageUp)"""
        if not self.pdf_document:
            return
        # Oblicz ile wierszy mieści się w oknie
        canvas_height = self.canvas.winfo_height()
        # Oszacuj wysokość wiersza (średnia wysokość miniatury + padding)
        if self.thumb_frames:
            first_frame = self._get_page_frame(0)
            if first_frame:
                row_height = first_frame.winfo_height() + self.THUMB_PADDING
                rows_per_page = max(1, canvas_height // row_height)
                # Przesuń fokus o liczbę miniatur odpowiadającą liczbie wierszy * liczbie kolumn
                delta = -(rows_per_page * self._get_current_num_cols())
                self._move_focus_and_scroll(delta)
                return
        # Fallback - przesuń o 10 stron
        self._move_focus_and_scroll(-10)
    
    def _page_down(self):
        """Przewiń w dół o jedną 'stronę' miniatur (PageDown)"""
        if not self.pdf_document:
            return
        # Oblicz ile wierszy mieści się w oknie
        canvas_height = self.canvas.winfo_height()
        # Oszacuj wysokość wiersza (średnia wysokość miniatury + padding)
        if self.thumb_frames:
            first_frame = self._get_page_frame(0)
            if first_frame:
                row_height = first_frame.winfo_height() + self.THUMB_PADDING
                rows_per_page = max(1, canvas_height // row_height)
                # Przesuń fokus o liczbę miniatur odpowiadającą liczbie wierszy * liczbie kolumn
                delta = rows_per_page * self._get_current_num_cols()
                self._move_focus_and_scroll(delta)
                return
        # Fallback - przesuń o 10 stron
        self._move_focus_and_scroll(10)
                        
    def _handle_lpm_click(self, page_index, event):
        # Validate page_index before using it
        if not self.pdf_document or page_index < 0 or page_index >= len(self.pdf_document):
            return

        is_shift_pressed = (event.state & 0x1) != 0 
        if is_shift_pressed and self.selected_pages:
            last_active = self.active_page_index
            self._select_range(last_active, page_index)
        else:
            self._toggle_selection_lpm(page_index)
        self.active_page_index = page_index
        self.update_focus_display(hide_mouse_focus=True)

        # --- Dodaj to poniżej! ---
        if self.macro_manager.is_recording():
            indices = sorted(self.selected_pages)
            page_count = len(self.pdf_document) if self.pdf_document else 0
            self._record_action('select_custom', indices=indices, source_page_count=page_count)
        
    def _toggle_selection_lpm(self, page_index):
        # Validate page_index before using it
        if not self.pdf_document or page_index < 0 or page_index >= len(self.pdf_document):
            return
            
        if page_index in self.selected_pages:
            self.selected_pages.remove(page_index)
        else:
            self.selected_pages.add(page_index)
        self.update_selection_display()

    def update_tool_button_states(self):
        doc_loaded = self.pdf_document is not None
        has_selection = len(self.selected_pages) > 0
        has_single_selection = len(self.selected_pages) == 1
        has_undo = len(self.undo_stack) > 0
        has_redo = len(self.redo_stack) > 0
        has_clipboard_content = self.clipboard is not None
        
        delete_state = tk.NORMAL if doc_loaded and has_selection else tk.DISABLED
        insert_state = tk.NORMAL if doc_loaded and (len(self.selected_pages) > 0) else tk.DISABLED
        paste_enable_state = tk.NORMAL if has_clipboard_content and doc_loaded and (len(self.selected_pages) > 0) else tk.DISABLED 
        rotate_state = tk.NORMAL if doc_loaded and has_selection else tk.DISABLED
        undo_state = tk.NORMAL if has_undo else tk.DISABLED
        redo_state = tk.NORMAL if has_redo else tk.DISABLED
        import_state = tk.NORMAL if doc_loaded else tk.DISABLED 
        select_state = tk.NORMAL if doc_loaded else tk.DISABLED
        reverse_state = tk.NORMAL if doc_loaded else tk.DISABLED
        two_pages_state = tk.NORMAL if doc_loaded and len(self.selected_pages) == 2 else tk.DISABLED,
         
        # 1. Aktualizacja przycisków w panelu głównym
        self.save_button_icon.config(state=import_state)
        self.undo_button.config(state=undo_state)
        self.redo_button.config(state=redo_state)
        self.delete_button.config(state=delete_state)
        self.cut_button.config(state=delete_state)
        self.copy_button.config(state=delete_state)
        self.import_button.config(state=import_state) 
        self.image_import_button.config(state=import_state) 
        self.extract_button.config(state=delete_state) 
        self.export_image_button.config(state=delete_state) 
        self.insert_before_button.config(state=insert_state)
        self.insert_after_button.config(state=insert_state)
        self.paste_before_button.config(state=paste_enable_state)
        self.paste_after_button.config(state=paste_enable_state)
        self.rotate_left_button.config(state=rotate_state)
        self.rotate_right_button.config(state=rotate_state)
        self.shift_content_btn.config(state=delete_state)
        self.remove_nums_btn.config(state=delete_state)
        self.add_nums_btn.config(state=delete_state)
        
        if doc_loaded:
             zoom_in_state = tk.NORMAL if self.thumb_width < self.max_thumb_width else tk.DISABLED
             zoom_out_state = tk.NORMAL if self.thumb_width > self.min_thumb_width else tk.DISABLED
        else:
             zoom_in_state = tk.DISABLED
             zoom_out_state = tk.DISABLED
             
        self.zoom_in_button.config(state=zoom_in_state)
        self.zoom_out_button.config(state=zoom_out_state)

        # 2. Aktualizacja pozycji w menu
        menus_to_update = [self.file_menu, self.edit_menu, self.select_menu]
        if hasattr(self, 'context_menu'):
            menus_to_update.append(self.context_menu)
        if hasattr(self, 'modifications_menu'):
            menus_to_update.append(self.modifications_menu)
        if hasattr(self, 'external_menu'):
            menus_to_update.append(self.external_menu)
                # --- DYNAMICZNIE: dezaktywuj CAŁE menu Makra jeśli nie ma pliku ---
        if hasattr(self, 'macros_menu'):
            doc_loaded = self.pdf_document is not None
            for i in range(self.macros_menu.index("end") + 1):
                try:
                    # Pomijamy separator (separator nie ma state)
                    if self.macros_menu.type(i) == "command":
                        self.macros_menu.entryconfig(i, state=tk.NORMAL if doc_loaded else tk.DISABLED)
                except Exception:
                    continue
                    
        menu_state_map = {
            "Importuj strony z PDF...": import_state, 
            "Importuj obraz na nową stronę...": import_state,
            "Eksportuj strony do PDF...": delete_state,
            "Eksportuj strony jako obrazy PNG...": delete_state,            
            "Cofnij": undo_state,
            "Ponów": redo_state,
            "Wszystkie strony": select_state,
            "Strony nieparzyste": select_state,
            "Strony parzyste": select_state,
            "Strony pionowe": select_state,
            "Strony poziome": select_state,
            "Wytnij zaznaczone": delete_state,
            "Kopiuj zaznaczone": delete_state,
            "Usuń zaznaczone": delete_state,
            "Wklej przed": paste_enable_state,
            "Wklej po": paste_enable_state,
            "Duplikuj stronę": insert_state,
            "Wstaw nową stronę przed": insert_state,
            "Wstaw nową stronę po": insert_state,
            "Obróć w lewo (-90°)": rotate_state,
            "Obróć w prawo (+90°)": rotate_state,
            "Odwróć kolejność wszystkich stron": reverse_state,
            "Usuń numery stron...": delete_state, 
            "Wstaw numery stron...": delete_state, 
            "Przesuń zawartość stron...": delete_state,
            "Kadruj / zmień rozmiar...": delete_state,
            "Scal strony na arkuszu...": delete_state,
            "Zamknij plik": import_state, 
            "Zapisz jako...": import_state,
            "Zapisz jako plik z hasłem...": reverse_state,
            "Zamień strony miejscami": two_pages_state,
            "Usuń puste strony": reverse_state,
            "Analiza PDF": reverse_state
            
        }
        
        for menu in menus_to_update:
            for label, state in menu_state_map.items():
                try:
                    menu.entryconfig(label, state=state)
                except tk.TclError:
                    continue
    
       # --- Metody obsługi plików i edycji (Ze zmianami w import_image_to_new_page) ---
    
    def open_pdf(self, event=None, filepath=None):
        if self.pdf_document is not None and len(self.undo_stack) > 0:
            response = custom_messagebox(
                self.master, "Niezapisane zmiany",
                "Dokument został zmodyfikowany. Czy chcesz zapisać zmiany przed otwarciem nowego pliku?",
                typ="yesnocancel"
            )
            if response is None:
                return  # Anuluj
            elif response:  # Tak - zapisz
                self.save_document()
                if len(self.undo_stack) > 0:
                    return  # Jeśli nie udało się zapisać, nie otwieraj nowego pliku
            # jeśli Nie - kontynuuj

        if not filepath:
            # Użyj domyślnej ścieżki odczytu lub ostatniej użytej ścieżki
            default_read_path = self.prefs_manager.get('default_read_path', '')
            if default_read_path:
                initialdir = default_read_path
            else:
                initialdir = self.prefs_manager.get('last_open_path', '')
            
            filepath = filedialog.askopenfilename(
                filetypes=[("Pliki PDF", "*.pdf")],
                initialdir=initialdir if initialdir else None
            )
            if not filepath:  
                self._update_status("Anulowano otwieranie pliku.")
                return
            
            # Zapisz ostatnią ścieżkę tylko jeśli domyślna jest pusta
            if not default_read_path:
                import os
                self.prefs_manager.set('last_open_path', os.path.dirname(filepath))

        try:
            if self.pdf_document: self.pdf_document.close()
            
            # Krok 1: inicjalizacja progresu i status
            # Update status FIRST, then show progress bar to ensure message is visible
            self._update_status("Otwieranie pliku PDF... (krok 1/2)")
            
            # Krok 2: otwieranie pliku (może potrwać)
            # Ensure status is visible BEFORE the blocking fitz.open() call
            self._update_status("Otwieranie pliku PDF...")
            # fitz.open() is a blocking operation - status must be shown before it starts
            doc = fitz.open(filepath)
            
            # Krok 3: obsługa hasła
            if doc.is_encrypted:
                doc.close()
                password = self._ask_for_password()
                if password is None:
                    self._update_status("Anulowano otwieranie pliku.")
                    return
                # Show status BEFORE blocking operations
                self._update_status("Otwieranie pliku PDF z hasłem...")
                # fitz.open() is a blocking operation - status must be visible before it
                doc = fitz.open(filepath)
                if not doc.authenticate(password):
                    doc.close()
                    custom_messagebox(
                        self.master, 
                        "Błąd", 
                        "Nieprawidłowe hasło. Nie udało się otworzyć pliku PDF.",
                        typ="error"
                    )
                    self._update_status("BŁĄD: Nieprawidłowe hasło do pliku PDF.")
                    return
                
            
            # Krok 4: czyszczenie i GUI
            # Status is updated and visible immediately thanks to _update_status() calling update_idletasks()
            self._update_status("Wczytywanie dokumentu i czyszczenie widoku...")
            self.pdf_document = doc
            self.selected_pages = set()
            self.tk_images = {}
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.clipboard = None
            self.pages_in_clipboard_count = 0
            self.active_page_index = 0
            self.thumb_frames.clear()
            self.undo_stack.clear()
            self.redo_stack.clear()
            for widget in list(self.scrollable_frame.winfo_children()):
                widget.destroy()
            self.thumb_width = 205  # Reset to default thumbnail width
            self._reconfigure_grid()
            
            # Final status update - will be immediately visible
            self._update_status(f"Wczytano {len(self.pdf_document)} stron. Generowanie miniatur...")
            self.save_button_icon.config(state=tk.NORMAL)
            self.file_menu.entryconfig("Zapisz jako...", state=tk.NORMAL)
            self.update_tool_button_states()
            self.update_focus_display()
            self.prefs_manager.set('last_opened_file', filepath)   
            
        except Exception as e:
            self._update_status(f"BŁĄD: Nie udało się wczytać pliku PDF: {e}")
            self.pdf_document = None
            if hasattr(self, 'save_button_icon'):
                self.save_button_icon.config(state=tk.DISABLED)
            if hasattr(self, 'file_menu'):
                self.file_menu.entryconfig("Zapisz jako...", state=tk.DISABLED)
            self.update_tool_button_states()
    
    def close_pdf(self):
        if self.pdf_document is not None and len(self.undo_stack) > 0:
            response = custom_messagebox(
                self.master, "Niezapisane zmiany",
                "Dokument został zmodyfikowany. Czy chcesz zapisać zmiany przed zamknięciem pliku?",
                typ="yesnocancel"
            )
            if response is None:
                return  # Anuluj zamykanie pliku
            elif response is True:
                self.save_document()
                if len(self.undo_stack) > 0:
                    return  # Jeśli nie udało się zapisać, nie zamykaj pliku
            # jeśli Nie - kontynuuj zamykanie pliku (bez zapisu)
        if self.pdf_document is not None:
            self.pdf_document.close()
            self.pdf_document = None
        self.selected_pages.clear()
        self.tk_images.clear()
        self.thumb_frames.clear()
        for widget in list(self.scrollable_frame.winfo_children()):
            widget.destroy()
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.clipboard = None
        self.pages_in_clipboard_count = 0
        self.active_page_index = 0
        self._update_status("Zamknięto plik PDF. Wybierz plik z menu, aby rozpocząć pracę.")
        self.update_tool_button_states()
        self.update_focus_display()
    def open_image_as_new_pdf(self, filepath=None):
        """
        Otwiera obraz jako nowy PDF. 
        Strona PDF będzie miała dokładnie taki rozmiar jak obraz (w punktach PDF).
        Jeśli filepath jest podany (np. przez drag&drop), użyje go, inaczej wyświetli dialog wyboru pliku.
        """
        if filepath is None:
            image_path = filedialog.askopenfilename(
                filetypes=[("Obrazy", "*.png;*.jpg;*.jpeg;*.tif;*.tiff")],
                title="Wybierz plik obrazu do otwarcia jako PDF"
            )
            if not image_path:
                self._update_status("Anulowano otwieranie obrazu.")
                return
        else:
            image_path = filepath

        try:
            # Deleguj do PDFTools
            new_pdf_document = self.pdf_tools.create_pdf_from_image_exact_size(image_path)
            
            if new_pdf_document is None:
                custom_messagebox(self.master, "Błąd", "Nie można utworzyć PDF z obrazu.", typ="error")
                return
            
            # Zamień obecny dokument nowym
            if self.pdf_document:
                self.pdf_document.close()
            
            self.pdf_document = new_pdf_document
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.selected_pages.clear()
            self.tk_images.clear()
            for widget in list(self.scrollable_frame.winfo_children()): 
                widget.destroy()
            self.thumb_frames.clear()

            self.active_page_index = 0
            self._reconfigure_grid()
            self.update_tool_button_states()
            self.update_focus_display()
            self._update_status("Utworzono nowy PDF ze stroną dopasowaną do obrazu. Odświeżanie miniatur...")
        except Exception as e:
            custom_messagebox(self.master, "Błąd", f"Nie można wczytać obrazu: {e}", typ="error")
    
    def import_pdf_after_active_page(self, event=None, filepath=None):
        if self.pdf_document is None:
            self._update_status("BŁĄD: Otwórz najpierw dokument PDF.")
            return

        # Jeśli filepath jest podany (np. przez drag & drop), nie pokazuj dialogu
        if filepath:
            import_path = filepath
        else:
            import_path = filedialog.askopenfilename(
                title="Wybierz plik PDF do zaimportowania",
                filetypes=[("Pliki PDF", "*.pdf")]
            )
            if not import_path:
                self._update_status("Anulowano importowanie pliku.")
                return
                
        imported_doc = None
        selected_indices = None 
        try:
            # Show status before the potentially blocking fitz.open() operation
            self._update_status("Importowanie pliku PDF...")
            imported_doc = fitz.open(import_path)
            
            # Sprawdź czy dokument jest zaszyfrowany
            if imported_doc.is_encrypted:
                password = self._ask_for_password()
                
                if password is None:
                    # Użytkownik anulował
                    imported_doc.close()
                    self._update_status("Anulowano importowanie pliku.")
                    return
                
                # Spróbuj uwierzytelnić
                if not imported_doc.authenticate(password):
                    imported_doc.close()
                    custom_messagebox(
                        self.master, 
                        "Błąd", 
                        "Nieprawidłowe hasło. Nie udało się otworzyć pliku PDF.",
                        typ="error"
                    )
                    self._update_status("BŁĄD: Nieprawidłowe hasło do pliku PDF.")
                    return
            
            max_pages = len(imported_doc)

            # Jeśli wywołano przez drag&drop, importuj wszystko bez dialogu wyboru zakresu
            if filepath:
                selected_indices = list(range(max_pages))
            else:
                self.master.update_idletasks() 
                dialog = EnhancedPageRangeDialog(self.master, "Ustawienia importu PDF", imported_doc)
                selected_indices = dialog.result 
                if selected_indices is None or not selected_indices:
                    self._update_status("Anulowano importowanie lub nie wybrano stron.")
                    return

            # Jeśli przeciągnięto plik (filepath != None), wstaw po stronie z aktywnym kursorem
            if filepath is not None:
                insert_index = self.active_page_index + 1
            else:
                if len(self.selected_pages) == 1:
                    page_index = list(self.selected_pages)[0]
                    insert_index = page_index + 1 
                elif len(self.selected_pages) > 1:
                    insert_index = max(self.selected_pages) + 1
                else:
                    insert_index = len(self.pdf_document)
                            
            self._save_state_to_undo()
            num_inserted = len(selected_indices)
            temp_doc_for_insert = fitz.open()
            
            self.show_progressbar(maximum=num_inserted)
            self._update_status("Importowanie stron z PDF...")
            
            for idx, page_index_to_import in enumerate(selected_indices):
                temp_doc_for_insert.insert_pdf(imported_doc, from_page=page_index_to_import, to_page=page_index_to_import)
                self.update_progressbar(idx + 1)
            
            self.pdf_document.insert_pdf(temp_doc_for_insert, start_at=insert_index)
            temp_doc_for_insert.close()
            self.hide_progressbar()

            # Select the newly imported pages
            self.selected_pages = set(range(insert_index, insert_index + num_inserted))
            
            self.tk_images.clear()
            for widget in list(self.scrollable_frame.winfo_children()): widget.destroy()
            self.thumb_frames.clear()

            self._reconfigure_grid()
            self.update_selection_display()
            self.update_tool_button_states()
            self.update_focus_display()
            self._update_status(f"Zaimportowano {num_inserted} wybranych stron i wstawiono w pozycji {insert_index}. Odświeżanie miniatur...")

        except Exception as e:
            self.hide_progressbar()
            self._update_status(f"BŁĄD Importowania: Nie udało się wczytać lub wstawić pliku: {e}")
            
        finally:
            if imported_doc and not imported_doc.is_closed:
                imported_doc.close()
    
    def import_image_to_new_page(self, filepath=None):
        if self.pdf_document is None:
            self._update_status("Błąd", "Najpierw otwórz dokument PDF.")
            return

        # Jeśli przekazano filepath (np. przez drag&drop), pomiń dialog wyboru pliku
        if filepath:
            image_path = filepath
        else:
            image_path = filedialog.askopenfilename(
                filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.tif;*.tiff")],
                title="Wybierz plik obrazu do importu"
            )
            if not image_path:
                return

        # 1. Otwarcie dialogu i pobranie ustawień (tylko jeśli nie drag&drop)
        if filepath:
            try:
                img = Image.open(image_path)
                image_width_px, image_height_px = img.size
                image_dpi = img.info.get('dpi', (96, 96))[0] if isinstance(img.info.get('dpi'), tuple) else 96
                img.close()
            except Exception:
                image_dpi = 96
            settings = {
                'scaling_mode': "PAGE_TO_IMAGE",
                'alignment': "SRODEK",  # alignment nieistotny w tym trybie
                'scale_factor': 1.0,
                'page_orientation': "PIONOWO",  # nieistotne
                'image_dpi': image_dpi,
                'custom_width_mm': None,
                'custom_height_mm': None
            }
        else:
            dialog = ImageImportSettingsDialog(self.master, "Ustawienia importu obrazu", image_path, prefs_manager=self.prefs_manager)
            settings = dialog.result
            if not settings:
                return

        scaling_mode = settings['scaling_mode']
        alignment = settings['alignment']
        scale_factor = settings['scale_factor']
        page_orientation = settings['page_orientation']
        custom_width_mm = settings.get('custom_width_mm')
        custom_height_mm = settings.get('custom_height_mm')

        try:
            img = Image.open(image_path)
            image_width_px, image_height_px = img.size
            image_dpi = settings.get('image_dpi', 96)
            image_width_points = (image_width_px / image_dpi) * 72
            image_height_points = (image_height_px / image_dpi) * 72
            img.close()
        except Exception as e:
            custom_messagebox(self.master, "Błąd", f"Nie można wczytać obrazu: {e}", typ="error")
            return

        MM_TO_POINTS = 72 / 25.4

        # --- TRYB: DOKŁADNY WYMIAR STRONY - OBRAZ ROZCIĄGANY DO CAŁEJ STRONY ---
        if scaling_mode == "CUSTOM_SIZE" and custom_width_mm and custom_height_mm:
            page_w = custom_width_mm * MM_TO_POINTS
            page_h = custom_height_mm * MM_TO_POINTS
            rect = fitz.Rect(0, 0, page_w, page_h)
        # --- TRYB: STRONA DOPASOWANA DO OBRAZU ---
        elif scaling_mode == "PAGE_TO_IMAGE":
            page_w = image_width_points
            page_h = image_height_points
            rect = fitz.Rect(0, 0, page_w, page_h)
        # --- POZOSTAŁE TRYBY (proporcje zachowane, centrowanie, marginesy, itp.) ---
        else:
            if page_orientation == "PIONOWO":
                page_w, page_h = A4_WIDTH_POINTS, A4_HEIGHT_POINTS
            else:
                page_w, page_h = A4_HEIGHT_POINTS, A4_WIDTH_POINTS

            if scaling_mode == "ORYGINALNY":
                scale = scale_factor
            elif scaling_mode == "SKALA":
                scale = scale_factor
            elif scaling_mode == "DOPASUJ":
                scale_margin_points = MM_TO_POINTS * 50  # 50mm marginesu (25mm z każdej strony)
                scale_w = (page_w - scale_margin_points) / image_width_points
                scale_h = (page_h - scale_margin_points) / image_height_points
                scale = min(scale_w, scale_h)
            else:
                scale = 1.0

            final_w = image_width_points * scale
            final_h = image_height_points * scale

            offset_mm = 25.0
            offset_points = offset_mm * MM_TO_POINTS

            if alignment == "SRODEK":
                x_start = (page_w - final_w) / 2
                y_start = (page_h - final_h) / 2
            elif alignment == "GORA":
                x_start = (page_w - final_w) / 2
                y_start = offset_points
            elif alignment == "DOL":
                x_start = (page_w - final_w) / 2
                y_start = page_h - final_h - offset_points
            else:
                x_start = offset_points
                y_start = page_h - final_h - offset_points

            rect = fitz.Rect(x_start, y_start, x_start + final_w, y_start + final_h)

        imported_doc = fitz.open()
        try:
            imported_page = imported_doc.new_page(-1, width=page_w, height=page_h)
        except Exception as e:
            custom_messagebox(self.master, "Błąd inicjalizacji fitz", f"Nie udało się utworzyć tymczasowej strony PDF: {e}", typ="error")
            return

        # 5. Wklejenie obrazu do tymczasowej strony fitz
        try:
            imported_page.insert_image(rect, filename=image_path)

            # 6. Określenie pozycji wstawienia w głównym dokumencie
            insert_index = len(self.pdf_document)
            if len(self.selected_pages) == 1:
                page_index = list(self.selected_pages)[0]
                insert_index = page_index + 1
            elif len(self.selected_pages) > 1:
                insert_index = max(self.selected_pages) + 1
            else:
                insert_index = len(self.pdf_document)

            self._save_state_to_undo()
            self.pdf_document.insert_pdf(imported_doc, from_page=0, to_page=0, start_at=insert_index)
            
            # Select the newly imported image page
            self.selected_pages = {insert_index}
            self.active_page_index = insert_index

            self.tk_images.clear()
            for widget in list(self.scrollable_frame.winfo_children()):
                widget.destroy()
            self.thumb_frames.clear()

            self._reconfigure_grid()
            self.update_selection_display()
            self.update_tool_button_states()
            self.update_focus_display()

            self.status_bar.config(text=f"Zaimportowano obraz jako stronę na pozycji {insert_index + 1}. Aktualna liczba stron: {len(self.pdf_document)}. Odświeżanie miniatur...")

        except Exception as e:
            custom_messagebox(self.master, "Błąd Wklejania", f"Nie udało się wkleić obrazu: {e}", typ="error")
        finally:
            if imported_doc and not imported_doc.is_closed:
                imported_doc.close()
                
    def _update_status(self, message):
        """
        Updates the status bar with a message and ensures immediate GUI refresh.
        This method forces the GUI to update immediately so status messages are
        always visible, even before blocking operations.
        """
        self.status_bar.config(text=message, fg="black")
        # Force immediate GUI update so the status is visible before any blocking operation
        self.master.update_idletasks()
    
    def show_progressbar(self, maximum=100, mode="determinate"):
        """
        Pokazuje pasek postępu na pasku statusu.
        
        Args:
            maximum: Maksymalna wartość paska postępu (liczba kroków)
            mode: "determinate" (znana liczba kroków) lub "indeterminate" (nieznana liczba kroków)
        """
        self.progress_bar["mode"] = mode
        self.progress_bar["maximum"] = maximum
        self.progress_bar["value"] = 0
        self.progress_bar.pack(side=tk.RIGHT, padx=(5, 5))
        if mode == "indeterminate":
            self.progress_bar.start(10)  # Animacja w trybie nieokreślonym
        self.master.update_idletasks()
    
    def update_progressbar(self, value):
        """
        Aktualizuje wartość paska postępu i odświeża GUI.
        
        Args:
            value: Aktualna wartość postępu (0 do maximum)
        """
        self.progress_bar["value"] = value
        self.master.update_idletasks()
    
    def hide_progressbar(self):
        """
        Ukrywa pasek postępu po zakończeniu operacji.
        """
        self.progress_bar.stop()  # Zatrzymaj animację (jeśli była)
        self.progress_bar.pack_forget()
        self.master.update_idletasks()
            
    def _save_state_to_undo(self):
        """Zapisuje bieżący stan dokumentu na stosie undo i czyści stos redo."""
        if self.pdf_document:
            buffer = self.pdf_document.write()
            self.undo_stack.append(buffer)
            if len(self.undo_stack) > self.max_stack_size:
                self.undo_stack.pop(0)
            # Każda nowa modyfikacja czyści stos redo
            self.redo_stack.clear()
            self.update_tool_button_states()
        else:
            self.undo_stack.clear()
            self.redo_stack.clear()
            print("DEBUG: Czyszczenie historii _save_state_to_undo")
            self.update_tool_button_states()
            
    def _get_page_bytes(self, page_indices: Set[int]) -> bytes:
        """Wrapper dla PDFTools.get_page_bytes"""
        return self.pdf_tools.get_page_bytes(self.pdf_document, page_indices)
    
    def copy_selected_pages(self):
        if not self.pdf_document or not self.selected_pages:
            self._update_status("BŁĄD: Zaznacz strony do skopiowania.")
            return
        try:
            self.clipboard = self._get_page_bytes(self.selected_pages)
            self.pages_in_clipboard_count = len(self.selected_pages)
            self.selected_pages.clear()
            self.update_selection_display()
            self._update_status(f"Skopiowano {self.pages_in_clipboard_count} stron do schowka.")
        except Exception as e:
            self._update_status(f"BŁĄD Kopiowania: {e}")
            
    def cut_selected_pages(self):
        if not self.pdf_document or not self.selected_pages:
            self._update_status("BŁĄD: Zaznacz strony do wycięcia.")
            return
        try:
            self._save_state_to_undo()
            self.clipboard = self._get_page_bytes(self.selected_pages)
            self.pages_in_clipboard_count = len(self.selected_pages)
            pages_to_delete = sorted(list(self.selected_pages), reverse=True)
            
            # Użyj PDFTools do usunięcia stron
            deleted_count = self.pdf_tools.delete_pages(
                self.pdf_document,
                pages_to_delete,
                progress_callback=self._update_status,
                progressbar_callback=None
            )
            
            self.selected_pages.clear()
            
            # Validate and update active_page_index after deletion
            if self.pdf_document and len(self.pdf_document) > 0:
                self.active_page_index = min(self.active_page_index, len(self.pdf_document) - 1)
                self.active_page_index = max(0, self.active_page_index)
            else:
                self.active_page_index = 0
            
            self.tk_images.clear()
            for widget in list(self.scrollable_frame.winfo_children()): widget.destroy()
            self.thumb_frames.clear()  
            self._reconfigure_grid()
            self.update_tool_button_states()
            self.update_focus_display()
            self._update_status(f"Wycięto {deleted_count} stron i skopiowano do schowka. Odświeżanie miniatur...")
        except Exception as e:
            self._update_status(f"BŁĄD Wycinania: {e}")
            
    def paste_pages_before(self):
        self._handle_paste_operation(before=True)

    def paste_pages_after(self):
        self._handle_paste_operation(before=False)
        
    def _handle_paste_operation(self, before: bool):
        if not self.pdf_document or not self.clipboard:
            self._update_status("BŁĄD: Schowek jest pusty.")
            return

        num_selected = len(self.selected_pages)
        if num_selected == 0:
            self._update_status("BŁĄD: Wklejanie wymaga zaznaczenia przynajmniej jednej strony jako miejsca docelowego.")
            return
        temp_doc = fitz.open("pdf", self.clipboard)
        pages_per_paste = len(temp_doc)

        # Confirmation dialog for multiple pages
        if num_selected > 1:
            direction = "przed" if before else "po"
            result = custom_messagebox(
                self.master, "Potwierdzenie",
                f"Czy na pewno chcesz wkleić {pages_per_paste} stron {direction} {num_selected} stronach?",
                typ="question"
            )
            if not result:
                self._update_status("Anulowano wklejanie stron.")
                return

        if num_selected == 0:
            # No selection - paste at the end
            target_index = len(self.pdf_document)
            self._perform_paste(target_index)
        else:
            try:
                self._save_state_to_undo()
                # Sort selected pages rosnąco (wstawianie od końca nie sprawdza się, bo za każdym razem przesuwamy dokument)
                sorted_pages = sorted(self.selected_pages)
                new_page_indices = set()
                offset = 0  # Ile już wstawiono (przesunięcie indeksów po każdej insercji)

                # Pokaż pasek postępu
                self.show_progressbar(maximum=len(sorted_pages))
                self._update_status("Wklejanie stron...")

                for idx, page_index in enumerate(sorted_pages):
                    if before:
                        target_index = page_index + offset
                    else:
                        target_index = page_index + 1 + offset

                    self.pdf_document.insert_pdf(temp_doc, start_at=target_index)
                    # Dodajemy do zaznaczenia nowo wstawione indeksy
                    for i in range(pages_per_paste):
                        new_page_indices.add(target_index + i)
                    offset += pages_per_paste
                    self.update_progressbar(idx + 1)

                temp_doc.close()
                self.selected_pages = new_page_indices

                self.tk_images.clear()
                for widget in list(self.scrollable_frame.winfo_children()):
                    widget.destroy()
                self.thumb_frames.clear()
                self._reconfigure_grid()
                self.update_selection_display()
                self.update_tool_button_states()
                self.update_focus_display()

                self.hide_progressbar()
                
                num_inserted = pages_per_paste * num_selected
                if num_selected == 1:
                    self._update_status(f"Wklejono {pages_per_paste} stron. Odświeżanie miniatur...")
                else:
                    self._update_status(f"Wklejono {num_inserted} stron razem. Odświeżanie miniatur...")
            except Exception as e:
                self.hide_progressbar()
                self._update_status(f"BŁĄD Wklejania: {e}")

    def _perform_paste(self, target_index: int):
        try:
            self._save_state_to_undo()
            
            # Pokaż pasek postępu
            self.show_progressbar(mode="indeterminate")
            self._update_status("Wklejanie stron...")
            
            # Deleguj do PDFTools
            def progress_callback(current, total):
                self.update_progressbar(current) if current else None
            
            num_inserted = self.pdf_tools.paste_pages(
                self.pdf_document,
                self.clipboard,
                target_index,
                progress_callback=self._update_status,
                progressbar_callback=progress_callback
            )

            # Select the newly pasted pages
            self.selected_pages = set(range(target_index, target_index + num_inserted))

            self.tk_images.clear()
            for widget in list(self.scrollable_frame.winfo_children()):
                widget.destroy()
            self.thumb_frames.clear()
            self._reconfigure_grid()
            self.update_selection_display()
            self.update_tool_button_states()
            self.update_focus_display()
            
            self.hide_progressbar()
            self._update_status(f"Wklejono {num_inserted} stron w pozycji {target_index}. Odświeżanie miniatur...")
        except Exception as e:
            self.hide_progressbar()
            self._update_status(f"BŁĄD Wklejania: {e}")
            
    def delete_selected_pages(self, event=None, save_state: bool = True): 
        if not self.pdf_document or not self.selected_pages:
            self._update_status("BŁĄD: Brak zaznaczonych stron do usunięcia.")
            return
        
        pages_to_delete = sorted(list(self.selected_pages), reverse=True)
        # --- BLOKADA: NIE USUWAJ OSTATNIEJ STRONY ---
        if len(pages_to_delete) >= len(self.pdf_document):
            self._update_status("BŁĄD: Nie można usunąć wszystkich stron. PDF musi mieć przynajmniej jedną stronę.")
            return
        
        # Sprawdź czy wymagane jest potwierdzenie przed usunięciem
        confirm_delete = self.prefs_manager.get('confirm_delete', 'False')
        if confirm_delete == 'True':
            page_count = len(pages_to_delete)
            page_text = "stronę" if page_count == 1 else f"{page_count} stron"
            response = custom_messagebox(
                self.master, "Potwierdzenie usunięcia",
                f"Czy na pewno chcesz usunąć {page_text}?",
                typ="question"
            )
            if not response:
                self._update_status("Anulowano usuwanie stron.")
                return
        
        try:
            if save_state:
                self._save_state_to_undo()
            
            # Deleguj do PDFTools
            def progress_callback(current, total):
                if current == 0:
                    self.show_progressbar(maximum=total)
                self.update_progressbar(current)
                if current == total:
                    self.hide_progressbar()
            
            deleted_count = self.pdf_tools.delete_pages(
                self.pdf_document,
                pages_to_delete,
                progress_callback=self._update_status,
                progressbar_callback=progress_callback
            )
            
            self.selected_pages.clear()
            self.tk_images.clear()
            for widget in list(self.scrollable_frame.winfo_children()): widget.destroy()
            self.thumb_frames.clear()  
            self.total_pages = len(self.pdf_document)
            self.active_page_index = min(self.active_page_index, self.total_pages - 1)
            self.active_page_index = max(0, self.active_page_index)
            self._reconfigure_grid()  
            self.update_tool_button_states()
            self.update_focus_display()  
            if save_state:
                self._update_status(
                    f"Usunięto {deleted_count} stron. Aktualna liczba stron: {self.total_pages}. Odświeżanie miniatur..."
                )
        except Exception as e:
            self.hide_progressbar()
            self._update_status(f"BŁĄD: Wystąpił błąd podczas usuwania: {e}")

    def extract_selected_pages(self):
        if not self.pdf_document or not self.selected_pages:
            self._update_status("BŁĄD: Zaznacz strony, które chcesz wyodrębnić do nowego pliku.")
            return
        
        selected_indices = sorted(list(self.selected_pages))
        
        # Jeśli więcej niż jedna strona, zapytaj o tryb eksportu
        export_mode = "single"  # domyślnie wszystkie do jednego pliku
        if len(selected_indices) > 1:
            # Dialog wyboru trybu
            dialog = tk.Toplevel(self.master)
            dialog.title("Tryb eksportu")
            dialog.transient(self.master)
            dialog.grab_set()
            dialog.resizable(False, False)
            
            main_frame = ttk.Frame(dialog, padding="12")
            main_frame.pack(fill="both", expand=True)
            
            ttk.Label(main_frame, text="Wybierz tryb eksportu:").pack(anchor="w", pady=(0, 8))
            
            mode_var = tk.StringVar(value="single")
            ttk.Radiobutton(main_frame, text="Wszystkie strony do jednego pliku PDF", variable=mode_var, value="single").pack(anchor="w", pady=2)
            ttk.Radiobutton(main_frame, text="Każda strona do osobnego pliku PDF", variable=mode_var, value="separate").pack(anchor="w", pady=2)
            
            result = [None]
            
            def on_ok():
                result[0] = mode_var.get()
                dialog.destroy()
            
            def on_cancel():
                dialog.destroy()
            
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(pady=(12, 0))
            ttk.Button(button_frame, text="OK", command=on_ok, width=10).pack(side="left", padx=4)
            ttk.Button(button_frame, text="Anuluj", command=on_cancel, width=10).pack(side="left", padx=4)
            
            dialog.bind("<Return>", lambda e: on_ok())
            dialog.bind("<Escape>", lambda e: on_cancel())
            
            # Wyśrodkuj
            dialog.update_idletasks()
            dialog_w = dialog.winfo_width()
            dialog_h = dialog.winfo_height()
            parent_x = self.master.winfo_rootx()
            parent_y = self.master.winfo_rooty()
            parent_w = self.master.winfo_width()
            parent_h = self.master.winfo_height()
            x = parent_x + (parent_w - dialog_w) // 2
            y = parent_y + (parent_h - dialog_h) // 2
            dialog.geometry(f"+{x}+{y}")
            
            dialog.wait_window()
            
            if result[0] is None:
                self._update_status("Anulowano ekstrakcję stron.")
                return
            export_mode = result[0]
        
        # Pobierz nazwę bazową pliku
        if hasattr(self, 'file_path') and self.file_path:
            base_filename = os.path.splitext(os.path.basename(self.file_path))[0]
        else:
            base_filename = "dokument"
        
        if export_mode == "single":
            # Wszystkie strony do jednego pliku
            output_dir = filedialog.askdirectory(
                title="Wybierz folder do zapisu PDF"
            )
            if not output_dir:
                self._update_status("Anulowano ekstrakcję stron.")
                return
            
            try:
                # Utwórz zakres stron
                if len(selected_indices) == 1:
                    page_range = str(selected_indices[0] + 1)
                else:
                    page_range = f"{selected_indices[0] + 1}-{selected_indices[-1] + 1}"
                
                # Generuj unikalną nazwę pliku
                filepath = generate_unique_export_filename(
                    output_dir, base_filename, page_range, "pdf"
                )
                
                # Deleguj do PDFTools
                def progress_callback(current, total):
                    if current == 0:
                        self.show_progressbar(maximum=total)
                    self.update_progressbar(current)
                    if current == total:
                        self.hide_progressbar()
                
                success = self.pdf_tools.extract_pages_to_single_pdf(
                    self.pdf_document, selected_indices, filepath,
                    progress_callback=self._update_status,
                    progressbar_callback=progress_callback
                )
                
                if success:
                    self._update_status(f"Pomyślnie wyodrębniono {len(selected_indices)} stron do: {filepath}")
                else:
                    self._update_status(f"BŁĄD: Nie udało się wyodrębnić stron")
            except Exception as e:
                self.hide_progressbar()
                self._update_status(f"BŁĄD Eksportu: Nie udało się zapisać nowego pliku: {e}")
        else:
            # Każda strona do osobnego pliku
            output_dir = filedialog.askdirectory(
                title="Wybierz folder do zapisu plików PDF"
            )
            if not output_dir:
                self._update_status("Anulowano ekstrakcję stron.")
                return
            
            try:
                # Deleguj do PDFTools
                def progress_callback(current, total):
                    if current == 0:
                        self.show_progressbar(maximum=total)
                    self.update_progressbar(current)
                    if current == total:
                        self.hide_progressbar()
                
                exported_count = self.pdf_tools.extract_pages_to_separate_pdfs(
                    self.pdf_document, selected_indices, output_dir, base_filename,
                    progress_callback=self._update_status,
                    progressbar_callback=progress_callback
                )
                
                self.hide_progressbar()
                self._update_status(f"Pomyślnie wyodrębniono {exported_count} stron do folderu: {output_dir}")
            except Exception as e:
                self.hide_progressbar()
                self._update_status(f"BŁĄD Eksportu: Nie udało się zapisać plików: {e}")

    def undo(self):
        """Cofnij ostatnią operację - przywraca stan ze stosu undo."""
        if len(self.undo_stack) == 0:
            self._update_status("Brak operacji do cofnięcia!")
            return

        # Zapisz bieżący stan na stos redo
        if self.pdf_document:
            current_state = self.pdf_document.write()
            self.redo_stack.append(current_state)
            if len(self.redo_stack) > self.max_stack_size:
                self.redo_stack.pop(0)

        # Pobierz poprzedni stan ze stosu undo
        previous_state_bytes = self.undo_stack.pop()
        
        try:
            old_page_count = len(self.pdf_document) if self.pdf_document else 0

            if self.pdf_document:
                self.pdf_document.close()
            self.pdf_document = fitz.open("pdf", previous_state_bytes)
            new_page_count = len(self.pdf_document)

            # Przywróć selekcję i indeks aktywnej strony
            self.selected_pages.clear()

            # Jeśli liczba stron się nie zmieniła – nie czyść ramek/widgetów!
            if old_page_count == new_page_count and self.thumb_frames:
                self.tk_images.clear()
                # Pokaz progress bar dla odświeżenia miniatur (jeśli plik jest duży)
                if new_page_count > 10:
                    self.show_progressbar(maximum=new_page_count, mode="determinate")
                else:
                    self.show_progressbar(maximum=1, mode="determinate")
                self._update_status("Przywracanie dokumentu po cofnięciu...")

                # Validate and clamp active_page_index to valid range
                if self.pdf_document and new_page_count > 0:
                    self.active_page_index = min(self.active_page_index, new_page_count - 1)
                    self.active_page_index = max(0, self.active_page_index)
                else:
                    self.active_page_index = 0

                for idx in range(new_page_count):
                    self._update_status("Cofnięto ostatnią operację. Odświeżanie miniatur...")
                    self.update_single_thumbnail(idx)
                    if new_page_count > 10:
                        self.update_progressbar(idx + 1)
            else:
                # Liczba stron się zmieniła: czyść wszystko i przebuduj siatkę
                self.selected_pages.clear()
                self.tk_images.clear()
                self.thumb_frames.clear()
                for widget in list(self.scrollable_frame.winfo_children()):
                    widget.destroy()
                self._reconfigure_grid()
                # Validate and clamp active_page_index to valid range
                if self.pdf_document and new_page_count > 0:
                    self.active_page_index = min(self.active_page_index, new_page_count - 1)
                    self.active_page_index = max(0, self.active_page_index)
                else:
                    self.active_page_index = 0

            self.update_tool_button_states()
            self.update_focus_display()
            self.hide_progressbar()
            self._update_status("Cofnięto ostatnią operację. Odświeżanie miniatur...")
        except Exception as e:
            self.hide_progressbar()
            self._update_status(f"BŁĄD: Nie udało się cofnąć operacji: {e}")
            self.pdf_document = None
            self.update_tool_button_states()
            
    def redo(self):
        """Ponów cofniętą operację - przywraca stan ze stosu redo."""
        if len(self.redo_stack) == 0:
            self._update_status("Brak operacji do ponowienia!")
            return

        # Zapisz bieżący stan na stos undo
        if self.pdf_document:
            current_state = self.pdf_document.write()
            self.undo_stack.append(current_state)
            if len(self.undo_stack) > self.max_stack_size:
                self.undo_stack.pop(0)

        # Pobierz następny stan ze stosu redo
        next_state_bytes = self.redo_stack.pop()
        
        try:
            old_page_count = len(self.pdf_document) if self.pdf_document else 0

            if self.pdf_document:
                self.pdf_document.close()
            self.pdf_document = fitz.open("pdf", next_state_bytes)
            new_page_count = len(self.pdf_document)

            # Przywróć selekcję i indeks aktywnej strony
            self.selected_pages.clear()

            # Jeśli liczba stron się nie zmieniła – nie czyść ramek/widgetów!
            if old_page_count == new_page_count and self.thumb_frames:
                self.tk_images.clear()
                # Pokaz progress bar dla odświeżenia miniatur (jeśli plik jest duży)
                if new_page_count > 10:
                    self.show_progressbar(maximum=new_page_count, mode="determinate")
                else:
                    self.show_progressbar(maximum=1, mode="determinate")
                self._update_status("Przywracanie dokumentu po ponowieniu...")

                # Validate and clamp active_page_index to valid range
                if self.pdf_document and new_page_count > 0:
                    self.active_page_index = min(self.active_page_index, new_page_count - 1)
                    self.active_page_index = max(0, self.active_page_index)
                else:
                    self.active_page_index = 0

                for idx in range(new_page_count):
                    self._update_status("Ponowiono operację. Odświeżanie miniatur...")
                    self.update_single_thumbnail(idx)
                    if new_page_count > 10:
                        self.update_progressbar(idx + 1)
            else:
                # Liczba stron się zmieniła: czyść wszystko i przebuduj siatkę
                self.selected_pages.clear()
                self.tk_images.clear()
                self.thumb_frames.clear()
                for widget in list(self.scrollable_frame.winfo_children()):
                    widget.destroy()
                self._reconfigure_grid()
                # Validate and clamp active_page_index to valid range
                if self.pdf_document and new_page_count > 0:
                    self.active_page_index = min(self.active_page_index, new_page_count - 1)
                    self.active_page_index = max(0, self.active_page_index)
                else:
                    self.active_page_index = 0

            self.update_tool_button_states()
            self.update_focus_display()
            self.hide_progressbar()
            self._update_status("Ponowiono operację. Odświeżanie miniatur...")
        except Exception as e:
            self.hide_progressbar()
            self._update_status(f"BŁĄD: Nie udało się ponowić operacji: {e}")
            self.pdf_document = None
            self.update_tool_button_states()
        
    def save_document(self):
        if not self.pdf_document: return
        
        # Użyj domyślnej ścieżki zapisu lub ostatniej użytej ścieżki
        default_save_path = self.prefs_manager.get('default_save_path', '')
        if default_save_path:
            initialdir = default_save_path
        else:
            initialdir = self.prefs_manager.get('last_save_path', '')
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Pliki PDF", "*.pdf")],
            title="Zapisz zmodyfikowany PDF jako...",
            initialdir=initialdir if initialdir else None
        )
        if not filepath:  
            self._update_status("Anulowano zapisywanie.")
            return
        
        # Zapisz ostatnią ścieżkę tylko jeśli domyślna jest pusta
        if not default_save_path:
            import os
            self.prefs_manager.set('last_save_path', os.path.dirname(filepath))
        
        try:
            self.pdf_document.save(filepath, garbage=4, clean=True, pretty=True)  
            self._update_status(f"Dokument pomyślnie zapisany jako: {filepath}")
            self.prefs_manager.set('last_saved_file', filepath) 
            # Po zapisaniu czyścimy stosy undo/redo
            self.undo_stack.clear()
            self.redo_stack.clear()
            print("DEBUG: Czyszczenie historii save_document")
            self.update_tool_button_states() 
            
        except Exception as e:
            self._update_status(f"BŁĄD: Nie udało się zapisać pliku: {e}")
            
    def rotate_selected_page(self, angle):
        if not self.pdf_document or not self.selected_pages: 
            self._update_status("BŁĄD: Zaznacz strony do obrotu.")
            return
        
        # Nagraj akcję
        if angle == -90:
            self._record_action('rotate_left')
        elif angle == 90:
            self._record_action('rotate_right')
        
        pages_to_rotate = sorted(list(self.selected_pages))
        try:
            self._save_state_to_undo()
            
            # Deleguj do PDFTools
            def progress_callback(current, total):
                if current == 0:
                    self.show_progressbar(maximum=total)
                self.update_progressbar(current)
                if current == total:
                    self.hide_progressbar()
            
            rotated_count = self.pdf_tools.rotate_pages(
                self.pdf_document,
                pages_to_rotate,
                angle,
                progress_callback=self._update_status,
                progressbar_callback=progress_callback
            )
            
            # Optymalizacja: odśwież tylko zmienione miniatury
            self.show_progressbar(maximum=len(pages_to_rotate))
            for i, page_index in enumerate(pages_to_rotate):
                self._update_status(f"Obrócono {rotated_count} stron o {angle} stopni. Odświeżanie miniatur...")
                self.update_single_thumbnail(page_index)
                self.update_progressbar(i + 1)
            self.hide_progressbar()
            
            self.update_tool_button_states()
            self.update_focus_display()
            self._update_status(f"Obrócono {rotated_count} stron o {angle} stopni.")
        except Exception as e:
            self.hide_progressbar()
            self._update_status(f"BŁĄD: Wystąpił błąd podczas obracania: {e}")

    def insert_blank_page_before(self):
           self._handle_insert_operation(before=True)

    def insert_blank_page_after(self):
        self._handle_insert_operation(before=False)
        
    def _handle_insert_operation(self, before: bool):
        if not self.pdf_document or len(self.selected_pages) < 1:  
            self._update_status("BŁĄD: Zaznacz przynajmniej jedną stronę, aby wstawić obok niej nową.")
            return
        
        num_selected = len(self.selected_pages)
        if num_selected > 1:
            direction = "przed" if before else "po"
            result = custom_messagebox(
                self.master, "Potwierdzenie",
                f"Czy na pewno chcesz wstawić pustą stronę {direction} {num_selected} stronach?",
                typ="question"
            )
            if not result:
                self._update_status("Anulowano wstawianie pustych stron.")
                return

        width, height = (595.276, 841.89)  # Domyślny A4

        try:
            self._save_state_to_undo()

            sorted_pages = sorted(self.selected_pages)
            
            # Pobierz rozmiar z pierwszej strony jeśli możliwe
            try:
                rect = self.pdf_document[sorted_pages[0]].rect
                width = rect.width
                height = rect.height  
            except Exception:
                pass  # Zostaw domyślne A4

            # Deleguj do PDFTools
            def progress_callback(current, total):
                if current == 0:
                    self.show_progressbar(maximum=total)
                self.update_progressbar(current)
                if current == total:
                    self.hide_progressbar()
            
            new_page_indices = self.pdf_tools.insert_blank_pages(
                self.pdf_document,
                sorted_pages,
                before,
                width,
                height,
                progress_callback=self._update_status,
                progressbar_callback=progress_callback
            )

            self.selected_pages = new_page_indices

            self.tk_images.clear()
            for widget in list(self.scrollable_frame.winfo_children()):
                widget.destroy()
            self.thumb_frames.clear()
            self._reconfigure_grid()
            self.update_selection_display()
            self.update_tool_button_states()
            self.update_focus_display()
            
            if num_selected == 1:
                self._update_status(f"Wstawiono nową, pustą stronę. Aktualna liczba stron: {len(self.pdf_document)}. Odświeżanie miniatur...")
            else:
                self._update_status(f"Wstawiono {num_selected} nowych, pustych stron. Aktualna liczba stron: {len(self.pdf_document)}. Odświeżanie miniatur...")
        except Exception as e:
            self.hide_progressbar()
            self._update_status(f"BŁĄD: Wystąpił błąd podczas wstawiania: {e}")
    
    def duplicate_selected_page(self):
        """Duplikuje zaznaczone strony i wstawia je zaraz po oryginałach."""
        if not self.pdf_document or len(self.selected_pages) < 1:
            self._update_status("BŁĄD: Zaznacz przynajmniej jedną stronę, aby ją zduplikować.")
            return

        num_selected = len(self.selected_pages)

        # Confirmation dialog for multiple pages
        if num_selected > 1:
            result = custom_messagebox(
                self.master, "Potwierdzenie",
                f"Czy na pewno zduplikować {num_selected} stron?",
                typ="question"
            )
            if not result:
                self._update_status("Anulowano duplikowanie stron.")
                return

        try:
            self._save_state_to_undo()

            # Sort pages in ascending order
            sorted_pages = sorted(self.selected_pages)
            new_page_indices = set()
            offset = 0
            
            self.show_progressbar(maximum=len(sorted_pages))
            self._update_status("Duplikowanie stron...")

            for idx_progress, original_index in enumerate(sorted_pages):
                # Po każdej insercji kolejne strony są przesunięte o offset
                idx = original_index + offset
                
                # Użyj PDFTools do duplikacji
                self.pdf_tools.duplicate_page(self.pdf_document, idx, idx + 1)
                
                # Wstawiona strona jest zawsze na pozycji idx+1
                new_page_indices.add(idx + 1)
                offset += 1
                self.update_progressbar(idx_progress + 1)

            self.hide_progressbar()
            self.selected_pages = new_page_indices

            # Odświeżenie GUI
            self.tk_images.clear()
            for widget in list(self.scrollable_frame.winfo_children()):
                widget.destroy()
            self.thumb_frames.clear()
            self._reconfigure_grid()
            self.update_selection_display()
            self.update_tool_button_states()
            self.update_focus_display()

            if num_selected == 1:
                self._update_status(f"Zduplikowano 1 stronę. Odświeżanie miniatur...")
            else:
                self._update_status(f"Zduplikowano {num_selected} stron. Odświeżanie miniatur...")
        except Exception as e:
            self.hide_progressbar()
            self._update_status(f"BŁĄD: Wystąpił błąd podczas duplikowania strony: {e}")
  
    def swap_pages(self):
        """Zamienia miejscami dokładnie 2 zaznaczone strony."""
        if not self.pdf_document or len(self.selected_pages) != 2:
            self._update_status("BŁĄD: Zaznacz dokładnie 2 strony, aby je zamienić miejscami.")
            return
        
        try:
            self._save_state_to_undo()
            
            self.show_progressbar(maximum=4)
            self._update_status("Zamiana stron miejscami...")
            
            # Get the two page indices
            pages = sorted(list(self.selected_pages))
            page1_idx = pages[0]
            page2_idx = pages[1]
            
            # Deleguj do PDFTools
            self.pdf_tools.swap_pages(self.pdf_document, page1_idx, page2_idx)
            self.update_progressbar(4)
            
            # Odśwież tylko zamienione miniatury
            self.update_single_thumbnail(page1_idx)
            self.update_single_thumbnail(page2_idx)
            
            self.update_selection_display()
            self.update_tool_button_states()
            self.update_focus_display()
            self.hide_progressbar()
            self._update_status(f"Zamieniono strony {page1_idx + 1} i {page2_idx + 1} miejscami.")
        except Exception as e:
            self.hide_progressbar()
            self._update_status(f"BŁĄD: Wystąpił błąd podczas zamiany stron: {e}")
  
    def merge_pages_to_grid(self):
        """
        Scala zaznaczone strony w siatkę na nowym arkuszu.
        Bitmapy renderowane są w 600dpi (bardzo wysoka jakość do druku).
        Przed renderowaniem każda strona jest automatycznie obracana jeśli jej orientacja nie pasuje do komórki siatki.
        Marginesy i odstępy pobierane są z dialogu (osobno dla każdej krawędzi/osi).
        """
        if not self.pdf_document:
            self._update_status("BŁĄD: Otwórz najpierw dokument PDF.")
            return
        if len(self.selected_pages) == 0:
            self._update_status("BŁĄD: Zaznacz przynajmniej jedną stronę do scalenia.")
            return

        selected_indices = sorted(list(self.selected_pages))
        num_pages = len(selected_indices)

        # Pokaż dialog ustawień
        dialog = MergePageGridDialog(self.master, page_count=num_pages, prefs_manager=self.prefs_manager)
        params = dialog.result
        if params is None:
            self._update_status("Anulowano scalanie stron.")
            return

        try:
            # Konwersja jednostek z mm na punkty
            sheet_width_pt = params["sheet_width_mm"] * self.MM_TO_POINTS
            sheet_height_pt = params["sheet_height_mm"] * self.MM_TO_POINTS
            margin_top_pt = params["margin_top_mm"] * self.MM_TO_POINTS
            margin_bottom_pt = params["margin_bottom_mm"] * self.MM_TO_POINTS
            margin_left_pt = params["margin_left_mm"] * self.MM_TO_POINTS
            margin_right_pt = params["margin_right_mm"] * self.MM_TO_POINTS
            spacing_x_pt = params["spacing_x_mm"] * self.MM_TO_POINTS
            spacing_y_pt = params["spacing_y_mm"] * self.MM_TO_POINTS
            rows = params["rows"]
            cols = params["cols"]
            target_dpi = params.get("dpi", 600)

            self._save_state_to_undo()
            
            # Deleguj do PDFTools
            def progress_callback(current, total):
                if current == 0:
                    self.show_progressbar(maximum=total)
                self.update_progressbar(current)
                if current == total:
                    self.hide_progressbar()
            
            self.pdf_tools.merge_pages_into_grid(
                self.pdf_document, selected_indices, rows, cols,
                sheet_width_pt, sheet_height_pt,
                margin_top_pt, margin_bottom_pt,
                margin_left_pt, margin_right_pt,
                spacing_x_pt, spacing_y_pt,
                target_dpi,
                progress_callback=self._update_status,
                progressbar_callback=progress_callback
            )

            # Odświeżenie GUI
            self.hide_progressbar()
            self.tk_images.clear()
            for widget in list(self.scrollable_frame.winfo_children()):
                widget.destroy()
            self.thumb_frames.clear()
            self._reconfigure_grid()
            self.update_tool_button_states()
            self.update_focus_display()
            self._update_status(
                f"Scalono {num_pages} stron w siatkę {rows}x{cols} na nowym arkuszu {params['format_name']} (bitmapy {target_dpi}dpi). Odświeżanie miniatur..."
            )
        except Exception as e:
            self.hide_progressbar()
            self._update_status(f"BŁĄD: Nie udało się scalić stron: {e}")
            import traceback
            traceback.print_exc()
            
    # --- Metody obsługi widoku/GUI (Bez zmian) ---
    def _on_mousewheel(self, event):
        # Oblicz różnicę w pozycji yview w zależności od scrolla
        step = 0.05  # Im mniejsza liczba, tym łagodniejsze przewijanie (np. 0.02)
        current_top, _ = self.canvas.yview()
        if event.num == 4 or event.delta > 0:
            new_pos = max(0, current_top - step)
            self.canvas.yview_moveto(new_pos)
        elif event.num == 5 or event.delta < 0:
            new_pos = min(1, current_top + step)
            self.canvas.yview_moveto(new_pos)
            
    def _get_current_num_cols(self):
        """Calculate current number of columns based on canvas width and thumb_width"""
        if not self.pdf_document:
            return 1
        
        actual_canvas_width = self.canvas.winfo_width()
        scrollbar_safety = 25
        available_width = max(100, actual_canvas_width - scrollbar_safety)
        thumb_with_padding = self.thumb_width + (2 * self.THUMB_PADDING)
        num_cols = max(self.min_cols, int(available_width / thumb_with_padding))
        num_cols = min(self.max_cols, num_cols)
        return max(1, num_cols)

    def zoom_in(self):
        self.master.state('zoomed')
        """Increase thumbnail size (zoom in)"""
        if self.pdf_document:
            new_width = int(self.thumb_width * (1 + self.zoom_step))
            self.thumb_width = min(self.max_thumb_width, new_width)
            self._reconfigure_grid()
            self.update_tool_button_states()  
            print(f"Zoom in: thumb_width = {self.thumb_width}")

    def zoom_out(self):
        self.master.state('normal')
        """Decrease thumbnail size (zoom out)"""
        if self.pdf_document:
            new_width = int(self.thumb_width * (1 - self.zoom_step))
            self.thumb_width = max(self.min_thumb_width, new_width)
            self._reconfigure_grid()
            self.update_tool_button_states()
            print(f"Zoom out: thumb_width = {self.thumb_width}")

    def _reconfigure_grid(self, event=None):
        # Poprawka: sprawdzanie, czy dokument istnieje i nie jest zamknięty (NIE używaj "not self.pdf_document"!)
        if self.pdf_document is None or getattr(self.pdf_document, "is_closed", False):
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
            return

        # Debouncing: cancel previous timer if exists
        if self._resize_timer is not None:
            self.master.after_cancel(self._resize_timer)

        # Schedule the actual reconfiguration after a delay
        self._resize_timer = self.master.after(self._resize_delay, self._do_reconfigure_grid)

    def _do_reconfigure_grid(self):
        """Actual grid reconfiguration logic (debounced)"""
        self._resize_timer = None

        # Poprawka: sprawdzanie, czy dokument istnieje i nie jest zamknięty (NIE używaj "not self.pdf_document"!)
        if self.pdf_document is None or getattr(self.pdf_document, "is_closed", False):
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
            return

        self.master.update_idletasks()
        actual_canvas_width = self.canvas.winfo_width()
        scrollbar_safety = 25  
        available_width = max(100, actual_canvas_width - scrollbar_safety)

        # Calculate number of columns based on current thumbnail width
        thumb_with_padding = self.thumb_width + (2 * self.THUMB_PADDING)
        num_cols = max(self.min_cols, int(available_width / thumb_with_padding))
        num_cols = min(self.max_cols, num_cols)  # Cap at max_cols

        if num_cols < 1:
            num_cols = 1

        column_width = self.thumb_width

        # Clean up non-thumbnail widgets
        for widget in list(self.scrollable_frame.grid_slaves()):
             if not isinstance(widget, ThumbnailFrame):
                 widget.destroy()

        # Configure grid columns
        for col in range(self.max_cols):  
             if col < num_cols:
                 self.scrollable_frame.grid_columnconfigure(col, weight=0, minsize=column_width)
             else:
                 self.scrollable_frame.grid_columnconfigure(col, weight=0, minsize=0)

        # Create or update widgets
        if not self.thumb_frames:
             self._create_widgets(num_cols, column_width)
        else:
             self._update_widgets(num_cols, column_width)

        self.scrollable_frame.update_idletasks()  
        bbox = self.canvas.bbox("all")
        if bbox is not None:
              self.canvas.config(scrollregion=(bbox[0], 0, bbox[2], bbox[3]))
              self.canvas.yview_moveto(0.0)  
              self.canvas.coords(self.canvas_window_id, 0, 0)
              self.canvas.yview_moveto(0.0)
        else:
              self.canvas.config(scrollregion=(0, 0, actual_canvas_width, 10))


    def _get_page_size_label(self, page_index):
        if not self.pdf_document: return ""
        page = self.pdf_document.load_page(page_index)
        page_width = page.rect.width
        page_height = page.rect.height
        width_mm = round(page_width / 72 * 25.4)
        height_mm = round(page_height / 72 * 25.4)
        
        # Popularne formaty (dopuszczamy tolerancję ±5mm)
        known_formats = {
            "A6": (105, 148),
            "A5": (148, 210),
            "A4": (210, 297),
            "A3": (297, 420),
            "A2": (420, 594),
            "A1": (594, 841),
            "A0": (841, 1189),
            # Format B (ISO 216)
            "B0": (1000, 1414),
            "B1": (707, 1000),
            "B2": (500, 707),
            "B3": (353, 500),
            "B4": (250, 353),
            "B5": (176, 250),
            "B6": (125, 176),
            "Letter": (216, 279),   # 8.5 × 11 in
            "Legal": (216, 356),    # 8.5 × 14 in
            "Tabloid": (279, 432),  # 11 × 17 in
        }
        # Tolerancja ±5mm
        tol = 5
        for name, (fw, fh) in known_formats.items():
            if (abs(width_mm - fw) <= tol and abs(height_mm - fh) <= tol) or \
               (abs(width_mm - fh) <= tol and abs(height_mm - fw) <= tol):
                if abs(width_mm - fw) < abs(width_mm - fh):
                    return name
                else:
                    return f"{name} (Poziom)"
        return f"{width_mm} x {height_mm} mm"


    def _create_widgets(self, num_cols, column_width):
        """Tworzy wszystkie ramki miniatur dla aktualnego dokumentu PDF."""
        page_count = len(self.pdf_document)
        # Dodaj pasek postępu tylko przy większej liczbie stron (np. 10+), by nie przeszkadzać przy szybkim ładowaniu
        if page_count > 10:
            self.show_progressbar(maximum=page_count, mode="determinate")
        for i in range(page_count):
            page_frame = ThumbnailFrame(
                parent=self.scrollable_frame,  
                viewer_app=self,  
                page_index=i,  
                column_width=column_width
            )
            page_frame.grid(row=i // num_cols, column=i % num_cols, padx=self.THUMB_PADDING, pady=self.THUMB_PADDING, sticky="n")  
            self.thumb_frames[i] = page_frame  
            if page_count > 10:
                self.update_progressbar(i + 1)
        if page_count > 10:
            self.hide_progressbar()
        self.update_selection_display()
        self.update_focus_display()

    def _update_widgets(self, num_cols, column_width):
        page_count = len(self.pdf_document)
        frame_bg = "#F5F5F5"

        # Dodaj brakujące ramki miniaturek
        for i in range(page_count):
            if i not in self.thumb_frames:
                page_frame = ThumbnailFrame(
                    parent=self.scrollable_frame,
                    viewer_app=self,
                    page_index=i,
                    column_width=column_width
                )
                self.thumb_frames[i] = page_frame

        # Usuń nadmiarowe ramki (jeśli stron jest mniej niż widgetów)
        to_remove = [idx for idx in self.thumb_frames if idx >= page_count]
        for idx in to_remove:
            self.thumb_frames[idx].destroy()
            del self.thumb_frames[idx]

        for i in range(page_count):
            page_frame = self.thumb_frames[i]
            page_frame.grid(row=i // num_cols, column=i % num_cols, padx=self.THUMB_PADDING, pady=self.THUMB_PADDING, sticky="n")
            img_tk = self._render_and_scale(i, column_width)
            page_frame.img_label.config(image=img_tk)
            page_frame.img_label.image = img_tk
            outer_frame_children = page_frame.outer_frame.winfo_children()
            if len(outer_frame_children) > 2:
                outer_frame_children[1].config(text=f"Strona {i + 1}", bg=frame_bg)
                outer_frame_children[2].config(text=self._get_page_size_label(i), bg=frame_bg)

        self.update_selection_display()
        self.update_focus_display()

    
    def _render_and_scale(self, page_index, column_width):
        # Diagnostyka cache miniaturek
        if page_index in self.tk_images and column_width in self.tk_images[page_index]:
            print(f"[CACHE] Używam cache dla strony {page_index}, szerokość {column_width}")
            return self.tk_images[page_index][column_width]

        print(f"[RENDER] Generuję miniaturę dla strony {page_index}, szerokość {column_width}")
        page = self.pdf_document.load_page(page_index)
        page_width = page.rect.width
        page_height = page.rect.height
        aspect_ratio = page_height / page_width if page_width != 0 else 1
        final_thumb_width = column_width
        final_thumb_height = int(final_thumb_width * aspect_ratio)
        if final_thumb_width <= 0:
            final_thumb_width = 1
        if final_thumb_height <= 0:
            final_thumb_height = 1

        print(f"final_thumb_width={final_thumb_width}, final_thumb_height={final_thumb_height}")

        mat = fitz.Matrix(self.render_dpi_factor, self.render_dpi_factor)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        img_data = pix.tobytes("ppm")
        image = Image.open(io.BytesIO(img_data))

        print(f"Image.size (oryginalny render): {image.size}")

        resized_image = image.resize((final_thumb_width, final_thumb_height), Image.BILINEAR)
        print(f"Resized image size: {resized_image.size}")

        img_tk = ImageTk.PhotoImage(resized_image)
        
        # Cache the thumbnail for this width
        if page_index not in self.tk_images:
            self.tk_images[page_index] = {}
        self.tk_images[page_index][column_width] = img_tk

        print(f"[CACHE UPDATE] Dodano do cache: strona {page_index}, szerokość {column_width}")

        return img_tk

    def _clear_thumbnail_cache(self, page_index):
        """
        Usuwa cache miniatury dla konkretnej strony.
        """
        if page_index in self.tk_images:
            del self.tk_images[page_index]

    def update_single_thumbnail(self, page_index, column_width=None):
        """
        Odświeża tylko konkretną miniaturę bez przebudowy całej siatki.
        Używane dla operacji, które zmieniają zawartość strony, ale nie liczbę stron.
        
        Args:
            page_index: Indeks strony do odświeżenia
            column_width: Szerokość kolumny (jeśli None, używa bieżącej self.thumb_width)
        """
        if not self.pdf_document or page_index >= len(self.pdf_document):
            return
        
        if page_index not in self.thumb_frames:
            return
        
        # Użyj bieżącej szerokości miniatur, jeśli nie podano
        if column_width is None:
            column_width = self.thumb_width
        
        # Usuń cache dla tej strony
        self._clear_thumbnail_cache(page_index)
        
        # Renderuj nową miniaturę
        img_tk = self._render_and_scale(page_index, column_width)
        
        # Zaktualizuj obraz w istniejącym ThumbnailFrame
        page_frame = self.thumb_frames[page_index]
        if page_frame.img_label:
            page_frame.img_label.config(image=img_tk)
            page_frame.img_label.image = img_tk
        
        # Zaktualizuj etykietę rozmiaru strony (może się zmienić przy kadracji/zmianie rozmiaru)
        outer_frame_children = page_frame.outer_frame.winfo_children()
        if len(outer_frame_children) > 2:
            frame_bg = page_frame.bg_selected if page_index in self.selected_pages else page_frame.bg_normal
            outer_frame_children[2].config(text=self._get_page_size_label(page_index), bg=frame_bg)

    def update_selection_display(self):
        # Clean up selected_pages to remove any invalid indices
        if self.pdf_document:
            valid_indices = set(range(len(self.pdf_document)))
            self.selected_pages = self.selected_pages & valid_indices
        
        num_selected = len(self.selected_pages)
        
        for frame_index, frame in self.thumb_frames.items():
            inner_frame = frame.outer_frame
            if frame_index in self.selected_pages:
                frame.config(bg=frame.bg_selected)  
                for widget in inner_frame.winfo_children():
                    if isinstance(widget, tk.Label) and widget.cget('bg') != 'white':
                         widget.config(bg=frame.bg_selected)
                inner_frame.config(bg=frame.bg_selected)
            else:
                frame.config(bg=frame.bg_normal)
                for widget in inner_frame.winfo_children():
                    if isinstance(widget, tk.Label) and widget.cget('bg') != 'white':
                         widget.config(bg=frame.bg_normal)
                inner_frame.config(bg=frame.bg_normal)

        self.update_tool_button_states()
        
        if self.pdf_document:
             if num_selected > 0:
                 msg = f"Zaznaczono {num_selected} stron. Użyj przycisków w panelu do edycji."
                 if num_selected == 1:
                      page_num = list(self.selected_pages)[0] + 1
                      msg = f"Zaznaczono 1 stronę (Strona {page_num}). Użyj przycisków w panelu do edycji."
                 self._update_status(msg)
             else:
                 self._update_status(f"Dokument wczytany. Liczba stron: {len(self.pdf_document)}. Zaznacz strony (LPM lub Spacja) do edycji.")
        else:
             self._update_status("Gotowy. Otwórz plik PDF.")

    # ===================================================================
    # NOWE FUNKCJE: HASŁA PDF, USUWANIE PUSTYCH STRON, SCALANIE PDF
    # ===================================================================
    
    def _ask_for_password(self):
        """Wyświetla dialog z prośbą o hasło do pliku PDF.
        Zwraca hasło lub None jeśli użytkownik anulował."""
        
        dialog = tk.Toplevel(self.master)
        dialog.title("Plik PDF wymaga hasła")
        dialog.transient(self.master)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        main_frame = ttk.Frame(dialog, padding="12")
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text="Ten plik PDF jest zabezpieczony hasłem.").pack(anchor="w", pady=(0, 8))
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
        parent_x = self.master.winfo_rootx()
        parent_y = self.master.winfo_rooty()
        parent_w = self.master.winfo_width()
        parent_h = self.master.winfo_height()
        x = parent_x + (parent_w - dialog_w) // 2
        y = parent_y + (parent_h - dialog_h) // 2
        dialog.geometry(f"+{x}+{y}")
        
        dialog.wait_window()
        
        return result[0]
    
    def set_pdf_password(self):
        """Ustawia hasło na otwarty plik PDF"""
        if not self.pdf_document:
            custom_messagebox(self.master, "Błąd", "Brak otwartego dokumentu PDF.", typ="error")
            return
            
        # Dialog do wprowadzenia hasła
        dialog = tk.Toplevel(self.master)
        dialog.title("Ustaw hasło PDF")
        dialog.transient(self.master)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        main_frame = ttk.Frame(dialog, padding="12")
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text="Wprowadź hasło:").grid(row=0, column=0, sticky="w", pady=2)
        password_var = tk.StringVar()
        password_entry = ttk.Entry(main_frame, textvariable=password_var, show="*", width=30)
        password_entry.grid(row=0, column=1, sticky="ew", pady=2, padx=(8, 0))
        
        ttk.Label(main_frame, text="Potwierdź hasło:").grid(row=1, column=0, sticky="w", pady=2)
        confirm_var = tk.StringVar()
        confirm_entry = ttk.Entry(main_frame, textvariable=confirm_var, show="*", width=30)
        confirm_entry.grid(row=1, column=1, sticky="ew", pady=2, padx=(8, 0))
        
        result = [None]
        
        def on_ok():
            pwd = password_var.get()
            conf = confirm_var.get()
            if not pwd:
                custom_messagebox(dialog, "Błąd", "Hasło nie może być puste.", typ="error")
                return
            if pwd != conf:
                custom_messagebox(dialog, "Błąd", "Hasła nie są identyczne.", typ="error")
                return
            result[0] = pwd
            dialog.destroy()
            
        def on_cancel():
            dialog.destroy()
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(12, 0))
        ttk.Button(button_frame, text="OK", command=on_ok, width=10).pack(side="left", padx=4)
        ttk.Button(button_frame, text="Anuluj", command=on_cancel, width=10).pack(side="left", padx=4)
        
        password_entry.focus_set()
        dialog.bind("<Return>", lambda e: on_ok())
        dialog.bind("<Escape>", lambda e: on_cancel())
        
        # Wyśrodkuj
        dialog.update_idletasks()
        dialog_w = dialog.winfo_width()
        dialog_h = dialog.winfo_height()
        parent_x = self.master.winfo_rootx()
        parent_y = self.master.winfo_rooty()
        parent_w = self.master.winfo_width()
        parent_h = self.master.winfo_height()
        x = parent_x + (parent_w - dialog_w) // 2
        y = parent_y + (parent_h - dialog_h) // 2
        dialog.geometry(f"+{x}+{y}")
        
        dialog.wait_window()
        
        if result[0]:
            # Zapisz PDF z hasłem używając pypdf
            try:
                filepath = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    filetypes=[("Pliki PDF", "*.pdf")],
                    title="Zapisz PDF z hasłem"
                )
                if not filepath:
                    return
                
                # Konwertuj PyMuPDF do PyPDF
                pdf_bytes = self.pdf_document.tobytes()
                reader = PdfReader(io.BytesIO(pdf_bytes))
                writer = PdfWriter()
                
                for page in reader.pages:
                    writer.add_page(page)
                
                # Ustaw hasło
                writer.encrypt(result[0])
                
                with open(filepath, "wb") as output_file:
                    writer.write(output_file)
                
                custom_messagebox(self.master, "Sukces", f"PDF z hasłem zapisany do:\n{filepath}", typ="info")
                self._update_status(f"Zapisano PDF z hasłem: {filepath}")
            except Exception as e:
                custom_messagebox(self.master, "Błąd", f"Nie udało się zapisać PDF z hasłem:\n{e}", typ="error")
    
    def remove_pdf_password(self):
        """Usuwa hasło z pliku PDF"""
        if not self.pdf_document:
            custom_messagebox(self.master, "Błąd", "Brak otwartego dokumentu PDF.", typ="error")
            return
        
        # Jeśli dokument jest już otwarty, to hasło zostało już podane przy otwarciu
        # Zapisujemy go bez hasła
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Pliki PDF", "*.pdf")],
            title="Zapisz PDF bez hasła"
        )
        if not filepath:
            return
        
        try:
            # Zapisz aktualny dokument bez hasła
            self.pdf_document.save(filepath)
            custom_messagebox(self.master, "Sukces", f"PDF bez hasła zapisany do:\n{filepath}", typ="info")
            self._update_status(f"Zapisano PDF bez hasła: {filepath}")
        except Exception as e:
            custom_messagebox(self.master, "Błąd", f"Nie udało się zapisać PDF bez hasła:\n{e}", typ="error")
    
    def remove_empty_pages(self):
        """Usuwa puste strony z dokumentu PDF"""
        if not self.pdf_document:
            custom_messagebox(self.master, "Błąd", "Brak otwartego dokumentu PDF.", typ="error")
            return
        
        answer = custom_messagebox(
            self.master,
            "Potwierdzenie",
            "Czy usunąć wszystkie puste strony?\n(Pusta strona = brak tekstu i białe tło)",
            typ="question"
        )
        
        if not answer:
            return
        
        try:
            self._save_state_to_undo()
            
            # Deleguj wykrywanie do PDFTools
            def progress_callback(current, total):
                if current == 0:
                    self.show_progressbar(maximum=total)
                self.update_progressbar(current)
                if current == total:
                    self.hide_progressbar()
            
            empty_pages = self.pdf_tools.detect_empty_pages(
                self.pdf_document,
                progress_callback=self._update_status,
                progressbar_callback=progress_callback
            )
            
            if not empty_pages:
                self.hide_progressbar()
                custom_messagebox(self.master, "Informacja", "Nie znaleziono pustych stron w dokumencie.", typ="info")
                return
            
            # Deleguj usuwanie do PDFTools
            deleted_count = self.pdf_tools.remove_empty_pages(
                self.pdf_document,
                empty_pages,
                progress_callback=self._update_status,
                progressbar_callback=progress_callback
            )
            
            # Odśwież widok
            self.selected_pages.clear()
            self.tk_images.clear()
            self.thumb_frames.clear()
            for widget in list(self.scrollable_frame.winfo_children()):
                widget.destroy()
            
            self.active_page_index = 0
            self._reconfigure_grid()
            self.update_tool_button_states()
            self.update_focus_display()
            
            self.hide_progressbar()
            
            self._update_status(f"Usunięto {deleted_count} pustych stron. Odswieżanie miniatur...")
        except Exception as e:
            self.hide_progressbar()
            custom_messagebox(self.master, "Błąd", f"Nie udało się usunąć pustych stron:\n{e}", typ="error")
    
    def merge_pdf_files(self):
        """Otwiera okno dialogowe do scalania plików PDF"""
        MergePDFDialog(self.master)
    
    # ===================================================================
    # FUNKCJE MAKR
    # ===================================================================
    
    def _init_macro_system(self):
        """Inicjalizuje system makr"""
        self.macro_manager = MacroManager(self.prefs_manager)
        self.macros_list_dialog = None  # Track the MacrosListDialog instance
        self.pdf_analysis_dialog = None  # Track the PDFAnalysisDialog instance
    

    def record_macro(self):
        """Opens non-blocking macro recording dialog"""
        MacroRecordingDialog(self.master, self)
    
    def _record_action(self, action_name, **kwargs):
        """Nagrywa akcję do bieżącego makra"""
        self.macro_manager.record_action(action_name, **kwargs)
    
    def show_macros_list(self):
        """Wyświetla listę makr użytkownika"""
        # Jeśli okno już istnieje, sprowadź je na wierzch
        if self.macros_list_dialog and self.macros_list_dialog.winfo_exists():
            self.macros_list_dialog.lift()
            self.macros_list_dialog.focus_force()
        else:
            # Utwórz nowe okno i zapisz referencję
            self.macros_list_dialog = MacrosListDialog(self.master, self.prefs_manager, self)
    
    def show_pdf_analysis(self):
        """Wyświetla okno analizy PDF"""
        # Jeśli okno już istnieje, sprowadź je na wierzch
        if hasattr(self, 'pdf_analysis_dialog') and self.pdf_analysis_dialog and self.pdf_analysis_dialog.winfo_exists():
            self.pdf_analysis_dialog.lift()
            self.pdf_analysis_dialog.focus_force()
        else:
            # Utwórz nowe okno i zapisz referencję
            self.pdf_analysis_dialog = PDFAnalysisDialog(self.master, self)
    
    def run_macro(self, macro_name):
        """Uruchamia makro o podanej nazwie"""
        macro = self.macro_manager.get_macro(macro_name)
        if not macro:
            custom_messagebox(self.master, "Błąd", f"Makro '{macro_name}' nie istnieje.", typ="error")
            return
        
        actions = macro.get('actions', [])
        
        if not actions:
            custom_messagebox(self.master, "Informacja", "Makro nie zawiera żadnych akcji.", typ="info")
            return
        
        # Wyłącz nagrywanie podczas wykonywania makra
        was_recording = self.macro_manager.is_recording()
        if was_recording:
            self.macro_manager.recording = False
        
        try:
            for action_data in actions:
                action = action_data.get('action')
                params = action_data.get('params', {})
                
                # Mapowanie akcji na metody - simple actions without params
                if action == 'rotate_left':
                    self.rotate_selected_page(-90)
                elif action == 'rotate_right':
                    self.rotate_selected_page(90)
                elif action == 'select_all':
                    self._select_all()
                elif action == 'select_odd':
                    self._select_odd_pages()
                elif action == 'select_even':
                    self._select_even_pages()
                elif action == 'select_portrait':
                    self._select_portrait_pages()
                elif action == 'select_landscape':
                    self._select_landscape_pages()
                elif action == 'select_custom' and params:
                    indices = params.get('indices', [])
                    if isinstance(indices, int):
                        indices = [indices]
                    source_page_count = params.get('source_page_count', None)
                    self._apply_selection_by_indices(indices, macro_source_page_count=source_page_count)
                # Parameterized actions - replay with saved parameters
                elif action == 'shift_page_content' and params:
                    self._replay_shift_page_content(params)
                elif action == 'insert_page_numbers' and params:
                    self._replay_insert_page_numbers(params)
                elif action == 'remove_page_numbers' and params:
                    self._replay_remove_page_numbers(params)
                elif action == 'apply_page_crop_resize' and params:
                    self._replay_apply_page_crop_resize(params)
            
            self._update_status(f"Wykonano makro '{macro_name}' ({len(actions)} akcji).")
        except Exception as e:
            custom_messagebox(self.master, "Błąd", f"Błąd podczas wykonywania makra:\n{e}", typ="error")
        finally:
            if was_recording:
                self.macro_manager.recording = True
    
    def _replay_shift_page_content(self, params):
        """Replay shift_page_content with saved parameters (zgodnie z aktualną wersją GUI)"""
        if not self.pdf_document or not self.selected_pages:
            return

        dx_pt = params['x_mm'] * self.MM_TO_POINTS
        dy_pt = params['y_mm'] * self.MM_TO_POINTS
        x_sign = 1 if params['x_dir'] == 'P' else -1
        y_sign = 1 if params['y_dir'] == 'G' else -1
        final_dx = dx_pt * x_sign
        final_dy = dy_pt * y_sign

        try:
            self._save_state_to_undo()
            pages_to_shift = sorted(list(self.selected_pages))
            pages_to_shift_set = set(pages_to_shift)
            total_pages = len(self.pdf_document)

            # 1. Oczyszczanie przez PyMuPDF
            import io
            import fitz
            from pypdf import PdfReader, PdfWriter, Transformation

            original_pdf_bytes = self.pdf_document.tobytes()
            pymupdf_doc = fitz.open("pdf", original_pdf_bytes)
            cleaned_doc = fitz.open()
            for idx in range(len(pymupdf_doc)):
                if idx in pages_to_shift_set:
                    temp = fitz.open()
                    temp.insert_pdf(pymupdf_doc, from_page=idx, to_page=idx)
                    cleaned_doc.insert_pdf(temp)
                    temp.close()
                else:
                    cleaned_doc.insert_pdf(pymupdf_doc, from_page=idx, to_page=idx)
            cleaned_pdf_bytes = cleaned_doc.write()
            pymupdf_doc.close()
            cleaned_doc.close()

            # 2. Przesuwanie przez PyPDF
            pdf_reader = PdfReader(io.BytesIO(cleaned_pdf_bytes))
            pdf_writer = PdfWriter()
            transform = Transformation().translate(tx=final_dx, ty=final_dy)

            for i, page in enumerate(pdf_reader.pages):
                if i in pages_to_shift_set:
                    page.add_transformation(transform)
                pdf_writer.add_page(page)

            new_pdf_stream = io.BytesIO()
            pdf_writer.write(new_pdf_stream)
            new_pdf_bytes = new_pdf_stream.getvalue()

            # 3. Aktualizacja dokumentu w aplikacji przez PyMuPDF
            if self.pdf_document:
                self.pdf_document.close()
            self.pdf_document = fitz.open("pdf", new_pdf_bytes)
            
            # Optymalizacja: odśwież tylko zmienione miniatury
            self.show_progressbar(maximum=len(pages_to_shift))
            for i, page_index in enumerate(pages_to_shift):
                self._update_status("Makro: Przesunięto zawartość stron zgodnie z parametrami. Odświeżanie miniatur...")
                
                self.update_single_thumbnail(page_index)
                self.update_progressbar(i + 1)
            self.hide_progressbar()
            
            self._update_status("Makro: Przesunięto zawartość stron zgodnie z parametrami.")
        except Exception as e:
            self._update_status(f"BŁĄD podczas odtwarzania shift_page_content: {e}")
    
    def _replay_insert_page_numbers(self, params):
        """Replay insert_page_numbers with saved parameters"""
        if not self.pdf_document or not self.selected_pages:
            self._update_status("Makro: Brak zaznaczonych stron dla numeracji.")
            return
        
        doc = self.pdf_document
        MM_PT = self.MM_TO_POINTS
        
        try:
            self._save_state_to_undo()
            
            # Extract parameters
            start_number = params.get('start_num', 1)
            mode = params.get('mode', 'zwykla')
            direction = params.get('alignment', 'prawa')
            position = params.get('vertical_pos', 'dol')
            mirror_margins = params.get('mirror_margins', False)
            format_mode = params.get('format_type', 'simple')
            left_mm = params.get('margin_left_mm', 10)
            right_mm = params.get('margin_right_mm', 10)
            margin_v_mm = params.get('margin_vertical_mm', 10)
            font_size = params.get('font_size', 10)
            font = params.get('font_name', 'helv')
            
            left_pt_base = left_mm * MM_PT
            right_pt_base = right_mm * MM_PT
            margin_v = margin_v_mm * MM_PT
            
            selected_indices = sorted(self.selected_pages)
            current_number = start_number
            total_counted_pages = len(selected_indices) + start_number - 1
            
            for i in selected_indices:
                page = doc.load_page(i)
                rect = page.rect
                rotation = page.rotation
                
                # Create numbering text
                if format_mode == 'full':
                    text = f"Strona {current_number} z {total_counted_pages}"
                else:
                    text = str(current_number)
                
                text_width = fitz.get_text_length(text, fontname=font, fontsize=font_size)
                
                # Determine alignment
                is_even_counted_page = (current_number - start_number) % 2 == 0
                
                if mode == "lustrzana":
                    if direction == "srodek":
                        align = "srodek"
                    elif direction == "lewa":
                        align = "lewa" if is_even_counted_page else "prawa"
                    else:
                        align = "prawa" if is_even_counted_page else "lewa"
                else:
                    align = direction
                
                # Mirror margins for physical pages
                is_physical_odd = (i + 1) % 2 == 1
                
                if mirror_margins:
                    if is_physical_odd:
                        left_pt, right_pt = left_pt_base, right_pt_base
                    else:
                        left_pt, right_pt = right_pt_base, left_pt_base
                else:
                    left_pt, right_pt = left_pt_base, right_pt_base
                
                # Calculate position based on rotation
                if rotation == 0:
                    if align == "lewa":
                        x = rect.x0 + left_pt
                    elif align == "prawa":
                        x = rect.x1 - right_pt - text_width
                    else:  # srodek
                        total_width = rect.width
                        margin_diff = left_pt - right_pt
                        x = rect.x0 + (total_width / 2) - (text_width / 2) + (margin_diff / 2)
                    y = rect.y0 + margin_v + font_size if position == "gora" else rect.y1 - margin_v
                    angle = 0
                elif rotation == 90:
                    if align == "lewa":
                        y = rect.y0 + left_pt
                    elif align == "prawa":
                        y = rect.y1 - right_pt - text_width
                    else:
                        total_height = rect.height
                        margin_diff = left_pt - right_pt
                        y = rect.y0 + (total_height / 2) - (text_width / 2) + (margin_diff / 2)
                    x = rect.x0 + margin_v + font_size if position == "gora" else rect.x1 - margin_v
                    angle = 90
                elif rotation == 180:
                    if align == "lewa":
                        x = rect.x1 - right_pt - text_width
                    elif align == "prawa":
                        x = rect.x0 + left_pt
                    else:
                        total_width = rect.width
                        margin_diff = left_pt - right_pt
                        x = rect.x0 + (total_width / 2) - (text_width / 2) + (margin_diff / 2)
                    y = rect.y1 - margin_v - font_size if position == "gora" else rect.y0 + margin_v
                    angle = 180
                elif rotation == 270:
                    if align == "lewa":
                        y = rect.y1 - right_pt - text_width
                    elif align == "prawa":
                        y = rect.y0 + left_pt
                    else:
                        total_height = rect.height
                        margin_diff = left_pt - right_pt
                        y = rect.y0 + (total_height / 2) - (text_width / 2) + (margin_diff / 2)
                    x = rect.x1 - margin_v - font_size if position == "gora" else rect.x0 + margin_v
                    angle = 270
                else:
                    x = rect.x0 + left_pt
                    y = rect.y1 - margin_v
                    angle = 0
                
                page.insert_text(
                    fitz.Point(x, y),
                    text,
                    fontsize=font_size,
                    fontname=font,
                    color=(0, 0, 0),
                    rotate=angle
                )
                
                current_number += 1
            
            # Optymalizacja: odśwież tylko zmienione miniatury
            self.show_progressbar(maximum=len(selected_indices))
            for i, page_index in enumerate(selected_indices):
                self._update_status(f"Makro: Numeracja wstawiona na {len(selected_indices)} stronach. Odświeżanie miniatur...")
              
                self.update_single_thumbnail(page_index)
                self.update_progressbar(i + 1)
            self.hide_progressbar()
            
            self._update_status(f"Makro: Numeracja wstawiona na {len(selected_indices)} stronach.")
            
        except Exception as e:
            self._update_status(f"Makro: Błąd przy dodawaniu numeracji: {e}")
    
    def _replay_remove_page_numbers(self, params):
        """Replay remove_page_numbers with saved parameters"""
        if not self.pdf_document or not self.selected_pages:
            self._update_status("Makro: Brak zaznaczonych stron do usunięcia numeracji.")
            return
        
        top_mm = params.get('top_mm', 20)
        bottom_mm = params.get('bottom_mm', 20)
        
        mm_to_points = self.MM_TO_POINTS
        top_pt = top_mm * mm_to_points
        bottom_pt = bottom_mm * mm_to_points
        
        page_number_patterns = [
            r'^\s*[-–]?\s*\d+\s*[-–]?\s*$',
            r'^\s*(?:Strona|Page)\s+\d+\s+(?:z|of)\s+\d+\s*$',
            r'^\s*\d+\s*(?:/|-|\s+)\s*\d+\s*$',
            r'^\s*\(\s*\d+\s*\)\s*$'
        ]
        compiled_patterns = [re.compile(p, re.IGNORECASE) for p in page_number_patterns]
        
        try:
            pages_to_process = sorted(list(self.selected_pages))
            if pages_to_process:
                self._save_state_to_undo()
            modified_count = 0
            
            for page_index in pages_to_process:
                page = self.pdf_document.load_page(page_index)
                rect = page.rect
                
                top_margin_rect = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y0 + top_pt)
                bottom_margin_rect = fitz.Rect(rect.x0, rect.y1 - bottom_pt, rect.x1, rect.y1)
                scan_rects = [top_margin_rect, bottom_margin_rect]
                
                found_and_removed = False
                
                for scan_rect in scan_rects:
                    text_blocks = page.get_text("blocks", clip=scan_rect)
                    
                    for block in text_blocks:
                        block_text = block[4]
                        lines = block_text.strip().split('\n')
                        
                        for line in lines:
                            cleaned_line = line.strip()
                            for pattern in compiled_patterns:
                                if pattern.fullmatch(cleaned_line):
                                    text_instances = page.search_for(cleaned_line, clip=scan_rect)
                                    
                                    for inst in text_instances:
                                        page.add_redact_annot(inst)
                                        found_and_removed = True
                
                if found_and_removed:
                    page.apply_redactions()
                    modified_count += 1
            
            if modified_count > 0:
                # Optymalizacja: odśwież tylko zmienione miniatury
                self.show_progressbar(maximum=len(pages_to_process))
                for i, page_index in enumerate(pages_to_process):
                    self._update_status(f"Makro: Usunięto numery stron na {modified_count} stronach. Odświeżanie miniatur...")

                    self.update_single_thumbnail(page_index)
                    self.update_progressbar(i + 1)
                self.hide_progressbar()
                
                self._update_status(f"Makro: Usunięto numery stron na {modified_count} stronach.")
            else:
                self._update_status("Makro: Nie znaleziono numerów stron do usunięcia.")
                
        except Exception as e:
            self._update_status(f"Makro: Błąd przy usuwaniu numeracji: {e}")
    
    def _replay_apply_page_crop_resize(self, params):
        """Replay apply_page_crop_resize with saved parameters"""
        if not self.pdf_document or not self.selected_pages:
            self._update_status("Makro: Brak zaznaczonych stron do kadrowania/zmiany rozmiaru.")
            return
        
        try:
            pdf_bytes_export = io.BytesIO()
            self.pdf_document.save(pdf_bytes_export)
            pdf_bytes_export.seek(0)
            pdf_bytes_val = pdf_bytes_export.read()
            indices = sorted(list(self.selected_pages))
            
            crop_mode = params.get("crop_mode", "nocrop")
            resize_mode = params.get("resize_mode", "noresize")
            
            if crop_mode == "crop_only" and resize_mode == "noresize":
                new_pdf_bytes = self._mask_crop_pages(
                    pdf_bytes_val, indices,
                    params.get("crop_top_mm", 0), params.get("crop_bottom_mm", 0),
                    params.get("crop_left_mm", 0), params.get("crop_right_mm", 0),
                )
                msg = "Makro: Dodano białe maski."
            elif crop_mode == "crop_resize" and resize_mode == "noresize":
                new_pdf_bytes = self._crop_pages(
                    pdf_bytes_val, indices,
                    params.get("crop_top_mm", 0), params.get("crop_bottom_mm", 0),
                    params.get("crop_left_mm", 0), params.get("crop_right_mm", 0),
                    reposition=False
                )
                msg = "Makro: Zastosowano przycięcie."
            elif resize_mode == "resize_scale":
                new_pdf_bytes = self._resize_scale(
                    pdf_bytes_val, indices,
                    params.get("target_width_mm", 210), params.get("target_height_mm", 297)
                )
                msg = "Makro: Zmieniono rozmiar ze skalowaniem."
            elif resize_mode == "resize_noscale":
                new_pdf_bytes = self._resize_noscale(
                    pdf_bytes_val, indices,
                    params.get("target_width_mm", 210), params.get("target_height_mm", 297),
                    pos_mode=params.get("position_mode", "center"),
                    offset_x_mm=params.get("offset_x_mm", 0),
                    offset_y_mm=params.get("offset_y_mm", 0),
                )
                msg = "Makro: Zmieniono rozmiar bez skalowania."
            else:
                self._update_status("Makro: Brak operacji do wykonania.")
                return
            
            self._save_state_to_undo()
            self.pdf_document.close()
            self.pdf_document = fitz.open("pdf", new_pdf_bytes)
            self._update_status(msg)
            
            # Optymalizacja: odśwież tylko zmienione miniatury
            self.show_progressbar(maximum=len(indices))
            for i, page_index in enumerate(indices):
                self._update_status("Operacja zakończona. Odświeżanie miniatur...")
                self.update_single_thumbnail(page_index)
                self.update_progressbar(i + 1)
            self.hide_progressbar()
            
            if hasattr(self, "update_selection_display"):
                self.update_selection_display()
            if hasattr(self, "update_focus_display"):
                self.update_focus_display()
                
        except Exception as e:
            self._update_status(f"Makro: Błąd podczas przetwarzania PDF: {e}")

    def update_focus_display(self, hide_mouse_focus: bool = False):
        if not self.pdf_document: return
        for index, frame in self.thumb_frames.items():
            inner_frame = frame.outer_frame
            if index == self.active_page_index and not hide_mouse_focus:
                inner_frame.config(highlightbackground=FOCUS_HIGHLIGHT_COLOR, highlightcolor=FOCUS_HIGHLIGHT_COLOR)
            else:
                inner_frame.config(highlightbackground=frame.bg_normal, highlightcolor=frame.bg_normal)

if __name__ == '__main__':
    try:
        from tkinterdnd2 import TkinterDnD
        root = TkinterDnD.Tk()
        from PIL import Image, ImageTk
        icon_path = resource_path(os.path.join('icons', 'gryf.ico'))  # lub .ico jeśli masz na Windows
        icon_img = Image.open(icon_path).resize((32, 32), Image.LANCZOS)
        icon_tk = ImageTk.PhotoImage(icon_img)
        root.iconphoto(True, icon_tk)
        app = SelectablePDFViewer(root)
        root.mainloop()
    except ImportError as e:
        print(f"BŁĄD: Wymagane biblioteki nie są zainstalowane. Upewnij się, że masz PyMuPDF (pip install PyMuPDF) i Pillow (pip install Pillow). Szczegóły: {e}")
        sys.exit(1)