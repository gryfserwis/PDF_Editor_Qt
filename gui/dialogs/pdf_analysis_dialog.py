import tkinter as tk
from tkinter import ttk
import fitz
from datetime import datetime

from utils import custom_messagebox, PROGRAM_TITLE, COPYRIGHT_INFO


class PDFAnalysisDialog(tk.Toplevel):
    """Okno analizy PDF - zlicza strony wg kolorystyki, formatu i orientacji"""
    
    # Formaty stron (w mm) z tolerancją ±5mm
    FORMATS = {
        'A0': (841, 1189),
        'A1': (594, 841),
        'A2': (420, 594),
        'A3': (297, 420),
        'A4': (210, 297),
        'Letter': (216, 279),
    }
    
    def __init__(self, parent, viewer):
        super().__init__(parent)
        self.parent = parent
        self.viewer = viewer
        self.prefs_manager = viewer.prefs_manager
        self.title("Analiza PDF")
        self.transient(parent)
        # Don't grab_set() - we want non-blocking dialog
        self.resizable(True, True)
        self.geometry("300x400")
        self.minsize(300, 400)
        
        self.analysis_results = {}
        self.result_buttons = []  # Store references to result buttons
        
        self.build_ui()
        self.position_below_macros(parent)
        self.protocol("WM_DELETE_WINDOW", self.close)
        
        # Auto-analyze on open
        self.after(100, self.analyze_pdf)
    
    def position_below_macros(self, parent):
        """Ustaw okno pod oknem makr (jeśli istnieje) lub obok głównego okna"""
        self.update_idletasks()
        dialog_w = self.winfo_width()
        dialog_h = self.winfo_height()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        
        # Check if macros window exists and is visible
        if hasattr(self.viewer, 'macros_list_dialog') and self.viewer.macros_list_dialog and self.viewer.macros_list_dialog.winfo_exists():
            macros_window = self.viewer.macros_list_dialog
            macros_x = macros_window.winfo_rootx()
            macros_y = macros_window.winfo_rooty()
            macros_h = macros_window.winfo_height()
            # Position below macros window
            x = macros_x
            y = macros_y + macros_h + 10
        else:
            # Position to the right of main window (same as macros default)
            x = parent_x + parent_w + 30
            y = parent_y
            # If doesn't fit on screen, move to left
            screen_w = self.winfo_screenwidth()
            if x + dialog_w > screen_w:
                x = max(0, parent_x - dialog_w - 30)
        
        self.geometry(f"+{x}+{y}")
    
    def build_ui(self):
        main_frame = ttk.Frame(self, padding="12")
        main_frame.pack(fill="both", expand=True)
        
        # Button to manually trigger analysis
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(0, 8))
        ttk.Button(button_frame, text="Analizuj PDF", command=self.analyze_pdf, width=15).pack()
        
        # Results area with scrollbar
        results_frame = ttk.LabelFrame(main_frame, text="Wyniki analizy")
        results_frame.pack(fill="both", expand=True, pady=(0, 8))
        
        # Create scrollable canvas
        canvas = tk.Canvas(results_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=canvas.yview)
        self.results_container = ttk.Frame(canvas)
        
        self.results_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.results_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.canvas = canvas
        
        # Close button
        ttk.Button(main_frame, text="Zamknij", command=self.close, width=15).pack()
    
    def analyze_pdf(self):
        """Analizuje PDF i wyświetla wyniki"""
        if not self.viewer.pdf_document:
            self._show_message("Brak otwartego dokumentu PDF.")
            return
        
        # Clear previous results
        for widget in self.results_container.winfo_children():
            widget.destroy()
        self.result_buttons.clear()
        self.analysis_results.clear()
        
        doc = self.viewer.pdf_document
        total_pages = len(doc)
        
        if total_pages == 0:
            self._show_message("Dokument nie zawiera stron.")
            return
        
        # Show progress message
        progress_label = ttk.Label(self.results_container, text="Analizowanie...")
        progress_label.pack(pady=10)
        self.update()
        
        # Analyze each page
        for page_idx in range(total_pages):
            page = doc[page_idx]
            
            # Detect color
            is_color = self._detect_color(page)
            color_type = "Kolor" if is_color else "Czarno-biały"
            
            # Detect format
            page_format = self._detect_format(page)
            
            # Detect orientation
            is_landscape = self._is_landscape(page)
            
            # Create key for grouping
            key = f"{color_type}_{page_format}"
            if not key in self.analysis_results:
                self.analysis_results[key] = {
                    'color': color_type,
                    'format': page_format,
                    'pages': [],
                    'landscape_count': 0
                }
            
            self.analysis_results[key]['pages'].append(page_idx)
            if is_landscape:
                self.analysis_results[key]['landscape_count'] += 1
        
        # Remove progress label
        progress_label.destroy()
        
        # Display results
        self._display_results()
    
    def _detect_color(self, page):
        """Wykrywa czy strona jest kolorowa czy czarno-biała"""
        try:
            # Get settings from preferences
            render_scale = float(self.prefs_manager.get('color_detect_scale', '0.2'))
            max_samples = int(self.prefs_manager.get('color_detect_samples', '300'))
            threshold = int(self.prefs_manager.get('color_detect_threshold', '5'))
            
            # Render page at configured resolution
            mat = fitz.Matrix(render_scale, render_scale)
            pix = page.get_pixmap(matrix=mat, alpha=False, colorspace=fitz.csGRAY)
            
            # Get another pixmap in RGB
            pix_rgb = page.get_pixmap(matrix=mat, alpha=False, colorspace=fitz.csRGB)
            
            # Sample pixels - check if RGB differs from grayscale
            samples = min(max_samples, pix.width * pix.height)
            step = max(1, (pix.width * pix.height) // samples)
            
            for i in range(0, pix.width * pix.height, step):
                y = i // pix.width
                x = i % pix.width
                if x >= pix.width or y >= pix.height:
                    continue
                
                # Get RGB pixel
                offset = (y * pix_rgb.width + x) * 3
                if offset + 2 >= len(pix_rgb.samples):
                    continue
                
                r = pix_rgb.samples[offset]
                g = pix_rgb.samples[offset + 1]
                b = pix_rgb.samples[offset + 2]
                
                # If R, G, B are different by more than threshold, it's color
                if abs(r - g) > threshold or abs(g - b) > threshold or abs(r - b) > threshold:
                    return True
            
            return False
        except:
            # If error, assume grayscale
            return False
    
    def _detect_format(self, page):
        """Wykrywa format strony (A4, A3, itp.)"""
        rect = page.rect
        width_pt = rect.width
        height_pt = rect.height
        
        # Convert to mm
        width_mm = round(width_pt / 72 * 25.4)
        height_mm = round(height_pt / 72 * 25.4)
        
        # Check known formats with tolerance
        tol = 5
        for name, (fw, fh) in self.FORMATS.items():
            if (abs(width_mm - fw) <= tol and abs(height_mm - fh) <= tol) or \
               (abs(width_mm - fh) <= tol and abs(height_mm - fw) <= tol):
                return name
        
        return "Niestandardowy"
    
    def _is_landscape(self, page):
        """Sprawdza czy strona jest w orientacji poziomej"""
        rect = page.rect
        return rect.width > rect.height
    
    def _display_results(self):
        """Wyświetla wyniki analizy jako klikalne przyciski"""
        if not self.analysis_results:
            self._show_message("Brak danych do wyświetlenia.")
            return
        
        # Group by format and color
        color_format_groups = {}
        for key, data in self.analysis_results.items():
            color = data['color']
            page_format = data['format']
            
            if color not in color_format_groups:
                color_format_groups[color] = {}
            if page_format not in color_format_groups[color]:
                color_format_groups[color][page_format] = []
            
            color_format_groups[color][page_format].append(data)
        
        # Display grouped results
        row = 0
        for color in sorted(color_format_groups.keys()):
            # Color header
            color_label = ttk.Label(self.results_container, text=f"{color}", font=("Arial", 10, "bold"))
            color_label.grid(row=row, column=0, columnspan=2, sticky="w", pady=(5, 2))
            row += 1
            
            for page_format in sorted(color_format_groups[color].keys()):
                for data in color_format_groups[color][page_format]:
                    pages = data['pages']
                    landscape_count = data['landscape_count']
                    
                    # Create clickable button
                    text = f"{page_format}: {len(pages)} str."
                    if page_format in ['A4', 'Letter'] and landscape_count > 0:
                        text += f" (poziomych: {landscape_count})"
                    
                    btn = tk.Button(
                        self.results_container,
                        text=text,
                        anchor="w",
                        relief="flat",
                        bg="#f0f0f0",
                        fg="#0066cc",
                        cursor="hand2",
                        command=lambda p=pages: self._select_pages(p)
                    )
                    btn.grid(row=row, column=0, sticky="ew", padx=(10, 5), pady=1)
                    self.result_buttons.append(btn)
                    
                    row += 1
        
        # Configure grid
        self.results_container.columnconfigure(0, weight=1)
    
    def _show_message(self, message):
        """Wyświetla komunikat w obszarze wyników"""
        label = ttk.Label(self.results_container, text=message)
        label.pack(pady=20)
    
    def _select_pages(self, page_indices):
        """Zaznacza strony w głównym oknie programu"""
        if not self.viewer.pdf_document:
            return
        
        # Clear current selection
        self.viewer.selected_pages.clear()
        
        # Add pages to selection
        for idx in page_indices:
            if 0 <= idx < len(self.viewer.pdf_document):
                self.viewer.selected_pages.add(idx)
        
        # Update display
        self.viewer.update_selection_display()
        
        # Set focus to first selected page
        if page_indices:
            self.viewer.active_page_index = min(page_indices)
            self.viewer.update_focus_display()
            
            # Scroll to first selected page
            if self.viewer.active_page_index in self.viewer.thumb_frames:
                frame = self.viewer.thumb_frames[self.viewer.active_page_index]
                self.viewer.canvas.yview_moveto(0)  # Reset scroll first
                frame.update_idletasks()
                # Calculate position
                frame_y = frame.winfo_y()
                canvas_height = self.viewer.canvas.winfo_height()
                scroll_region = self.viewer.canvas.cget("scrollregion")
                if scroll_region:
                    _, _, _, max_y = map(int, scroll_region.split())
                    if max_y > 0:
                        fraction = frame_y / max_y
                        self.viewer.canvas.yview_moveto(max(0, fraction - 0.1))
    
    def close(self):
        """Zamknij okno"""
        self.destroy()


# ====================================================================
# GŁÓWNA KLASA PROGRAMU: SELECTABLEPDFVIEWER
# ====================================================================

