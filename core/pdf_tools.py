"""
PDFTools - Narzędzia do operacji na plikach PDF

Ten moduł zawiera wszystkie operacje związane z manipulacją dokumentów PDF:
- Kadrowanie i zmiana rozmiaru stron
- Numeracja stron
- Obracanie, usuwanie, duplikowanie stron
- Operacje clipboard (kopiowanie, wycinanie, wklejanie)
- Import i eksport PDF oraz obrazów
- Przesuwanie zawartości, scalanie stron
"""

import io
import fitz  # PyMuPDF
from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import RectangleObject, FloatObject, ArrayObject, NameObject
from PIL import Image
import os
from typing import Set, Optional, Callable
from utils import mm2pt, custom_messagebox, generate_unique_export_filename


class PDFTools:
    """Klasa narzędziowa do operacji na dokumentach PDF"""
    
    MM_TO_POINTS = 72 / 25.4  # ~2.8346
    MARGIN_HEIGHT_MM = 20
    MARGIN_HEIGHT_PT = MARGIN_HEIGHT_MM * MM_TO_POINTS
    
    def __init__(self):
        """Inicjalizacja narzędzi PDF"""
        pass
    
    # ============================================================================
    # KADROWANIE I ZMIANA ROZMIARU
    # ============================================================================
    
    def crop_pages(self, pdf_bytes: bytes, selected_indices: Set[int], 
                   top_mm: float, bottom_mm: float, left_mm: float, right_mm: float,
                   reposition: bool = False, pos_mode: str = "center", 
                   offset_x_mm: float = 0, offset_y_mm: float = 0,
                   progress_callback: Optional[Callable[[str], None]] = None,
                   progressbar_callback: Optional[Callable[[int, int], None]] = None) -> bytes:
        """
        Kadruje strony PDF poprzez ustawienie cropbox.
        
        Args:
            pdf_bytes: Bajty dokumentu PDF
            selected_indices: Indeksy stron do kadrowania
            top_mm, bottom_mm, left_mm, right_mm: Marginesy kadrowania w mm
            reposition: Czy przesunąć zawartość
            pos_mode: Tryb pozycjonowania ("center" lub "custom")
            offset_x_mm, offset_y_mm: Przesunięcie w mm (gdy pos_mode="custom")
            progress_callback: Funkcja callback dla statusu
            progressbar_callback: Funkcja callback dla paska postępu (current, total)
            
        Returns:
            Bajty zmodyfikowanego dokumentu PDF
        """
        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()
        total_pages = len(reader.pages)
        
        if progress_callback:
            progress_callback("Kadrowanie stron...")
        if progressbar_callback:
            progressbar_callback(0, total_pages)
        
        for i, page in enumerate(reader.pages):
            if i not in selected_indices:
                writer.add_page(page)
                if progressbar_callback:
                    progressbar_callback(i + 1, total_pages)
                continue
                
            orig_mediabox = RectangleObject([float(v) for v in page.mediabox])
            x0, y0, x1, y1 = [float(v) for v in orig_mediabox]
            new_x0 = x0 + mm2pt(left_mm)
            new_y0 = y0 + mm2pt(bottom_mm)
            new_x1 = x1 - mm2pt(right_mm)
            new_y1 = y1 - mm2pt(top_mm)
            
            if new_x0 >= new_x1 or new_y0 >= new_y1:
                writer.add_page(page)
                if progressbar_callback:
                    progressbar_callback(i + 1, total_pages)
                continue
                
            new_rect = RectangleObject([new_x0, new_y0, new_x1, new_y1])
            
            # Ustaw tylko cropbox, trimbox, artbox - mediabox zostaje oryginalny
            page.cropbox = new_rect
            page.trimbox = new_rect
            page.artbox = new_rect
            page.mediabox = orig_mediabox
            
            # Opcjonalnie: przesuwanie zawartości strony
            if reposition:
                dx = mm2pt(offset_x_mm) if pos_mode == "custom" else 0
                dy = mm2pt(offset_y_mm) if pos_mode == "custom" else 0
                if dx != 0 or dy != 0:
                    transform = Transformation().translate(tx=dx, ty=dy)
                    page.add_transformation(transform)
            
            writer.add_page(page)
            if progressbar_callback:
                progressbar_callback(i + 1, total_pages)
        
        out = io.BytesIO()
        writer.write(out)
        out.seek(0)
        return out.read()
    
    def mask_crop_pages(self, pdf_bytes: bytes, selected_indices: Set[int],
                       top_mm: float, bottom_mm: float, left_mm: float, right_mm: float,
                       progress_callback: Optional[Callable[[str], None]] = None,
                       progressbar_callback: Optional[Callable[[int, int], None]] = None) -> bytes:
        """
        Kadruje strony PDF poprzez maskowanie (usuwanie zawartości poza obszarem).
        Używa PyMuPDF do faktycznego usunięcia zawartości.
        
        Args:
            pdf_bytes: Bajty dokumentu PDF
            selected_indices: Indeksy stron do kadrowania
            top_mm, bottom_mm, left_mm, right_mm: Marginesy kadrowania w mm
            progress_callback: Funkcja callback dla statusu
            progressbar_callback: Funkcja callback dla paska postępu
            
        Returns:
            Bajty zmodyfikowanego dokumentu PDF
        """
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)
        
        if progress_callback:
            progress_callback("Kadrowanie z maską stron...")
        if progressbar_callback:
            progressbar_callback(0, total_pages)
        
        for i in range(total_pages):
            if i not in selected_indices:
                if progressbar_callback:
                    progressbar_callback(i + 1, total_pages)
                continue
                
            page = doc.load_page(i)
            rect = page.rect
            x0, y0, x1, y1 = rect.x0, rect.y0, rect.x1, rect.y1
            
            new_x0 = x0 + mm2pt(left_mm)
            new_y0 = y0 + mm2pt(bottom_mm)
            new_x1 = x1 - mm2pt(right_mm)
            new_y1 = y1 - mm2pt(top_mm)
            
            if new_x0 >= new_x1 or new_y0 >= new_y1:
                if progressbar_callback:
                    progressbar_callback(i + 1, total_pages)
                continue
            
            new_rect = fitz.Rect(new_x0, new_y0, new_x1, new_y1)
            page.set_cropbox(new_rect)
            page.set_mediabox(new_rect)
            
            if progressbar_callback:
                progressbar_callback(i + 1, total_pages)
        
        out = io.BytesIO()
        doc.save(out)
        doc.close()
        out.seek(0)
        return out.read()
    
    def resize_pages_with_scale(self, pdf_bytes: bytes, selected_indices: Set[int],
                               width_mm: float, height_mm: float,
                               progress_callback: Optional[Callable[[str], None]] = None,
                               progressbar_callback: Optional[Callable[[int, int], None]] = None) -> bytes:
        """
        Zmienia rozmiar stron ze skalowaniem zawartości.
        
        Args:
            pdf_bytes: Bajty dokumentu PDF
            selected_indices: Indeksy stron do zmiany rozmiaru
            width_mm, height_mm: Nowy rozmiar w mm
            progress_callback: Funkcja callback dla statusu
            progressbar_callback: Funkcja callback dla paska postępu
            
        Returns:
            Bajty zmodyfikowanego dokumentu PDF
        """
        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()
        target_width = mm2pt(width_mm)
        target_height = mm2pt(height_mm)
        total_pages = len(reader.pages)
        
        if progress_callback:
            progress_callback("Zmiana rozmiaru stron ze skalowaniem...")
        if progressbar_callback:
            progressbar_callback(0, total_pages)
        
        for i, page in enumerate(reader.pages):
            if i not in selected_indices:
                writer.add_page(page)
                if progressbar_callback:
                    progressbar_callback(i + 1, total_pages)
                continue
                
            orig_w = float(page.mediabox.width)
            orig_h = float(page.mediabox.height)
            scale = min(target_width / orig_w, target_height / orig_h)
            dx = (target_width - orig_w * scale) / 2
            dy = (target_height - orig_h * scale) / 2
            transform = Transformation().scale(sx=scale, sy=scale).translate(tx=dx, ty=dy)
            page.add_transformation(transform)
            page.mediabox = RectangleObject([0, 0, target_width, target_height])
            page.cropbox = RectangleObject([0, 0, target_width, target_height])
            writer.add_page(page)
            
            if progressbar_callback:
                progressbar_callback(i + 1, total_pages)
        
        out = io.BytesIO()
        writer.write(out)
        out.seek(0)
        return out.read()
    
    def resize_pages_without_scale(self, pdf_bytes: bytes, selected_indices: Set[int],
                                   width_mm: float, height_mm: float,
                                   pos_mode: str = "center", offset_x_mm: float = 0, offset_y_mm: float = 0,
                                   progress_callback: Optional[Callable[[str], None]] = None,
                                   progressbar_callback: Optional[Callable[[int, int], None]] = None) -> bytes:
        """
        Zmienia rozmiar stron bez skalowania zawartości.
        
        Args:
            pdf_bytes: Bajty dokumentu PDF
            selected_indices: Indeksy stron do zmiany rozmiaru
            width_mm, height_mm: Nowy rozmiar w mm
            pos_mode: Tryb pozycjonowania ("center" lub "custom")
            offset_x_mm, offset_y_mm: Przesunięcie w mm
            progress_callback: Funkcja callback dla statusu
            progressbar_callback: Funkcja callback dla paska postępu
            
        Returns:
            Bajty zmodyfikowanego dokumentu PDF
        """
        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()
        target_width = mm2pt(width_mm)
        target_height = mm2pt(height_mm)
        total_pages = len(reader.pages)
        
        if progress_callback:
            progress_callback("Zmiana rozmiaru stron bez skalowania...")
        if progressbar_callback:
            progressbar_callback(0, total_pages)
        
        for i, page in enumerate(reader.pages):
            if i not in selected_indices:
                writer.add_page(page)
                if progressbar_callback:
                    progressbar_callback(i + 1, total_pages)
                continue
                
            orig_w = float(page.mediabox.width)
            orig_h = float(page.mediabox.height)
            
            if pos_mode == "center":
                dx = (target_width - orig_w) / 2
                dy = (target_height - orig_h) / 2
            else:  # custom
                dx = mm2pt(offset_x_mm)
                dy = mm2pt(offset_y_mm)
            
            if dx != 0 or dy != 0:
                transform = Transformation().translate(tx=dx, ty=dy)
                page.add_transformation(transform)
            
            page.mediabox = RectangleObject([0, 0, target_width, target_height])
            page.cropbox = RectangleObject([0, 0, target_width, target_height])
            writer.add_page(page)
            
            if progressbar_callback:
                progressbar_callback(i + 1, total_pages)
        
        out = io.BytesIO()
        writer.write(out)
        out.seek(0)
        return out.read()
    
    # ============================================================================
    # NUMERACJA STRON
    # ============================================================================
    
    def insert_page_numbers(self, pdf_document, selected_indices: list, settings: dict,
                           progress_callback: Optional[Callable[[str], None]] = None,
                           progressbar_callback: Optional[Callable[[int, int], None]] = None):
        """
        Wstawia numerację stron do dokumentu PDF.
        
        Args:
            pdf_document: Dokument fitz (PyMuPDF)
            selected_indices: Lista indeksów stron do numeracji (posortowana)
            settings: Słownik z ustawieniami numeracji
            progress_callback: Funkcja callback dla statusu
            progressbar_callback: Funkcja callback dla paska postępu
        """
        if progress_callback:
            progress_callback("Wstawianie numeracji stron...")
        
        MM_PT = self.MM_TO_POINTS
        
        start_number = settings['start_num']
        mode = settings['mode']
        direction = settings['alignment']
        position = settings['vertical_pos']
        mirror_margins = settings['mirror_margins']
        format_mode = settings['format_type']
        
        left_mm = settings['margin_left_mm']
        right_mm = settings['margin_right_mm']
        
        left_pt_base = left_mm * MM_PT
        right_pt_base = right_mm * MM_PT
        margin_v = settings['margin_vertical_mm'] * MM_PT
        font_size = settings['font_size']
        font = settings['font_name']
        
        current_number = start_number
        total_counted_pages = len(selected_indices) + start_number - 1
        
        if progressbar_callback:
            progressbar_callback(0, len(selected_indices))
        
        for idx, i in enumerate(selected_indices):
            page = pdf_document.load_page(i)
            rect = page.rect
            rotation = page.rotation
            
            text = f"Strona {current_number} z {total_counted_pages}" if format_mode == 'full' else str(current_number)
            text_width = fitz.get_text_length(text, fontname=font, fontsize=font_size)
            
            numerowana_strona = idx
            
            # Ustal alignment
            if mode == "lustrzana":
                if direction == "lewa":
                    align = "lewa" if numerowana_strona % 2 == 0 else "prawa"
                elif direction == "prawa":
                    align = "prawa" if numerowana_strona % 2 == 0 else "lewa"
                else:
                    align = "srodek"
            else:
                align = direction
            
            # Pozycjonowanie numeru
            if mirror_margins:
                if numerowana_strona % 2 == 1:
                    left_pt, right_pt = right_pt_base, left_pt_base
                else:
                    left_pt, right_pt = left_pt_base, right_pt_base
            else:
                left_pt, right_pt = left_pt_base, right_pt_base
            
            # Logika pozycjonowania dla różnych rotacji
            if rotation == 0:
                if align == "lewa":
                    x = rect.x0 + left_pt
                elif align == "prawa":
                    x = rect.x1 - right_pt - text_width
                elif align == "srodek":
                    text_area_w = rect.width - left_pt - right_pt
                    x = rect.x0 + left_pt + (text_area_w / 2) - (text_width / 2)
                y = rect.y0 + margin_v + font_size if position == "gora" else rect.y1 - margin_v
                angle = 0
                
            elif rotation == 90:
                lp, rp = left_pt, right_pt
                x = rect.y0 + margin_v + font_size if position == "gora" else rect.y1 - margin_v
                if align == "lewa":
                    y = rect.x1 - lp
                elif align == "prawa":
                    y = rect.x0 + rp + text_width
                elif align == "srodek":
                    text_area_w = rect.width - lp - rp
                    y = rect.x0 + rp + (text_area_w / 2) + (text_width / 2)
                angle = 90
                
            elif rotation == 180:
                lp, rp = left_pt, right_pt
                if align == "lewa":
                    x = rect.x1 - lp
                elif align == "prawa":
                    x = rect.x0 + rp + text_width
                elif align == "srodek":
                    text_area_w = rect.width - lp - rp
                    x = rect.x0 + rp + (text_area_w / 2) + (text_width / 2)
                y = rect.y1 - margin_v - font_size if position == "gora" else rect.y0 + margin_v
                angle = 180
                
            elif rotation == 270:
                lp, rp = left_pt, right_pt
                x = rect.y1 - margin_v - font_size if position == "gora" else rect.y0 + margin_v
                if align == "lewa":
                    y = rect.x0 + lp
                elif align == "prawa":
                    y = rect.x1 - rp - text_width
                elif align == "srodek":
                    text_area_w = rect.width - lp - rp
                    x_center = rect.x0 + rp + (text_area_w / 2)
                    y = x_center - (text_width / 2)
                angle = 270
            
            # Wstaw tekst na stronę
            page.insert_text(
                (x, y),
                text,
                fontname=font,
                fontsize=font_size,
                rotate=angle
            )
            
            current_number += 1
            
            if progressbar_callback:
                progressbar_callback(idx + 1, len(selected_indices))
    
    def remove_page_numbers(self, pdf_document, selected_indices: list, settings: dict,
                           progress_callback: Optional[Callable[[str], None]] = None,
                           progressbar_callback: Optional[Callable[[int, int], None]] = None):
        """
        Usuwa numerację stron z dokumentu PDF.
        
        Args:
            pdf_document: Dokument fitz (PyMuPDF)
            selected_indices: Lista indeksów stron
            settings: Słownik z ustawieniami obszaru usuwania
            progress_callback: Funkcja callback dla statusu
            progressbar_callback: Funkcja callback dla paska postępu
        """
        if progress_callback:
            progress_callback("Usuwanie numeracji stron...")
        
        MM_PT = self.MM_TO_POINTS
        margin_top_mm = settings['margin_top_mm']
        margin_bottom_mm = settings['margin_bottom_mm']
        margin_left_mm = settings['margin_left_mm']
        margin_right_mm = settings['margin_right_mm']
        
        if progressbar_callback:
            progressbar_callback(0, len(selected_indices))
        
        for idx, i in enumerate(selected_indices):
            page = pdf_document.load_page(i)
            rect = page.rect
            
            # Definiuj obszary do wyczyszczenia (górny i dolny margines)
            top_rect = fitz.Rect(
                rect.x0 + margin_left_mm * MM_PT,
                rect.y0,
                rect.x1 - margin_right_mm * MM_PT,
                rect.y0 + margin_top_mm * MM_PT
            )
            
            bottom_rect = fitz.Rect(
                rect.x0 + margin_left_mm * MM_PT,
                rect.y1 - margin_bottom_mm * MM_PT,
                rect.x1 - margin_right_mm * MM_PT,
                rect.y1
            )
            
            # Usuń tekst z tych obszarów
            page.add_redact_annot(top_rect, fill=(1, 1, 1))
            page.add_redact_annot(bottom_rect, fill=(1, 1, 1))
            page.apply_redactions()
            
            if progressbar_callback:
                progressbar_callback(idx + 1, len(selected_indices))
    
    # ============================================================================
    # OBRACANIE STRON
    # ============================================================================
    
    def rotate_pages(self, pdf_document, selected_indices: list, angle: int,
                    progress_callback: Optional[Callable[[str], None]] = None,
                    progressbar_callback: Optional[Callable[[int, int], None]] = None) -> int:
        """
        Obraca strony o podany kąt.
        
        Args:
            pdf_document: Dokument fitz (PyMuPDF)
            selected_indices: Lista indeksów stron do obrotu
            angle: Kąt obrotu (90, -90, 180, itp.)
            progress_callback: Funkcja callback dla statusu
            progressbar_callback: Funkcja callback dla paska postępu
            
        Returns:
            Liczba obróconych stron
        """
        if progressbar_callback:
            progressbar_callback(0, len(selected_indices))
        
        rotated_count = 0
        for idx, page_index in enumerate(selected_indices):
            page = pdf_document.load_page(page_index)
            current_rotation = page.rotation
            new_rotation = (current_rotation + angle) % 360
            page.set_rotation(new_rotation)
            rotated_count += 1
            
            if progressbar_callback:
                progressbar_callback(idx + 1, len(selected_indices))
        
        return rotated_count
    
    # ============================================================================
    # USUWANIE I ZARZĄDZANIE STRONAMI
    # ============================================================================
    
    def delete_pages(self, pdf_document, pages_to_delete: list,
                    progress_callback: Optional[Callable[[str], None]] = None,
                    progressbar_callback: Optional[Callable[[int, int], None]] = None) -> int:
        """
        Usuwa strony z dokumentu PDF.
        
        Args:
            pdf_document: Dokument fitz (PyMuPDF)
            pages_to_delete: Lista indeksów stron do usunięcia (posortowana malejąco)
            progress_callback: Funkcja callback dla statusu
            progressbar_callback: Funkcja callback dla paska postępu
            
        Returns:
            Liczba usuniętych stron
        """
        if progress_callback:
            progress_callback("Usuwanie stron...")
        
        if progressbar_callback:
            progressbar_callback(0, len(pages_to_delete))
        
        deleted_count = 0
        for idx, page_index in enumerate(pages_to_delete):
            pdf_document.delete_page(page_index)
            deleted_count += 1
            
            if progressbar_callback:
                progressbar_callback(idx + 1, len(pages_to_delete))
        
        return deleted_count
    
    def duplicate_page(self, pdf_document, page_index: int, position: int):
        """
        Duplikuje stronę w dokumencie PDF.
        
        Args:
            pdf_document: Dokument fitz (PyMuPDF)
            page_index: Indeks strony do duplikacji
            position: Pozycja, na której wstawić duplikat
        """
        pdf_document.copy_page(page_index, position)
    
    def swap_pages(self, pdf_document, page1_index: int, page2_index: int):
        """
        Zamienia miejscami dwie strony.
        
        Args:
            pdf_document: Dokument fitz (PyMuPDF)
            page1_index: Indeks pierwszej strony
            page2_index: Indeks drugiej strony
        """
        pdf_document.move_page(page1_index, page2_index)
        if page1_index < page2_index:
            pdf_document.move_page(page2_index - 1, page1_index)
        else:
            pdf_document.move_page(page2_index + 1, page1_index)
    
    def insert_blank_pages(self, pdf_document, sorted_pages: list, before: bool,
                          width: float = 595.276, height: float = 841.89,
                          progress_callback: Optional[Callable[[str], None]] = None,
                          progressbar_callback: Optional[Callable[[int, int], None]] = None) -> set:
        """
        Wstawia puste strony przed lub po zaznaczonych stronach.
        
        Args:
            pdf_document: Dokument fitz (PyMuPDF)
            sorted_pages: Posortowana lista indeksów stron
            before: True - przed stronami, False - po stronach
            width, height: Rozmiar pustej strony w punktach
            progress_callback: Funkcja callback dla statusu
            progressbar_callback: Funkcja callback dla paska postępu
            
        Returns:
            Zbiór indeksów nowo wstawionych stron
        """
        if progress_callback:
            progress_callback("Wstawianie pustych stron...")
        
        if progressbar_callback:
            progressbar_callback(0, len(sorted_pages))
        
        new_page_indices = set()
        offset = 0
        
        for idx, page_index in enumerate(sorted_pages):
            insert_at = page_index + offset if before else page_index + offset + 1
            pdf_document.new_page(pno=insert_at, width=width, height=height)
            new_page_indices.add(insert_at)
            offset += 1
            
            if progressbar_callback:
                progressbar_callback(idx + 1, len(sorted_pages))
        
        return new_page_indices
    
    # ============================================================================
    # CLIPBOARD (KOPIOWANIE, WYCINANIE, WKLEJANIE)
    # ============================================================================
    
    def get_page_bytes(self, pdf_document, page_indices: Set[int]) -> bytes:
        """
        Pobiera bajty wybranych stron jako osobny dokument PDF.
        
        Args:
            pdf_document: Dokument fitz (PyMuPDF)
            page_indices: Zbiór indeksów stron
            
        Returns:
            Bajty dokumentu PDF zawierającego wybrane strony
        """
        temp_doc = fitz.open()
        for idx in sorted(page_indices):
            temp_doc.insert_pdf(pdf_document, from_page=idx, to_page=idx)
        out = io.BytesIO()
        temp_doc.save(out)
        temp_doc.close()
        out.seek(0)
        return out.read()
    
    def paste_pages(self, pdf_document, clipboard_bytes: bytes, target_index: int,
                   progress_callback: Optional[Callable[[str], None]] = None,
                   progressbar_callback: Optional[Callable[[int, int], None]] = None) -> int:
        """
        Wkleja strony ze schowka do dokumentu.
        
        Args:
            pdf_document: Dokument fitz (PyMuPDF) docelowy
            clipboard_bytes: Bajty PDF ze schowka
            target_index: Indeks, na którym wkleić strony
            progress_callback: Funkcja callback dla statusu
            progressbar_callback: Funkcja callback dla paska postępu
            
        Returns:
            Liczba wklejonych stron
        """
        if progress_callback:
            progress_callback("Wklejanie stron...")
        
        clipboard_doc = fitz.open(stream=clipboard_bytes, filetype="pdf")
        pages_count = len(clipboard_doc)
        
        if progressbar_callback:
            progressbar_callback(0, pages_count)
        
        for i in range(pages_count):
            pdf_document.insert_pdf(clipboard_doc, from_page=i, to_page=i, start_at=target_index + i)
            if progressbar_callback:
                progressbar_callback(i + 1, pages_count)
        
        clipboard_doc.close()
        return pages_count
    
    # ============================================================================
    # PRZESUWANIE ZAWARTOŚCI
    # ============================================================================
    
    def shift_page_content(self, pdf_bytes: bytes, selected_indices: Set[int],
                          dx_mm: float, dy_mm: float,
                          progress_callback: Optional[Callable[[str], None]] = None,
                          progressbar_callback: Optional[Callable[[int, int], None]] = None) -> bytes:
        """
        Przesuwa zawartość stron o podane wartości.
        
        Args:
            pdf_bytes: Bajty dokumentu PDF
            selected_indices: Indeksy stron do przesunięcia
            dx_mm, dy_mm: Przesunięcie w mm
            progress_callback: Funkcja callback dla statusu
            progressbar_callback: Funkcja callback dla paska postępu
            
        Returns:
            Bajty zmodyfikowanego dokumentu PDF
        """
        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()
        total_pages = len(reader.pages)
        
        if progress_callback:
            progress_callback("Przesuwanie zawartości stron...")
        
        if progressbar_callback:
            progressbar_callback(0, total_pages)
        
        dx_pt = mm2pt(dx_mm)
        dy_pt = mm2pt(dy_mm)
        
        for i, page in enumerate(reader.pages):
            if i in selected_indices:
                transform = Transformation().translate(tx=dx_pt, ty=dy_pt)
                page.add_transformation(transform)
            writer.add_page(page)
            
            if progressbar_callback:
                progressbar_callback(i + 1, total_pages)
        
        out = io.BytesIO()
        writer.write(out)
        out.seek(0)
        return out.read()
    
    # ============================================================================
    # IMPORT I EKSPORT
    # ============================================================================
    
    def import_pdf_pages(self, pdf_document, import_filepath: str, target_index: int,
                        progress_callback: Optional[Callable[[str], None]] = None,
                        progressbar_callback: Optional[Callable[[int, int], None]] = None) -> int:
        """
        Importuje strony z innego pliku PDF.
        
        Args:
            pdf_document: Dokument fitz (PyMuPDF) docelowy
            import_filepath: Ścieżka do pliku PDF do zaimportowania
            target_index: Indeks, na którym wstawić zaimportowane strony
            progress_callback: Funkcja callback dla statusu
            progressbar_callback: Funkcja callback dla paska postępu
            
        Returns:
            Liczba zaimportowanych stron
        """
        if progress_callback:
            progress_callback("Importowanie PDF...")
        
        imported_doc = fitz.open(import_filepath)
        pages_count = len(imported_doc)
        
        if progressbar_callback:
            progressbar_callback(0, pages_count)
        
        for i in range(pages_count):
            pdf_document.insert_pdf(imported_doc, from_page=i, to_page=i, start_at=target_index + i)
            if progressbar_callback:
                progressbar_callback(i + 1, pages_count)
        
        imported_doc.close()
        return pages_count
    
    def import_image_as_page(self, pdf_document, image_filepath: str, target_index: int,
                            settings: dict,
                            progress_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Importuje obraz jako nową stronę PDF.
        
        Args:
            pdf_document: Dokument fitz (PyMuPDF) docelowy
            image_filepath: Ścieżka do pliku obrazu
            target_index: Indeks, na którym wstawić stronę
            settings: Słownik z ustawieniami (page_size, dpi, maintain_aspect_ratio)
            progress_callback: Funkcja callback dla statusu
            
        Returns:
            True jeśli import się powiódł, False w przeciwnym razie
        """
        if progress_callback:
            progress_callback("Importowanie obrazu...")
        
        try:
            page_size_str = settings.get('page_size', 'A4')
            dpi = settings.get('dpi', 300)
            maintain_aspect = settings.get('maintain_aspect_ratio', True)
            
            # Mapowanie rozmiarów stron
            page_sizes = {
                'A4': (595.276, 841.89),
                'A3': (841.89, 1190.55),
                'Letter': (612, 792),
                'Legal': (612, 1008)
            }
            
            page_width, page_height = page_sizes.get(page_size_str, (595.276, 841.89))
            
            # Utwórz nową stronę
            new_page = pdf_document.new_page(pno=target_index, width=page_width, height=page_height)
            
            # Wstaw obraz
            img_rect = fitz.Rect(0, 0, page_width, page_height)
            
            if maintain_aspect:
                # Oblicz skalowanie z zachowaniem proporcji
                img = Image.open(image_filepath)
                img_width, img_height = img.size
                img.close()
                
                scale_w = page_width / img_width
                scale_h = page_height / img_height
                scale = min(scale_w, scale_h)
                
                new_width = img_width * scale
                new_height = img_height * scale
                
                # Wycentruj obraz
                x_offset = (page_width - new_width) / 2
                y_offset = (page_height - new_height) / 2
                
                img_rect = fitz.Rect(x_offset, y_offset, x_offset + new_width, y_offset + new_height)
            
            new_page.insert_image(img_rect, filename=image_filepath)
            return True
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"Błąd importu obrazu: {e}")
            return False
    
    def export_pages_to_pdf(self, pdf_document, selected_indices: list, output_filepath: str,
                           progress_callback: Optional[Callable[[str], None]] = None,
                           progressbar_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        """
        Eksportuje wybrane strony do nowego pliku PDF.
        
        Args:
            pdf_document: Dokument fitz (PyMuPDF) źródłowy
            selected_indices: Lista indeksów stron do eksportu
            output_filepath: Ścieżka do pliku wyjściowego
            progress_callback: Funkcja callback dla statusu
            progressbar_callback: Funkcja callback dla paska postępu
            
        Returns:
            True jeśli eksport się powiódł, False w przeciwnym razie
        """
        if progress_callback:
            progress_callback("Eksportowanie stron do PDF...")
        
        try:
            new_doc = fitz.open()
            
            if progressbar_callback:
                progressbar_callback(0, len(selected_indices))
            
            for idx, page_index in enumerate(selected_indices):
                new_doc.insert_pdf(pdf_document, from_page=page_index, to_page=page_index)
                if progressbar_callback:
                    progressbar_callback(idx + 1, len(selected_indices))
            
            new_doc.save(output_filepath)
            new_doc.close()
            return True
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"Błąd eksportu: {e}")
            return False
    
    def export_pages_to_images(self, pdf_document, selected_indices: list, output_dir: str,
                              base_filename: str, dpi: int, image_format: str = 'png',
                              progress_callback: Optional[Callable[[str], None]] = None,
                              progressbar_callback: Optional[Callable[[int, int], None]] = None) -> list:
        """
        Eksportuje wybrane strony jako obrazy.
        
        Args:
            pdf_document: Dokument fitz (PyMuPDF) źródłowy
            selected_indices: Lista indeksów stron do eksportu
            output_dir: Katalog docelowy
            base_filename: Bazowa nazwa pliku
            dpi: Rozdzielczość eksportu
            image_format: Format obrazu ('png', 'jpg', 'tiff')
            progress_callback: Funkcja callback dla statusu
            progressbar_callback: Funkcja callback dla paska postępu
            
        Returns:
            Lista ścieżek do wyeksportowanych plików
        """
        if progress_callback:
            progress_callback("Eksportowanie stron do obrazów...")
        
        exported_files = []
        
        if progressbar_callback:
            progressbar_callback(0, len(selected_indices))
        
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        
        for idx, page_index in enumerate(selected_indices):
            page = pdf_document.load_page(page_index)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            # Generuj unikalną nazwę pliku
            single_page_range = str(page_index + 1)
            output_path = generate_unique_export_filename(
                output_dir, base_filename, single_page_range, image_format
            )
            
            # Zapisz obraz
            pix.save(output_path)
            
            exported_files.append(output_path)
            
            if progressbar_callback:
                progressbar_callback(idx + 1, len(selected_indices))
        
        return exported_files
    
    def create_pdf_from_image(self, image_filepath: str, settings: dict) -> Optional[bytes]:
        """
        Tworzy nowy dokument PDF z obrazu.
        
        Args:
            image_filepath: Ścieżka do pliku obrazu
            settings: Słownik z ustawieniami (page_size, dpi, maintain_aspect_ratio)
            
        Returns:
            Bajty dokumentu PDF lub None w przypadku błędu
        """
        try:
            page_size_str = settings.get('page_size', 'A4')
            maintain_aspect = settings.get('maintain_aspect_ratio', True)
            
            page_sizes = {
                'A4': (595.276, 841.89),
                'A3': (841.89, 1190.55),
                'Letter': (612, 792),
                'Legal': (612, 1008)
            }
            
            page_width, page_height = page_sizes.get(page_size_str, (595.276, 841.89))
            
            doc = fitz.open()
            page = doc.new_page(width=page_width, height=page_height)
            
            img_rect = fitz.Rect(0, 0, page_width, page_height)
            
            if maintain_aspect:
                img = Image.open(image_filepath)
                img_width, img_height = img.size
                img.close()
                
                scale_w = page_width / img_width
                scale_h = page_height / img_height
                scale = min(scale_w, scale_h)
                
                new_width = img_width * scale
                new_height = img_height * scale
                
                x_offset = (page_width - new_width) / 2
                y_offset = (page_height - new_height) / 2
                
                img_rect = fitz.Rect(x_offset, y_offset, x_offset + new_width, y_offset + new_height)
            
            page.insert_image(img_rect, filename=image_filepath)
            
            out = io.BytesIO()
            doc.save(out)
            doc.close()
            out.seek(0)
            return out.read()
            
        except Exception:
            return None
    
    def create_pdf_from_image_exact_size(self, image_filepath: str) -> Optional['fitz.Document']:
        """
        Tworzy nowy dokument PDF z obrazu.
        Strona PDF będzie miała dokładnie taki rozmiar jak obraz (w punktach PDF).
        
        Args:
            image_filepath: Ścieżka do pliku obrazu
            
        Returns:
            Dokument fitz (PyMuPDF) lub None w przypadku błędu
        """
        try:
            img = Image.open(image_filepath)
            image_width_px, image_height_px = img.size
            image_dpi = img.info.get('dpi', (96, 96))[0] if isinstance(img.info.get('dpi'), tuple) else 96
            img.close()
            
            # Przelicz piksele na punkty PDF (1 cal = 72 punkty)
            image_width_pt = (image_width_px / image_dpi) * 72
            image_height_pt = (image_height_px / image_dpi) * 72
            
            # Stwórz nowy dokument PDF
            pdf_document = fitz.open()
            
            # Nowa strona o rozmiarze obrazu
            page = pdf_document.new_page(width=image_width_pt, height=image_height_pt)
            rect = fitz.Rect(0, 0, image_width_pt, image_height_pt)
            page.insert_image(rect, filename=image_filepath)
            
            return pdf_document
            
        except Exception:
            return None
    
    # ============================================================================
    # SCALANIE STRON W SIATKĘ
    # ============================================================================
    
    def merge_pages_into_grid(self, pdf_document, selected_indices: list, rows: int, cols: int,
                             sheet_width_pt: float, sheet_height_pt: float,
                             margin_top_pt: float, margin_bottom_pt: float,
                             margin_left_pt: float, margin_right_pt: float,
                             spacing_x_pt: float, spacing_y_pt: float,
                             target_dpi: int = 600,
                             progress_callback: Optional[Callable[[str], None]] = None,
                             progressbar_callback: Optional[Callable[[int, int], None]] = None) -> None:
        """
        Scala strony w siatkę na nowym arkuszu.
        Bitmapy renderowane są w wysokiej rozdzielczości (domyślnie 600dpi).
        Przed renderowaniem każda strona jest automatycznie obracana jeśli jej orientacja nie pasuje do komórki siatki.
        
        Args:
            pdf_document: Dokument fitz (PyMuPDF)
            selected_indices: Lista indeksów stron do scalenia
            rows, cols: Liczba wierszy i kolumn w siatce
            sheet_width_pt, sheet_height_pt: Rozmiar arkusza w punktach
            margin_top_pt, margin_bottom_pt, margin_left_pt, margin_right_pt: Marginesy w punktach
            spacing_x_pt, spacing_y_pt: Odstępy między komórkami w punktach
            target_dpi: Rozdzielczość renderowania bitmap (domyślnie 600)
            progress_callback: Funkcja callback dla statusu
            progressbar_callback: Funkcja callback dla paska postępu
        """
        if progress_callback:
            progress_callback("Scalanie stron w siatkę...")
        
        num_pages = len(selected_indices)
        total_cells = rows * cols
        
        # Poprawka: powielaj tylko jeśli jedna strona, przy wielu nie powielaj żadnej
        if num_pages == 1:
            source_pages = [selected_indices[0]] * total_cells
        else:
            source_pages = [selected_indices[i] if i < num_pages else None for i in range(total_cells)]
        
        # Oblicz rozmiar komórki
        if cols == 1:
            cell_width = sheet_width_pt - margin_left_pt - margin_right_pt
        else:
            cell_width = (sheet_width_pt - margin_left_pt - margin_right_pt - (cols - 1) * spacing_x_pt) / cols
        if rows == 1:
            cell_height = sheet_height_pt - margin_top_pt - margin_bottom_pt
        else:
            cell_height = (sheet_height_pt - margin_top_pt - margin_bottom_pt - (rows - 1) * spacing_y_pt) / rows
        
        new_page = pdf_document.new_page(width=sheet_width_pt, height=sheet_height_pt)
        
        if progressbar_callback:
            progressbar_callback(0, len(source_pages))
        
        PT_TO_INCH = 1 / 72
        
        for idx, src_idx in enumerate(source_pages):
            row = idx // cols
            col = idx % cols
            if row >= rows:
                break
            if src_idx is None:
                continue  # Pusta komórka
            
            x = margin_left_pt + col * (cell_width + spacing_x_pt)
            y = margin_top_pt + row * (cell_height + spacing_y_pt)
            
            src_page = pdf_document[src_idx]
            page_rect = src_page.rect
            page_w = page_rect.width
            page_h = page_rect.height
            
            # Automatyczny obrót jeśli orientacja strony nie pasuje do komórki
            page_landscape = page_w > page_h
            cell_landscape = cell_width > cell_height
            rotate = 0
            if page_landscape != cell_landscape:
                rotate = 90  # Obróć o 90 stopni
            
            # Skala renderowania: bitmapa ma dokładnie tyle pikseli, ile wynosi rozmiar komórki w punktach * DPI / 72
            bitmap_w = int(round(cell_width * target_dpi * PT_TO_INCH))
            bitmap_h = int(round(cell_height * target_dpi * PT_TO_INCH))
            
            if rotate == 90:
                scale_x = bitmap_w / page_h
                scale_y = bitmap_h / page_w
            else:
                scale_x = bitmap_w / page_w
                scale_y = bitmap_h / page_h
            
            # Renderuj bitmapę w bardzo wysokiej rozdzielczości, z ewentualnym obrotem
            pix = src_page.get_pixmap(matrix=fitz.Matrix(scale_x, scale_y).prerotate(rotate), alpha=False)
            img_bytes = pix.tobytes("png")
            rect = fitz.Rect(x, y, x + cell_width, y + cell_height)
            new_page.insert_image(rect, stream=img_bytes)
            
            if progressbar_callback:
                progressbar_callback(idx + 1, len(source_pages))
    
    # ============================================================================
    # WYKRYWANIE I USUWANIE PUSTYCH STRON
    # ============================================================================
    
    def detect_empty_pages(self, pdf_document,
                          progress_callback: Optional[Callable[[str], None]] = None,
                          progressbar_callback: Optional[Callable[[int, int], None]] = None) -> list:
        """
        Wykrywa puste strony w dokumencie PDF.
        Pusta strona = brak tekstu, rysunków i obrazów.
        
        Args:
            pdf_document: Dokument fitz (PyMuPDF)
            progress_callback: Funkcja callback dla statusu
            progressbar_callback: Funkcja callback dla paska postępu
            
        Returns:
            Lista indeksów pustych stron
        """
        if progress_callback:
            progress_callback("Skanowanie pustych stron...")
        
        empty_pages = []
        total_pages = len(pdf_document)
        
        if progressbar_callback:
            progressbar_callback(0, total_pages)
        
        for page_index in range(total_pages):
            page = pdf_document[page_index]
            text = page.get_text().strip()
            
            # Sprawdź czy strona ma tekst
            if not text:
                # Sprawdź czy są jakieś rysunki/obrazy
                drawings = page.get_drawings()
                images = page.get_images()
                
                # Jeśli brak tekstu, rysunków i obrazów - strona jest pusta
                if not drawings and not images:
                    empty_pages.append(page_index)
            
            if progressbar_callback:
                progressbar_callback(page_index + 1, total_pages)
        
        return empty_pages
    
    def remove_empty_pages(self, pdf_document, empty_pages: list,
                          progress_callback: Optional[Callable[[str], None]] = None,
                          progressbar_callback: Optional[Callable[[int, int], None]] = None) -> int:
        """
        Usuwa puste strony z dokumentu PDF.
        
        Args:
            pdf_document: Dokument fitz (PyMuPDF)
            empty_pages: Lista indeksów pustych stron
            progress_callback: Funkcja callback dla statusu
            progressbar_callback: Funkcja callback dla paska postępu
            
        Returns:
            Liczba usuniętych stron
        """
        if progress_callback:
            progress_callback("Usuwanie pustych stron...")
        
        if progressbar_callback:
            progressbar_callback(0, len(empty_pages))
        
        # Usuń puste strony (od końca, żeby nie zmienić indeksów)
        for idx, page_index in enumerate(reversed(empty_pages)):
            pdf_document.delete_page(page_index)
            if progressbar_callback:
                progressbar_callback(idx + 1, len(empty_pages))
        
        return len(empty_pages)
    
    # ============================================================================
    # ODWRACANIE KOLEJNOŚCI STRON
    # ============================================================================
    
    def reverse_pages(self, pdf_document,
                     progress_callback: Optional[Callable[[str], None]] = None,
                     progressbar_callback: Optional[Callable[[int, int], None]] = None):
        """
        Odwraca kolejność wszystkich stron w dokumencie PDF.
        Zwraca nowy dokument z odwróconą kolejnością stron.
        
        Args:
            pdf_document: Dokument fitz (PyMuPDF)
            progress_callback: Funkcja callback dla statusu
            progressbar_callback: Funkcja callback dla paska postępu
            
        Returns:
            Nowy dokument fitz z odwróconą kolejnością stron
        """
        if progress_callback:
            progress_callback("Odwracanie kolejności stron...")
        
        page_count = len(pdf_document)
        new_doc = fitz.open()
        
        if progressbar_callback:
            progressbar_callback(0, page_count)
        
        for idx, i in enumerate(range(page_count - 1, -1, -1)):
            new_doc.insert_pdf(pdf_document, from_page=i, to_page=i)
            if progressbar_callback:
                progressbar_callback(idx + 1, page_count)
        
        return new_doc
    
    # ============================================================================
    # EKSPORT STRON DO PDF
    # ============================================================================
    
    def extract_pages_to_single_pdf(self, pdf_document, selected_indices: list, 
                                    output_filepath: str,
                                    progress_callback: Optional[Callable[[str], None]] = None,
                                    progressbar_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        """
        Ekstraktuje wybrane strony do jednego pliku PDF.
        
        Args:
            pdf_document: Dokument fitz (PyMuPDF)
            selected_indices: Lista indeksów stron do ekstraktowania
            output_filepath: Ścieżka do pliku wyjściowego
            progress_callback: Funkcja callback dla statusu
            progressbar_callback: Funkcja callback dla paska postępu
            
        Returns:
            True jeśli sukces, False w przeciwnym razie
        """
        if progress_callback:
            progress_callback("Ekstrakcja stron do PDF...")
        
        try:
            # Użyj istniejącej metody export_pages_to_pdf
            return self.export_pages_to_pdf(pdf_document, selected_indices, output_filepath,
                                           progress_callback, progressbar_callback)
        except Exception as e:
            if progress_callback:
                progress_callback(f"BŁĄD: {e}")
            return False
    
    def extract_pages_to_separate_pdfs(self, pdf_document, selected_indices: list,
                                      output_dir: str, base_filename: str,
                                      progress_callback: Optional[Callable[[str], None]] = None,
                                      progressbar_callback: Optional[Callable[[int, int], None]] = None) -> int:
        """
        Ekstraktuje każdą stronę do osobnego pliku PDF.
        
        Args:
            pdf_document: Dokument fitz (PyMuPDF)
            selected_indices: Lista indeksów stron do ekstraktowania
            output_dir: Katalog wyjściowy
            base_filename: Nazwa bazowa plików
            progress_callback: Funkcja callback dla statusu
            progressbar_callback: Funkcja callback dla paska postępu
            
        Returns:
            Liczba wyekstraktowanych plików
        """
        if progress_callback:
            progress_callback("Ekstrakcja stron do osobnych plików...")
        
        exported_count = 0
        
        if progressbar_callback:
            progressbar_callback(0, len(selected_indices))
        
        for idx, page_index in enumerate(selected_indices):
            # Generuj nazwę pliku
            single_page_range = str(page_index + 1)
            output_path = generate_unique_export_filename(
                output_dir, base_filename, single_page_range, "pdf"
            )
            
            # Ekstraktuj pojedynczą stronę
            success = self.export_pages_to_pdf(pdf_document, [page_index], output_path)
            if success:
                exported_count += 1
            
            if progressbar_callback:
                progressbar_callback(idx + 1, len(selected_indices))
        
        return exported_count
