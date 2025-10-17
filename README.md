# GRYF PDF Editor

## Opis

GRYF PDF Editor to zaawansowana aplikacja do edycji plików PDF z pełnym zestawem narzędzi do manipulacji stronami, numeracji, kadrowania, scalania i wielu innych operacji.

## 🆕 Refaktoryzacja (v5.6.0)

Aplikacja została zrefaktoryzowana w celu poprawy struktury kodu:

- ✅ **Modularna struktura** - kod podzielony na pakiety utils/, core/, gui/
- ✅ **Lepsze zarządzanie** - łatwiejsze utrzymanie i rozwój
- ✅ **Pełna kompatybilność** - wszystkie funkcje działają bez zmian
- ✅ **Dokumentacja** - szczegółowe opisy modułów i API

**Zobacz dokumentację:**
- [STRUCTURE.md](STRUCTURE.md) - szczegółowa dokumentacja struktury
- [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) - podsumowanie refaktoryzacji

## Funkcjonalność

### Podstawowe operacje:
- ✅ Otwieranie i zapisywanie plików PDF
- ✅ Wyświetlanie miniaturek w siatce
- ✅ Zaznaczanie wielu stron
- ✅ System cofania/ponawiania (Undo/Redo)
- ✅ Drag & Drop plików PDF i obrazów

### Edycja stron:
- ✅ Obracanie stron (90°, -90°, 180°)
- ✅ Usuwanie zaznaczonych stron
- ✅ Kopiowanie/Wycinanie/Wklejanie stron
- ✅ Duplikowanie stron
- ✅ Zamiana stron miejscami
- ✅ Wstawianie pustych stron
- ✅ Odwracanie kolejności stron
- ✅ Usuwanie pustych stron

### Zaawansowane operacje:
- ✅ **Kadrowanie stron** - przycinanie marginesów
- ✅ **Zmiana rozmiaru** - dopasowanie do formatu (A4, A3, Letter, etc.)
- ✅ **Numeracja stron** - różne formaty i pozycje
- ✅ **Przesunięcie zawartości** - przesuwanie elementów na stronie
- ✅ **Scalanie PDF** - łączenie wielu plików
- ✅ **Scalanie do siatki** - wiele stron na jednej
- ✅ **Import/Eksport obrazów** - konwersja PDF ↔ obrazy

### System makr:
- ✅ Nagrywanie makr (sekwencji operacji)
- ✅ Odtwarzanie makr
- ✅ Zarządzanie listą makr
- ✅ Edycja i usuwanie makr

### Narzędzia:
- ✅ **Analiza PDF** - informacje o dokumencie
- ✅ **Hasła PDF** - ustawianie i usuwanie haseł
- ✅ **Detekcja orientacji** - automatyczne wykrywanie orientacji stron
- ✅ **Profile ustawień** - zapisywanie preferencji

### Interfejs:
- ✅ Zoom miniatur (2x-8x kolumn)
- ✅ Menu kontekstowe
- ✅ Skróty klawiszowe
- ✅ Tooltips
- ✅ Pasek postępu dla długich operacji

## Wymagania

```bash
pip install PyMuPDF Pillow pypdf tkinterdnd2
```

### Szczegółowe zależności:
- **Python 3.8+**
- **PyMuPDF (fitz)** - renderowanie i analiza PDF
- **Pillow (PIL)** - przetwarzanie obrazów
- **pypdf** - operacje na PDF
- **tkinter** - interfejs graficzny (zwykle wbudowany w Python)
- **tkinterdnd2** - obsługa Drag & Drop

## Instalacja

### Windows
```bash
pip install PyMuPDF Pillow pypdf tkinterdnd2
python PDFEditor.py
```

### Linux
```bash
sudo apt-get install python3-tk
pip install PyMuPDF Pillow pypdf tkinterdnd2
python3 PDFEditor.py
```

### macOS
```bash
brew install python-tk
pip3 install PyMuPDF Pillow pypdf tkinterdnd2
python3 PDFEditor.py
```

## Struktura Projektu

```
PDF_Editor_Qt/
├── PDFEditor.py              # Główna aplikacja
├── core/                     # Moduły podstawowe
│   ├── __init__.py
│   └── preferences_manager.py
├── utils/                    # Narzędzia i funkcje pomocnicze
│   ├── __init__.py
│   ├── constants.py          # Stałe aplikacji
│   ├── helpers.py            # Funkcje pomocnicze
│   ├── messagebox.py         # Okna dialogowe
│   └── tooltip.py            # Tooltips
├── gui/                      # Komponenty GUI (zarezerwowane)
├── icons/                    # Ikony aplikacji
├── STRUCTURE.md              # Dokumentacja struktury
├── REFACTORING_SUMMARY.md    # Podsumowanie refaktoryzacji
└── validate_structure.py     # Skrypt walidacji
```

## Użycie

### Podstawowe operacje

