"""Dialog classes for PDF Editor"""

from gui.dialogs.preferences_dialog import PreferencesDialog
from gui.dialogs.page_crop_resize_dialog import PageCropResizeDialog
from gui.dialogs.page_numbering_dialog import PageNumberingDialog
from gui.dialogs.page_number_margin_dialog import PageNumberMarginDialog
from gui.dialogs.shift_content_dialog import ShiftContentDialog
from gui.dialogs.image_import_settings_dialog import ImageImportSettingsDialog
from gui.dialogs.enhanced_page_range_dialog import EnhancedPageRangeDialog
from gui.dialogs.merge_page_grid_dialog import MergePageGridDialog
from gui.dialogs.macro_edit_dialog import MacroEditDialog
from gui.dialogs.macro_recording_dialog import MacroRecordingDialog
from gui.dialogs.macros_list_dialog import MacrosListDialog
from gui.dialogs.merge_pdf_dialog import MergePDFDialog
from gui.dialogs.pdf_analysis_dialog import PDFAnalysisDialog

__all__ = [
    'PreferencesDialog',
    'PageCropResizeDialog',
    'PageNumberingDialog',
    'PageNumberMarginDialog',
    'ShiftContentDialog',
    'ImageImportSettingsDialog',
    'EnhancedPageRangeDialog',
    'MergePageGridDialog',
    'MacroEditDialog',
    'MacroRecordingDialog',
    'MacrosListDialog',
    'MergePDFDialog',
    'PDFAnalysisDialog',
]
