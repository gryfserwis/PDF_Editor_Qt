# Struktura Projektu PDF Editor Qt

## Przegląd

Projekt został zrefaktoryzowany w celu poprawy organizacji kodu i ułatwienia utrzymania. Kod został podzielony na moduły według funkcjonalności.

## Struktura Katalogów

```
PDF_Editor_Qt/
├── PDFEditor.py           # Główny plik aplikacji
├── core/                  # Moduły podstawowe
│   ├── __init__.py
│   └── preferences_manager.py  # Zarządzanie preferencjami
├── utils/                 # Funkcje pomocnicze i narzędzia
│   ├── __init__.py
│   ├── constants.py       # Stałe aplikacji
│   ├── helpers.py         # Funkcje pomocnicze
│   ├── messagebox.py      # Niestandardowe okna dialogowe
│   └── tooltip.py         # Widget tooltip
└── gui/                   # (Zarezerwowane na przyszłe komponenty GUI)
```

## Moduły

### utils/

Moduł zawierający funkcje pomocnicze i stałe używane w całej aplikacji.

**constants.py**
- `BASE_DIR` - Katalog bazowy aplikacji
- `ICON_FOLDER` - Katalog z ikonami
- `PROGRAM_TITLE`, `PROGRAM_VERSION`, `PROGRAM_DATE` - Informacje o programie
- `A4_WIDTH_POINTS`, `A4_HEIGHT_POINTS`, `MM_TO_POINTS` - Stałe PDF
- `BG_PRIMARY`, `BG_SECONDARY`, `BG_BUTTON_DEFAULT`, `FG_TEXT` - Kolory UI
- `COPYRIGHT_INFO` - Informacja o prawach autorskich

**helpers.py**
- `mm2pt(mm)` - Konwersja milimetrów na punkty PDF
- `validate_float_range(value, minval, maxval)` - Walidacja zakresu wartości
- `generate_unique_export_filename(...)` - Generowanie unikalnych nazw plików
- `resource_path(relative_path)` - Obsługa ścieżek zasobów dla PyInstaller

**messagebox.py**
- `custom_messagebox(parent, title, message, typ)` - Niestandardowe okna dialogowe

**tooltip.py**
- `Tooltip` - Klasa do wyświetlania podpowiedzi dla widgetów

### core/

Moduł zawierający podstawową logikę aplikacji.

**preferences_manager.py**
- `PreferencesManager` - Zarządza preferencjami programu, zapisuje/odczytuje z pliku

### PDFEditor.py

Główny plik aplikacji zawierający:
- Wszystkie klasy dialogów (PreferencesDialog, PageCropResizeDialog, etc.)
- Klasę główną `SelectablePDFViewer`
- Logikę operacji na PDF
- System makr
- Obsługę interfejsu użytkownika

## Użycie

### Importowanie modułów

```python
# Import z modułu utils
from utils import (
    BASE_DIR, PROGRAM_TITLE, mm2pt, 
    validate_float_range, custom_messagebox, Tooltip
)

# Import z modułu core
from core import PreferencesManager
```

### Przykłady

```python
# Użycie stałych
from utils import A4_WIDTH_POINTS, MM_TO_POINTS

# Konwersja jednostek
from utils import mm2pt
points = mm2pt(210)  # Konwertuje 210mm na punkty

# Zarządzanie preferencjami
from core import PreferencesManager
prefs = PreferencesManager()
value = prefs.get('default_save_path', '')
prefs.set('last_open_path', '/path/to/file.pdf')
```

## Przyszłe Ulepszenia

Planowane są następujące refaktoryzacje:

1. **gui/dialogs/** - Przeniesienie klas dialogów do osobnych plików
   - preferences_dialog.py
   - page_crop_resize_dialog.py
   - page_numbering_dialog.py
   - etc.

2. **core/pdf_tools.py** - Operacje na PDF
   - Kadrowanie stron
   - Zmiana rozmiaru
   - Numeracja stron
   - Import/Eksport

3. **core/macro_manager.py** - Zarządzanie makrami
   - Nagrywanie makr
   - Odtwarzanie makr
   - Zarządzanie listą makr

4. **gui/main_window.py** - Główne okno aplikacji
   - Toolbar
   - Menu
   - Canvas
   - Obsługa zdarzeń

## Zgodność Wsteczna

Wszystkie funkcje i klasy zostały przeniesione bez zmian w logice działania. Istniejący kod powinien działać bez modyfikacji, ponieważ wszystkie symbole są nadal dostępne przez importy z nowych modułów.

## Testowanie

Po refaktoryzacji należy przetestować:
- [ ] Otwarcie pliku PDF
- [ ] Zapisywanie pliku PDF
- [ ] Wszystkie operacje edycji (kadrowanie, obracanie, numeracja, etc.)
- [ ] System makr
- [ ] Wszystkie okna dialogowe
- [ ] Preferencje i ich zapisywanie
- [ ] Import/Eksport obrazów
- [ ] Drag & Drop
