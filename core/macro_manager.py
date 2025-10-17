"""
Macro Manager Module

This module contains the MacroManager class responsible for managing macro recording,
storage, and execution logic. It is separated from GUI dialogs to maintain clean
architecture.

Author: GitHub Copilot
Date: 2025-10-17
"""


class MacroManager:
    """
    Manages macro recording, storage, and execution logic.
    
    This class handles:
    - Recording macro actions
    - Starting/stopping recording sessions
    - Retrieving macro data
    - Managing macro state
    
    Note: This class does NOT contain any GUI/tkinter code.
    All dialog classes remain in PDFEditor.py and use this manager.
    """
    
    def __init__(self, prefs_manager):
        """
        Initialize the MacroManager.
        
        Args:
            prefs_manager: PreferencesManager instance for storing macros
        """
        self.prefs_manager = prefs_manager
        self.recording = False
        self.current_actions = []
        self.recording_name = None
    
    def is_recording(self):
        """
        Check if macro recording is currently active.
        
        Returns:
            bool: True if recording, False otherwise
        """
        return self.recording
    
    def get_recording_name(self):
        """
        Get the name of the currently recording macro.
        
        Returns:
            str or None: Name of the macro being recorded, or None if not recording
        """
        return self.recording_name
    
    def get_current_actions(self):
        """
        Get the list of actions in the current recording.
        
        Returns:
            list: List of action dictionaries
        """
        return self.current_actions.copy()
    
    def get_actions_count(self):
        """
        Get the number of actions recorded in the current session.
        
        Returns:
            int: Number of recorded actions
        """
        return len(self.current_actions)
    
    def start_recording(self, macro_name):
        """
        Start recording a new macro.
        
        Args:
            macro_name (str): Name of the macro to record
            
        Returns:
            bool: True if recording started successfully, False if already recording
        """
        if self.recording:
            return False
        
        self.recording = True
        self.recording_name = macro_name
        self.current_actions = []
        return True
    
    def stop_recording(self):
        """
        Stop the current recording session.
        
        Returns:
            tuple: (macro_name, actions_list) or (None, None) if not recording
        """
        if not self.recording:
            return None, None
        
        macro_name = self.recording_name
        actions = self.current_actions.copy()
        
        self.recording = False
        self.recording_name = None
        self.current_actions = []
        
        return macro_name, actions
    
    def cancel_recording(self):
        """
        Cancel the current recording session without saving.
        """
        self.recording = False
        self.recording_name = None
        self.current_actions = []
    
    def record_action(self, action_name, **params):
        """
        Record an action to the current macro.
        
        Args:
            action_name (str): Name of the action
            **params: Action parameters as keyword arguments
            
        Returns:
            bool: True if action was recorded, False if not recording
        """
        if not self.recording:
            return False
        
        self.current_actions.append({
            'action': action_name,
            'params': params
        })
        return True
    
    def save_macro(self, macro_name, actions, shortcut=''):
        """
        Save a macro to preferences.
        
        Args:
            macro_name (str): Name of the macro
            actions (list): List of action dictionaries
            shortcut (str): Keyboard shortcut (optional)
            
        Returns:
            bool: True if saved successfully
        """
        macros = self.prefs_manager.get_profiles('macros')
        macros[macro_name] = {
            'actions': actions,
            'shortcut': shortcut
        }
        self.prefs_manager.save_profiles('macros', macros)
        return True
    
    def get_macro(self, macro_name):
        """
        Retrieve a macro by name.
        
        Args:
            macro_name (str): Name of the macro
            
        Returns:
            dict or None: Macro data (actions, shortcut) or None if not found
        """
        macros = self.prefs_manager.get_profiles('macros')
        return macros.get(macro_name)
    
    def get_all_macros(self):
        """
        Get all stored macros.
        
        Returns:
            dict: Dictionary of all macros {name: {actions, shortcut}}
        """
        return self.prefs_manager.get_profiles('macros')
    
    def delete_macro(self, macro_name):
        """
        Delete a macro.
        
        Args:
            macro_name (str): Name of the macro to delete
            
        Returns:
            bool: True if deleted, False if not found
        """
        macros = self.prefs_manager.get_profiles('macros')
        if macro_name in macros:
            del macros[macro_name]
            self.prefs_manager.save_profiles('macros', macros)
            return True
        return False
    
    def update_macro(self, macro_name, actions=None, shortcut=None):
        """
        Update an existing macro.
        
        Args:
            macro_name (str): Name of the macro
            actions (list, optional): New actions list
            shortcut (str, optional): New shortcut
            
        Returns:
            bool: True if updated, False if macro not found
        """
        macros = self.prefs_manager.get_profiles('macros')
        if macro_name not in macros:
            return False
        
        if actions is not None:
            macros[macro_name]['actions'] = actions
        if shortcut is not None:
            macros[macro_name]['shortcut'] = shortcut
        
        self.prefs_manager.save_profiles('macros', macros)
        return True
    
    def duplicate_macro(self, source_name, target_name):
        """
        Duplicate a macro with a new name.
        
        Args:
            source_name (str): Name of the macro to duplicate
            target_name (str): Name for the duplicate
            
        Returns:
            bool: True if duplicated, False if source not found or target exists
        """
        macros = self.prefs_manager.get_profiles('macros')
        
        if source_name not in macros or target_name in macros:
            return False
        
        macros[target_name] = macros[source_name].copy()
        self.prefs_manager.save_profiles('macros', macros)
        return True
    
    def macro_exists(self, macro_name):
        """
        Check if a macro with the given name exists.
        
        Args:
            macro_name (str): Name to check
            
        Returns:
            bool: True if macro exists
        """
        macros = self.prefs_manager.get_profiles('macros')
        return macro_name in macros
