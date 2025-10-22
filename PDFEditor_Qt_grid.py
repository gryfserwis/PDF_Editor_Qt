import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QScrollArea, QGridLayout, QToolButton
)
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
import fitz  # PyMuPDF


class PDFThumbnailsWidget(QWidget):
    def __init__(self, pdf_path: str):
        super().__init__()
        self.doc = None
        self.thumb_scale = 0.2
        self.selected_pages = set()
        self.buttons: list[QToolButton] = []
        self.thumbnails: list[QWidget] = []
        self._last_selected_idx: int | None = None
        self._current_cols: int | None = None

        # Layout for the grid of thumbnails
        self.grid_layout = QGridLayout()
        self.grid_layout.setHorizontalSpacing(12)
        self.grid_layout.setVerticalSpacing(16)
        self.setLayout(self.grid_layout)

        # Open document
        try:
            self.doc = fitz.open(pdf_path)
        except Exception as e:
            lay = QVBoxLayout()
            lay.addWidget(QLabel(f"Cannot open PDF: {e}"))
            self.setLayout(lay)
            return

        if self.doc.page_count == 0:
            lay = QVBoxLayout()
            lay.addWidget(QLabel("PDF has no pages."))
            self.setLayout(lay)
            return

        self._build_thumbnails()
        self.update_grid()

    # Public selection helpers
    def select_all(self):
        for btn in self.buttons:
            btn.setChecked(True)

    def clear_selection(self):
        for btn in self.buttons:
            btn.setChecked(False)

    # Internal: build all thumbnails
    def _build_thumbnails(self):
        self.thumbnails.clear()
        self.buttons.clear()
        thumb_style = (
            "QToolButton {background: white; border: 2px solid #ccc; margin: 4px;}"
            " QToolButton:checked {border: 2px solid #0078d7; background: #e6f0fa;}"
        )
        for i, page in enumerate(self.doc):
            pix = page.get_pixmap(matrix=fitz.Matrix(self.thumb_scale, self.thumb_scale), alpha=False)
            fmt = QImage.Format_RGBA8888 if pix.alpha else QImage.Format_RGB888
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
            pixmap = QPixmap.fromImage(img)

            btn = QToolButton()
            btn.setCheckable(True)
            btn.setIcon(pixmap)
            btn.setIconSize(pixmap.size())
            btn.setFixedSize(pixmap.size())
            btn.setStyleSheet(thumb_style)

            def on_clicked(checked, idx=i):
                mods = QApplication.keyboardModifiers()
                if mods & Qt.ShiftModifier and self._last_selected_idx is not None:
                    start = min(self._last_selected_idx, idx)
                    end = max(self._last_selected_idx, idx)
                    for j in range(start, end + 1):
                        self.buttons[j].setChecked(True)
                else:
                    self.toggle_page(idx, checked)
                    if checked:
                        self._last_selected_idx = idx

            btn.clicked.connect(on_clicked)

            page_num = QLabel(f"Strona {i+1}")
            page_num.setAlignment(Qt.AlignHCenter)
            w, h = page.rect.width, page.rect.height
            fmt_name = self._get_format_name(w, h)
            fmt_label = QLabel(fmt_name)
            fmt_label.setAlignment(Qt.AlignHCenter)

            container = QWidget()
            v = QVBoxLayout(container)
            v.setContentsMargins(4, 4, 4, 4)
            v.setSpacing(4)
            v.setAlignment(Qt.AlignHCenter)
            v.addWidget(btn, alignment=Qt.AlignHCenter)
            bottom = QVBoxLayout()
            bottom.setSpacing(0)
            bottom.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
            bottom.addWidget(page_num, alignment=Qt.AlignHCenter)
            bottom.addWidget(fmt_label, alignment=Qt.AlignHCenter)
            v.addLayout(bottom)

            def update_style(checked, widget=container, page_label=page_num, format_label=fmt_label):
                if checked:
                    widget.setStyleSheet("background: #e6f0fa;")
                    page_label.setStyleSheet("color: black;")
                    format_label.setStyleSheet("color: black;")
                else:
                    widget.setStyleSheet("")
                    page_label.setStyleSheet("")
                    format_label.setStyleSheet("")

            btn.toggled.connect(update_style)

            self.thumbnails.append(container)
            self.buttons.append(btn)

    def set_thumb_scale(self, scale: float):
        self.thumb_scale = max(0.1, min(scale, 1.5))
        if not self.doc:
            return
        # Rerender images for new scale
        for i, page in enumerate(self.doc):
            pix = page.get_pixmap(matrix=fitz.Matrix(self.thumb_scale, self.thumb_scale), alpha=False)
            fmt = QImage.Format_RGBA8888 if pix.alpha else QImage.Format_RGB888
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
            pm = QPixmap.fromImage(img)
            btn = self.buttons[i]
            btn.setIcon(pm)
            btn.setIconSize(pm.size())
            btn.setFixedSize(pm.size())
        self._current_cols = None
        self.update_grid(self._get_area_width())

    def _get_area_width(self) -> int:
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, 'viewport'):
                return parent.viewport().width()
            parent = parent.parent()
        return self.width()

    def _get_format_name(self, w: float, h: float) -> str:
        mm_w = w * 25.4 / 72
        mm_h = h * 25.4 / 72
        formats = {
            "A0": (841, 1189),
            "A1": (594, 841),
            "A2": (420, 594),
            "A3": (297, 420),
            "A4": (210, 297),
            "A5": (148, 210),
            "Letter": (216, 279),
        }
        for name, (fw, fh) in formats.items():
            if (abs(mm_w - fw) < 15 and abs(mm_h - fh) < 15) or (abs(mm_w - fh) < 15 and abs(mm_h - fw) < 15):
                return name
        return f"{int(mm_w)}x{int(mm_h)} mm"

    def update_grid(self, area_width: int | None = None):
        if not self.thumbnails:
            return
        btn = self.buttons[0]
        thumb_w = btn.width() + 24  # include padding/margins
        if area_width is None:
            area_width = self._get_area_width()
        cols = max(1, area_width // thumb_w)
        if self._current_cols == cols:
            return
        self._current_cols = cols

        # Clear previous
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
        # Add in grid
        for idx, widget in enumerate(self.thumbnails):
            self.grid_layout.addWidget(widget, idx // cols, idx % cols)
        for c in range(cols):
            self.grid_layout.setColumnStretch(c, 1)

    def toggle_page(self, idx: int, checked: bool):
        if checked:
            self.selected_pages.add(idx)
        else:
            self.selected_pages.discard(idx)

    def get_selected_pages(self) -> list[int]:
        return sorted(self.selected_pages)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Thumbnails Viewer")
        self.resize(1000, 700)

        central = QWidget()
        v = QVBoxLayout(central)

        hb = QHBoxLayout()
        self.zoom_in_btn = QPushButton("+")
        self.zoom_out_btn = QPushButton("-")
        self.zoom_in_btn.setFixedWidth(40)
        self.zoom_out_btn.setFixedWidth(40)
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        hb.addWidget(self.zoom_in_btn)
        hb.addWidget(self.zoom_out_btn)
        hb.addStretch()
        self.open_btn = QPushButton("Open PDF")
        self.open_btn.clicked.connect(self.open_pdf)
        hb.addWidget(self.open_btn)
        v.addLayout(hb)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        v.addWidget(self.scroll)

        self.setCentralWidget(central)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        child = self.scroll.widget()
        if child and hasattr(child, 'update_grid'):
            child.update_grid(self.scroll.viewport().width())

    def keyPressEvent(self, event):
        child = self.scroll.widget()
        if isinstance(child, PDFThumbnailsWidget):
            if event.key() in (Qt.Key_Plus, Qt.Key_Equal):
                self.zoom_in()
            elif event.key() in (Qt.Key_Minus, Qt.Key_Underscore):
                self.zoom_out()
            elif event.key() == Qt.Key_A and event.modifiers() & Qt.ControlModifier:
                child.select_all()
            elif event.key() == Qt.Key_Escape:
                child.clear_selection()
        super().keyPressEvent(event)

    def zoom_in(self):
        child = self.scroll.widget()
        if isinstance(child, PDFThumbnailsWidget):
            child.set_thumb_scale(child.thumb_scale + 0.05)

    def zoom_out(self):
        child = self.scroll.widget()
        if isinstance(child, PDFThumbnailsWidget):
            child.set_thumb_scale(child.thumb_scale - 0.05)

    def open_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf)")
        if file_path:
            widget = PDFThumbnailsWidget(file_path)
            self.scroll.setWidget(widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