1. **Otwórz plik PDF**
   - Kliknij ikonę "Otwórz" lub Ctrl+O
   - Lub przeciągnij plik PDF na okno aplikacji

2. **Zaznacz strony**
   - Kliknij na miniaturę - zaznacz pojedynczą stronę
   - Shift+Klik - zaznacz zakres
   - Ctrl+A - zaznacz wszystkie
   - Spacja - przełącz zaznaczenie aktywnej strony

3. **Edytuj strony**
   - Użyj przycisków na pasku narzędzi
   - Lub wybierz opcję z menu
   - Lub użyj skrótu klawiszowego

4. **Zapisz zmiany**
   - Kliknij ikonę "Zapisz" lub Ctrl+S

### Skróty klawiszowe

**Plik:**
- `Ctrl+O` - Otwórz PDF
- `Ctrl+S` - Zapisz PDF
- `Ctrl+W` - Zamknij PDF
- `Ctrl+Q` - Wyjdź z programu

**Edycja:**
- `Ctrl+Z` - Cofnij
- `Ctrl+Y` - Ponów
- `Delete` - Usuń zaznaczone strony
- `Ctrl+C` - Kopiuj strony
- `Ctrl+X` - Wytnij strony
- `Ctrl+V` - Wklej po aktywnej stronie
- `Ctrl+D` - Duplikuj stronę

**Zaznaczanie:**
- `Ctrl+A` - Zaznacz wszystkie
- `Ctrl+Shift+A` - Odznacz wszystkie
- `Spacja` - Przełącz zaznaczenie
- `Ctrl+E` - Zaznacz strony parzyste
- `Ctrl+Shift+E` - Zaznacz strony nieparzyste

**Nawigacja:**
- `Strzałki` - Przesuwanie fokusu
- `Home` - Pierwsza strona
- `End` - Ostatnia strona
- `Page Up/Down` - Przewijanie

**Modyfikacje:**
- `Ctrl+L` - Obróć w lewo
- `Ctrl+R` - Obróć w prawo
- `Ctrl+Insert` - Wstaw pustą stronę przed
- `Insert` - Wstaw pustą stronę po

**Widok:**
- `Ctrl++` - Powiększ miniatury
- `Ctrl+-` - Pomniejsz miniatury

## Walidacja struktury

Sprawdź poprawność struktury projektu:

```bash
python3 validate_structure.py
```

Wynik:
```
============================================================
Module Structure: ✓ PASS
Syntax Check:     ✓ PASS  
Import Check:     ✓ PASS
============================================================
✓ All checks passed!
```

## Dla programistów

### Importowanie modułów

```python
# Import stałych i funkcji
from utils import (
    BASE_DIR, PROGRAM_TITLE, PROGRAM_VERSION,
    mm2pt, validate_float_range, 
    custom_messagebox, Tooltip
)

# Import managera preferencji
from core import PreferencesManager

# Przykład użycia
prefs = PreferencesManager()
last_file = prefs.get('last_opened_file', '')
prefs.set('last_opened_file', '/path/to/file.pdf')
```

### Rozwój

1. **Moduły utils/** - Dodawanie nowych funkcji pomocniczych
2. **Moduły core/** - Logika biznesowa i operacje PDF
3. **Moduły gui/** - Komponenty interfejsu użytkownika

### Testy

```bash
# Walidacja składni
python3 -m py_compile PDFEditor.py utils/*.py core/*.py

# Walidacja struktury
python3 validate_structure.py
```

## Znane problemy

- Niektóre bardzo duże pliki PDF mogą powodować wolniejsze renderowanie miniatur
- Import bardzo dużych obrazów (>20MB) może być czasochłonny
- Obsługa Drag & Drop wymaga biblioteki tkinterdnd2

## Plany rozwoju

### Faza 2 - Dialogi w osobnych plikach
- Przeniesienie każdego dialogu do gui/dialogs/
- Redukcja głównego pliku o ~2000 linii

### Faza 3 - PDF Tools
- Wydzielenie operacji PDF do core/pdf_tools.py
- Metody: kadrowanie, zmiana rozmiaru, numeracja

### Faza 4 - Macro Manager
- System makr w core/macro_manager.py
- Lepsza obsługa i edycja makr

### Faza 5 - Main Window
- GUI w gui/main_window.py
- Finalna redukcja do ~2000 linii

## Licencja

Program stanowi wyłączną własność intelektualną **Centrum Graficznego Gryf sp. z o.o.**

Wszelkie prawa zastrzeżone. Kopiowanie, modyfikowanie oraz rozpowszechnianie programu bez pisemnej zgody autora jest zabronione.

## Autor

© **Centrum Graficzne GRYF sp. z o.o.**

## Wersja

**5.6.0** - Refaktoryzacja struktury kodu (2025-10-17)

---

**Dokumentacja techniczna:**
- [STRUCTURE.md](STRUCTURE.md) - Szczegółowa dokumentacja struktury modułów
- [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) - Podsumowanie zmian w refaktoryzacji
