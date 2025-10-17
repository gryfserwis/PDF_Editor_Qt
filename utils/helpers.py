"""Helper utility functions"""
import os
import sys
from datetime import datetime
from .constants import MM_TO_POINTS

def mm2pt(mm):
    """Convert millimeters to points"""
    return float(mm) * MM_TO_POINTS

def validate_float_range(value, minval, maxval):
    """Validate if a value is a float within a given range"""
    if not value:
        return True
    try:
        v = float(value.replace(",", "."))
        return minval <= v <= maxval
    except Exception:
        return False

def generate_unique_export_filename(directory, base_name, page_range, extension):
    """
    Generuje unikalną nazwę pliku w formacie:
    "Eksport z pliku [base_name]_[page_range]_[date]_[time].[extension]"
    Jeśli plik istnieje, dodaje (1), (2), (3) itd.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"Eksport_{page_range}_{timestamp}.{extension}"
    filepath = os.path.join(directory, filename)
    
    # Jeśli plik istnieje, dodaj numer
    if os.path.exists(filepath):
        counter = 1
        base_without_ext = f"Eksport_{page_range}_{timestamp}"
        while True:
            filename = f"{base_without_ext} ({counter}).{extension}"
            filepath = os.path.join(directory, filename)
            if not os.path.exists(filepath):
                break
            counter += 1
    
    return filepath
        
def resource_path(relative_path):
    """
    Tworzy poprawną ścieżkę do zasobów (logo, ikony itp.).
    Działa w trybie deweloperskim i po spakowaniu PyInstallerem.
    """
    try:
        # Aplikacja spakowana (PyInstaller --onefile)
        base_path = sys._MEIPASS
    except AttributeError:
        # Tryb deweloperski (po prostu katalog skryptu)
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    return os.path.join(base_path, relative_path)
