"""Preferences Manager - manages application preferences"""
import os
import json
from utils.constants import BASE_DIR

class PreferencesManager:
    """Zarządza preferencjami programu i dialogów, zapisuje/odczytuje z pliku preferences.txt"""
    
    def __init__(self, filepath="preferences.txt"):
        self.filepath = os.path.join(BASE_DIR, filepath)
        self.preferences = {}
        self.defaults = {
            # Preferencje globalne
            'default_save_path': '',
            'default_read_path': '',
            'last_open_path': '',
            'last_save_path': '',
            'thumbnail_quality': 'Średnia',
            'confirm_delete': 'False',
            'export_image_dpi': '300',  # DPI dla eksportu obrazów (150, 300, 600)
            
            # PageCropResizeDialog
            'PageCropResizeDialog.crop_mode': 'nocrop',
            'PageCropResizeDialog.margin_top': '10',
            'PageCropResizeDialog.margin_bottom': '10',
            'PageCropResizeDialog.margin_left': '10',
            'PageCropResizeDialog.margin_right': '10',
            'PageCropResizeDialog.resize_mode': 'noresize',
            'PageCropResizeDialog.target_format': 'A4',
            'PageCropResizeDialog.custom_width': '',
            'PageCropResizeDialog.custom_height': '',
            'PageCropResizeDialog.position_mode': 'center',
            'PageCropResizeDialog.offset_x': '0',
            'PageCropResizeDialog.offset_y': '0',
            
            # PageNumberingDialog
            'PageNumberingDialog.margin_left': '35',
            'PageNumberingDialog.margin_right': '25',
            'PageNumberingDialog.margin_vertical_mm': '15',
            'PageNumberingDialog.vertical_pos': 'dol',
            'PageNumberingDialog.alignment': 'prawa',
            'PageNumberingDialog.mode': 'normalna',
            'PageNumberingDialog.start_page': '1',
            'PageNumberingDialog.start_number': '1',
            'PageNumberingDialog.font_name': 'Times-Roman',
            'PageNumberingDialog.font_size': '12',
            'PageNumberingDialog.mirror_margins': 'False',
            'PageNumberingDialog.format_type': 'simple',
            
            # ShiftContentDialog
            'ShiftContentDialog.x_direction': 'P',
            'ShiftContentDialog.y_direction': 'G',
            'ShiftContentDialog.x_value': '0',
            'ShiftContentDialog.y_value': '0',
            
            # PageNumberMarginDialog
            'PageNumberMarginDialog.top_margin': '20',
            'PageNumberMarginDialog.bottom_margin': '20',
            
            # MergePageGridDialog
            'MergePageGridDialog.sheet_format': 'A4',
            'MergePageGridDialog.orientation': 'Pionowa',
            'MergePageGridDialog.margin_top_mm': '5',
            'MergePageGridDialog.margin_bottom_mm': '5',
            'MergePageGridDialog.margin_left_mm': '5',
            'MergePageGridDialog.margin_right_mm': '5',
            'MergePageGridDialog.spacing_x_mm': '10',
            'MergePageGridDialog.spacing_y_mm': '10',
            'MergePageGridDialog.dpi_var': '300',
            
            # EnhancedPageRangeDialog
            'EnhancedPageRangeDialog.last_range': '',
            
            # ImageImportSettingsDialog
            'ImageImportSettingsDialog.target_format': 'A4',
            'ImageImportSettingsDialog.orientation': 'auto',
            'ImageImportSettingsDialog.margin_mm': '10',
            'ImageImportSettingsDialog.scaling_mode': 'DOPASUJ',
            'ImageImportSettingsDialog.alignment_mode': 'SRODEK',
            'ImageImportSettingsDialog.scale_factor': '100.0',
            'ImageImportSettingsDialog.page_orientation': 'PIONOWO',
            'ImageImportSettingsDialog.custom_width': '',
            'ImageImportSettingsDialog.custom_height': '',
            'ImageImportSettingsDialog.keep_ratio': 'True',
            
            # Color detection settings
            'color_detect_threshold': '5',
            'color_detect_samples': '300',
            'color_detect_scale': '0.2',
        }
        self.load_preferences()
    
    def load_preferences(self):
        """Wczytuje preferencje z pliku"""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and '=' in line:
                            key, value = line.split('=', 1)
                            self.preferences[key.strip()] = value.strip()
            except Exception as e:
                print(f"Błąd wczytywania preferencji: {e}")
        # Wypełnij brakujące wartości domyślnymi
        for key, value in self.defaults.items():
            if key not in self.preferences:
                self.preferences[key] = value
    
    def save_preferences(self):
        """Zapisuje preferencje do pliku"""
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                for key, value in sorted(self.preferences.items()):
                    f.write(f"{key}={value}\n")
        except Exception as e:
            print(f"Błąd zapisywania preferencji: {e}")
    
    def get(self, key, default=None):
        """Pobiera wartość preferencji"""
        return self.preferences.get(key, default if default is not None else self.defaults.get(key, ''))
    
    def set(self, key, value):
        """Ustawia wartość preferencji"""
        self.preferences[key] = str(value)
        self.save_preferences()
    
    def reset_to_defaults(self):
        """Przywraca wszystkie preferencje do wartości domyślnych"""
        self.preferences = self.defaults.copy()
        self.save_preferences()
    
    def reset_dialog_defaults(self, dialog_name):
        """Przywraca wartości domyślne dla konkretnego dialogu"""
        for key in list(self.preferences.keys()):
            if key.startswith(f"{dialog_name}."):
                if key in self.defaults:
                    self.preferences[key] = self.defaults[key]
        self.save_preferences()
    
    def get_profiles(self, profile_key):
        """Pobiera profile z preferencji jako słownik"""
        profiles_json = self.get(profile_key, '{}')
        try:
            return json.loads(profiles_json)
        except:
            return {}
    
    def save_profiles(self, profile_key, profiles_dict):
        """Zapisuje profile do preferencji jako JSON"""
        profiles_json = json.dumps(profiles_dict, ensure_ascii=False)
        self.set(profile_key, profiles_json)
