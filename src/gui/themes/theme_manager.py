"""
Theme manager for the Video Downloader application.
Provides functionality to switch between dark and light themes.
"""

from .dark_theme import DarkTheme
from .light_theme import LightTheme

class ThemeManager:
    """
    Manages application themes and provides methods to apply them.
    """
    
    def __init__(self, main_window, app_settings):
        """
        Initialize the theme manager.
        
        Args:
            main_window: The main window instance to apply themes to
            app_settings: Dictionary containing application settings
        """
        self.main_window = main_window
        self.app_settings = app_settings
        self.components = []
        
    def register_component(self, component):
        """
        Register a component for theme updates.
        
        Args:
            component: Component to register
        """
        self.components.append(component)
        
    def apply_theme(self):
        """Apply the current theme based on app settings."""
        if self.app_settings["dark_theme"]:
            self.apply_dark_theme()
        else:
            self.apply_light_theme()
            
    def toggle_theme(self):
        """Toggle between dark and light themes."""
        self.app_settings["dark_theme"] = not self.app_settings["dark_theme"]
        self.apply_theme()
        return self.app_settings["dark_theme"]
            
    def apply_dark_theme(self):
        """Apply dark theme to all components."""
        # Apply the main window style
        self.main_window.setStyleSheet(DarkTheme.get_main_style())
        
        # Apply component-specific styles
        for component in self.components:
            if hasattr(component, 'apply_theme'):
                component.apply_theme(True)
                
        # Apply combo box style to format selector if it exists
        if hasattr(self.main_window, 'format_selector') and hasattr(self.main_window.format_selector, 'format_combo'):
            self.main_window.format_selector.format_combo.setStyleSheet(DarkTheme.get_combo_box_style())
            
        # Apply menu bar style if it exists
        if hasattr(self.main_window, 'menu_bar'):
            self.main_window.menu_bar.apply_theme_styles(True)
            
    def apply_light_theme(self):
        """Apply light theme to all components."""
        # Apply the main window style
        self.main_window.setStyleSheet(LightTheme.get_main_style())
        
        # Apply component-specific styles
        for component in self.components:
            if hasattr(component, 'apply_theme'):
                component.apply_theme(False)
                
        # Apply combo box style to format selector if it exists
        if hasattr(self.main_window, 'format_selector') and hasattr(self.main_window.format_selector, 'format_combo'):
            self.main_window.format_selector.format_combo.setStyleSheet(LightTheme.get_combo_box_style())
            
        # Apply menu bar style if it exists
        if hasattr(self.main_window, 'menu_bar'):
            self.main_window.menu_bar.apply_theme_styles(False)
            
    def get_dialog_style(self):
        """Get the appropriate dialog style based on current theme."""
        if self.app_settings["dark_theme"]:
            return DarkTheme.get_dialog_style()
        else:
            return LightTheme.get_dialog_style() 