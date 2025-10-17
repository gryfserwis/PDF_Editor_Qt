"""Constants used throughout the application"""
import os
import sys
from datetime import date

# Definicja BASE_DIR i inne stałe
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_icon_folder():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, "icons")
    else:
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icons")

ICON_FOLDER = get_icon_folder()

# Focus highlight settings
FOCUS_HIGHLIGHT_COLOR = "#d3d3d3"
FOCUS_HIGHLIGHT_WIDTH = 6

# DANE PROGRAMU
PROGRAM_TITLE = "GRYF PDF Editor" 
PROGRAM_VERSION = "5.6.0"
PROGRAM_DATE = date.today().strftime("%Y-%m-%d")

# === STAŁE DLA A4 [w punktach PDF i mm] ===
A4_WIDTH_POINTS = 595.276 
A4_HEIGHT_POINTS = 841.89
MM_TO_POINTS = 72 / 25.4  # ~2.8346

# === STAŁE KOLORY NARZĘDZIOWE ===
BG_IMPORT = "#F0AD4E"
GRAY_FG = "#555555"

COPYRIGHT_INFO = (
    "Program stanowi wyłączną własność intelektualną Centrum Graficznego Gryf sp. z o.o.\n\n"
    "Wszelkie prawa zastrzeżone. Kopiowanie, modyfikowanie oraz rozpowszechnianie "
    "programu bez pisemnej zgody autora jest zabronione."
)

# === STAŁE KOLORYSTYKA DLA SPOJNOSCI ===
BG_PRIMARY = '#F0F0F0'  # Główne tło okien i dialogów
BG_SECONDARY = '#E0E0E0' # Tło paneli kontrolnych/przycisków
BG_BUTTON_DEFAULT = "#D0D0D0" # Domyślny kolor przycisków
FG_TEXT = "#444444" # Kolor tekstu na przyciskach
