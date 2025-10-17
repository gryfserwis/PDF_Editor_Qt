#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GRYF PDF Viewer - Qt Edition
Simplified PDF viewer using PySide6 for viewing PDF documents.
Based on the original Tkinter PDFEditor but focused on viewing only.
"""

import sys
import os
import io
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QScrollArea, QGridLayout, 
    QLabel, QFileDialog, QStatusBar, QToolBar, QFrame, QVBoxLayout,
    QSizePolicy
)
from PySide6.QtCore import Qt, QSize, Signal, QTimer
from PySide6.QtGui import QPixmap, QImage, QAction, QIcon

import fitz  # PyMuPDF
from PIL import Image

# === CONSTANTS ===
PROGRAM_TITLE = "GRYF PDF Viewer (Qt)"
PROGRAM_VERSION = "1.0.0"

# Colors matching the original Tkinter app
BG_PRIMARY = '#F0F0F0'
BG_SECONDARY = '#E0E0E0'
BG_FRAME = '#F5F5F5'
FG_TEXT = '#444444'

# Thumbnail settings
DEFAULT_THUMB_WIDTH = 200
MIN_THUMB_WIDTH = 100
MAX_THUMB_WIDTH = 400
THUMB_PADDING = 10
MIN_COLS = 1
MAX_COLS = 20

# Rendering quality
RENDER_DPI_FACTOR = 1.5  # Higher = better quality but slower


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


class ThumbnailWidget(QFrame):
    """Widget displaying a single PDF page thumbnail"""
    
    def __init__(self, page_index: int, parent=None):
        super().__init__(parent)
        self.page_index = page_index
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet(f"background-color: {BG_FRAME}; border: 1px solid #D0D0D0;")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(4)
        
        # Page number label
        self.page_label = QLabel(f"Strona {page_index + 1}")
        self.page_label.setAlignment(Qt.AlignCenter)
        self.page_label.setStyleSheet(f"color: {FG_TEXT}; font-weight: bold; background: transparent; border: none;")
        layout.addWidget(self.page_label)
        
        # Image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background: white; border: 1px solid #C0C0C0;")
        layout.addWidget(self.image_label)
        
        # Size label
        self.size_label = QLabel("")
        self.size_label.setAlignment(Qt.AlignCenter)
        self.size_label.setStyleSheet(f"color: gray; font-size: 9pt; background: transparent; border: none;")
        layout.addWidget(self.size_label)
        
        self.setLayout(layout)
    
    def set_thumbnail(self, pixmap: QPixmap, size_text: str):
        """Set the thumbnail image and size text"""
        self.image_label.setPixmap(pixmap)
        self.size_label.setText(size_text)


class PDFViewerWidget(QWidget):
    """Main PDF viewer widget with grid of thumbnails"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pdf_document: Optional[fitz.Document] = None
        self.thumbnail_widgets = []
        self.thumb_width = DEFAULT_THUMB_WIDTH
        self.current_cols = MIN_COLS
        
        # Setup UI
        self.setup_ui()
        
        # Timer for debouncing resize events
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.reconfigure_grid)
    
    def setup_ui(self):
        """Setup the scrollable grid layout"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"background-color: {BG_PRIMARY};")
        
        # Container widget for grid
        self.container = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(THUMB_PADDING)
        self.grid_layout.setContentsMargins(THUMB_PADDING, THUMB_PADDING, THUMB_PADDING, THUMB_PADDING)
        self.container.setLayout(self.grid_layout)
        
        self.scroll_area.setWidget(self.container)
        main_layout.addWidget(self.scroll_area)
        
        self.setLayout(main_layout)
    
    def load_pdf(self, filepath: str):
        """Load a PDF file"""
        try:
            # Try to open with password support
            doc = fitz.open(filepath)
            
            # Check if password protected
            if doc.needs_pass:
                # For now, just show error - password support can be added later
                raise Exception("Plik PDF jest zabezpieczony hasłem. Funkcja nie jest jeszcze obsługiwana.")
            
            self.pdf_document = doc
            self.render_thumbnails()
            return True
        except Exception as e:
            self.pdf_document = None
            raise e
    
    def close_pdf(self):
        """Close the current PDF document"""
        if self.pdf_document:
            self.pdf_document.close()
            self.pdf_document = None
        
        # Clear thumbnails
        self.clear_thumbnails()
    
    def clear_thumbnails(self):
        """Remove all thumbnail widgets"""
        for widget in self.thumbnail_widgets:
            widget.deleteLater()
        self.thumbnail_widgets.clear()
        
        # Clear grid layout
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def render_thumbnails(self):
        """Render all PDF pages as thumbnails"""
        if not self.pdf_document:
            return
        
        self.clear_thumbnails()
        
        page_count = len(self.pdf_document)
        
        # Calculate number of columns
        self.calculate_columns()
        
        # Create thumbnail for each page
        for page_index in range(page_count):
            thumbnail = ThumbnailWidget(page_index)
            
            # Render page
            pixmap, size_text = self.render_page(page_index, self.thumb_width)
            thumbnail.set_thumbnail(pixmap, size_text)
            
            # Add to grid
            row = page_index // self.current_cols
            col = page_index % self.current_cols
            self.grid_layout.addWidget(thumbnail, row, col)
            
            self.thumbnail_widgets.append(thumbnail)
    
    def render_page(self, page_index: int, width: int) -> tuple:
        """Render a single page to QPixmap"""
        page = self.pdf_document.load_page(page_index)
        
        # Get page dimensions
        page_rect = page.rect
        page_width = page_rect.width
        page_height = page_rect.height
        
        # Calculate size
        aspect_ratio = page_height / page_width if page_width != 0 else 1
        final_width = width
        final_height = int(final_width * aspect_ratio)
        
        # Render at higher resolution
        mat = fitz.Matrix(RENDER_DPI_FACTOR, RENDER_DPI_FACTOR)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        # Convert to PIL Image
        img_data = pix.tobytes("ppm")
        pil_image = Image.open(io.BytesIO(img_data))
        
        # Resize to thumbnail size
        pil_image = pil_image.resize((final_width, final_height), Image.BILINEAR)
        
        # Convert to QPixmap
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        qimage = QImage()
        qimage.loadFromData(img_byte_arr)
        pixmap = QPixmap.fromImage(qimage)
        
        # Get page size label
        size_text = self.get_page_size_label(page_index)
        
        return pixmap, size_text
    
    def get_page_size_label(self, page_index: int) -> str:
        """Get formatted page size label"""
        page = self.pdf_document.load_page(page_index)
        page_width = page.rect.width
        page_height = page.rect.height
        
        # Convert to mm
        width_mm = round(page_width / 72 * 25.4)
        height_mm = round(page_height / 72 * 25.4)
        
        # Known formats with tolerance
        known_formats = {
            "A6": (105, 148),
            "A5": (148, 210),
            "A4": (210, 297),
            "A3": (297, 420),
            "A2": (420, 594),
            "A1": (594, 841),
            "A0": (841, 1189),
            "B5": (176, 250),
            "B4": (250, 353),
            "Letter": (216, 279),
            "Legal": (216, 356),
        }
        
        tolerance = 5
        for name, (fw, fh) in known_formats.items():
            if (abs(width_mm - fw) <= tolerance and abs(height_mm - fh) <= tolerance):
                return name
            elif (abs(width_mm - fh) <= tolerance and abs(height_mm - fw) <= tolerance):
                return f"{name} (Poziom)"
        
        return f"{width_mm} x {height_mm} mm"
    
    def calculate_columns(self):
        """Calculate number of columns based on available width"""
        available_width = self.scroll_area.viewport().width() - 25  # scrollbar safety
        thumb_with_padding = self.thumb_width + (2 * THUMB_PADDING)
        cols = max(MIN_COLS, int(available_width / thumb_with_padding))
        cols = min(MAX_COLS, cols)
        self.current_cols = max(1, cols)
    
    def reconfigure_grid(self):
        """Reconfigure the grid layout (called on resize)"""
        if not self.pdf_document:
            return
        
        old_cols = self.current_cols
        self.calculate_columns()
        
        # Only reconfigure if column count changed
        if old_cols != self.current_cols:
            # Remove all widgets from layout
            for i in reversed(range(self.grid_layout.count())):
                item = self.grid_layout.itemAt(i)
                if item.widget():
                    self.grid_layout.removeItem(item)
            
            # Re-add in new grid configuration
            for idx, thumbnail in enumerate(self.thumbnail_widgets):
                row = idx // self.current_cols
                col = idx % self.current_cols
                self.grid_layout.addWidget(thumbnail, row, col)
    
    def resizeEvent(self, event):
        """Handle resize events with debouncing"""
        super().resizeEvent(event)
        self.resize_timer.start(150)  # 150ms debounce


class PDFViewerMainWindow(QMainWindow):
    """Main window for PDF viewer"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{PROGRAM_TITLE} v{PROGRAM_VERSION}")
        self.resize(1024, 768)
        
        # Set icon if available
        icon_path = resource_path(os.path.join('icons', 'gryf.ico'))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Setup UI
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()
        
        # Apply stylesheet
        self.apply_stylesheet()
        
        self.update_status("Gotowy. Otwórz plik PDF.")
    
    def setup_ui(self):
        """Setup main UI components"""
        self.viewer = PDFViewerWidget()
        self.setCentralWidget(self.viewer)
    
    def setup_menu(self):
        """Setup menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&Plik")
        
        open_action = QAction("&Otwórz PDF...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_pdf)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        close_action = QAction("&Zamknij PDF", self)
        close_action.setShortcut("Ctrl+W")
        close_action.triggered.connect(self.close_pdf)
        file_menu.addAction(close_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("&Zakończ", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Pomoc")
        
        about_action = QAction("&O programie", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_toolbar(self):
        """Setup toolbar with buttons"""
        toolbar = QToolBar("Narzędzia")
        toolbar.setIconSize(QSize(32, 32))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Open button
        open_icon_path = resource_path(os.path.join('icons', 'open.png'))
        if os.path.exists(open_icon_path):
            open_action = QAction(QIcon(open_icon_path), "Otwórz PDF", self)
        else:
            open_action = QAction("Otwórz PDF", self)
        open_action.triggered.connect(self.open_pdf)
        toolbar.addAction(open_action)
        
        toolbar.addSeparator()
        
        # Zoom buttons
        zoom_in_icon_path = resource_path(os.path.join('icons', 'zoom_in.png'))
        zoom_out_icon_path = resource_path(os.path.join('icons', 'zoom_out.png'))
        
        if os.path.exists(zoom_in_icon_path):
            zoom_in_action = QAction(QIcon(zoom_in_icon_path), "Powiększ miniatury", self)
        else:
            zoom_in_action = QAction("Powiększ", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)
        
        if os.path.exists(zoom_out_icon_path):
            zoom_out_action = QAction(QIcon(zoom_out_icon_path), "Pomniejsz miniatury", self)
        else:
            zoom_out_action = QAction("Pomniejsz", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)
    
    def setup_statusbar(self):
        """Setup status bar"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.setStyleSheet(f"background-color: {BG_SECONDARY}; color: {FG_TEXT};")
    
    def apply_stylesheet(self):
        """Apply application stylesheet for consistent look"""
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {BG_PRIMARY};
            }}
            QMenuBar {{
                background-color: {BG_SECONDARY};
                color: {FG_TEXT};
            }}
            QMenuBar::item:selected {{
                background-color: #C0C0C0;
            }}
            QMenu {{
                background-color: {BG_SECONDARY};
                color: {FG_TEXT};
            }}
            QMenu::item:selected {{
                background-color: #C0C0C0;
            }}
            QToolBar {{
                background-color: {BG_SECONDARY};
                border: 1px solid #C0C0C0;
                spacing: 3px;
            }}
            QToolButton {{
                background-color: #D0D0D0;
                border: 1px solid #A0A0A0;
                border-radius: 3px;
                padding: 5px;
            }}
            QToolButton:hover {{
                background-color: #E0E0E0;
            }}
            QToolButton:pressed {{
                background-color: #B0B0B0;
            }}
        """)
    
    def open_pdf(self):
        """Open a PDF file"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Wybierz plik PDF",
            "",
            "Pliki PDF (*.pdf)"
        )
        
        if not filepath:
            return
        
        try:
            self.update_status(f"Otwieranie pliku: {os.path.basename(filepath)}...")
            QApplication.processEvents()  # Update UI
            
            self.viewer.load_pdf(filepath)
            
            page_count = len(self.viewer.pdf_document)
            self.update_status(f"Dokument wczytany. Liczba stron: {page_count}")
            self.setWindowTitle(f"{PROGRAM_TITLE} - {os.path.basename(filepath)}")
            
        except Exception as e:
            self.update_status(f"Błąd podczas otwierania pliku: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Błąd", f"Nie udało się otworzyć pliku PDF:\n{e}")
    
    def close_pdf(self):
        """Close the current PDF"""
        self.viewer.close_pdf()
        self.setWindowTitle(f"{PROGRAM_TITLE} v{PROGRAM_VERSION}")
        self.update_status("Gotowy. Otwórz plik PDF.")
    
    def zoom_in(self):
        """Increase thumbnail size"""
        if self.viewer.pdf_document:
            new_width = int(self.viewer.thumb_width * 1.2)
            self.viewer.thumb_width = min(MAX_THUMB_WIDTH, new_width)
            self.viewer.render_thumbnails()
            self.update_status(f"Powiększono miniatury (szerokość: {self.viewer.thumb_width}px)")
    
    def zoom_out(self):
        """Decrease thumbnail size"""
        if self.viewer.pdf_document:
            new_width = int(self.viewer.thumb_width * 0.8)
            self.viewer.thumb_width = max(MIN_THUMB_WIDTH, new_width)
            self.viewer.render_thumbnails()
            self.update_status(f"Pomniejszono miniatury (szerokość: {self.viewer.thumb_width}px)")
    
    def show_about(self):
        """Show about dialog"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.about(
            self,
            "O programie",
            f"{PROGRAM_TITLE}\n"
            f"Wersja {PROGRAM_VERSION}\n\n"
            "Przeglądarka dokumentów PDF oparta na PySide6.\n"
            "Uproszczona wersja do przeglądania plików PDF.\n\n"
            "© Centrum Graficzne GRYF sp. z o.o."
        )
    
    def update_status(self, message: str):
        """Update status bar message"""
        self.statusbar.showMessage(message)


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName(PROGRAM_TITLE)
    app.setApplicationVersion(PROGRAM_VERSION)
    
    window = PDFViewerMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
