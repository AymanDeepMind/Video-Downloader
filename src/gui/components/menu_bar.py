"""
Menu bar component for the Video Downloader application.
Handles the application menu bar with tools, settings, and help options.
"""

import webbrowser
import os
import subprocess
import sys
from PyQt5.QtWidgets import QMenuBar, QAction, QMenu
from PyQt5.QtCore import pyqtSignal

class MenuBarComponent(QMenuBar):
    """
    Component for the application menu bar.
    Provides menus for tools, settings, and help.
    """
    
    # Signals
    theme_toggle_triggered = pyqtSignal()
    default_format_triggered = pyqtSignal()
    auto_fetch_toggled = pyqtSignal(bool)
    remember_directory_toggled = pyqtSignal(bool)
    view_logs_triggered = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize the menu bar component."""
        super().__init__(parent)
        
        # App settings - will be updated by the main window
        self.app_settings = {
            "dark_theme": True,
            "auto_fetch": False,
            "remember_directory": True
        }
        
        self._setup_menus()
        
    def _setup_menus(self):
        """Set up the menu structure."""
        # Tools Menu
        self.tools_menu = self.addMenu("&Tools")
        
        # Add a placeholder or remove Tools menu if empty
        if not self.tools_menu.actions():
             # Option 1: Add a placeholder action
             placeholder_action = QAction("(No tools yet)", self)
             placeholder_action.setEnabled(False)
             self.tools_menu.addAction(placeholder_action)
             # Option 2: Remove the empty Tools menu
             # self.removeAction(self.tools_menu.menuAction())
             # self.tools_menu = None # Set to None if removed
        
        # Settings Menu
        self.settings_menu = self.addMenu("&Settings")
        
        # Default Download Format
        self.default_format_action = QAction("Default Download &Format", self)
        self.default_format_action.setStatusTip("Set the default download format")
        self.default_format_action.triggered.connect(self._on_default_format_triggered)
        self.settings_menu.addAction(self.default_format_action)
        
        # Light/Dark Toggle
        self.theme_toggle_action = QAction("Switch to &Light Theme", self)
        self.theme_toggle_action.setStatusTip("Switch between light and dark themes")
        self.theme_toggle_action.triggered.connect(self._on_theme_toggle_triggered)
        self.settings_menu.addAction(self.theme_toggle_action)
        
        self.settings_menu.addSeparator()
        
        # Auto-fetch toggle
        self.auto_fetch_action = QAction("&Auto-fetch formats when URL is entered", self)
        self.auto_fetch_action.setStatusTip("Automatically fetch formats when URL is entered")
        self.auto_fetch_action.setCheckable(True)
        self.auto_fetch_action.setChecked(self.app_settings["auto_fetch"])
        self.auto_fetch_action.triggered.connect(self._on_auto_fetch_toggled)
        self.settings_menu.addAction(self.auto_fetch_action)
        
        # Remember last directory toggle
        self.remember_dir_action = QAction("&Remember last used directory", self)
        self.remember_dir_action.setStatusTip("Remember the last used download directory")
        self.remember_dir_action.setCheckable(True)
        self.remember_dir_action.setChecked(self.app_settings["remember_directory"])
        self.remember_dir_action.triggered.connect(self._on_remember_directory_toggled)
        self.settings_menu.addAction(self.remember_dir_action)
        
        # Help Menu
        self.help_menu = self.addMenu("&Help")
        
        # View Logs
        self.logs_action = QAction("View &Logs", self)
        self.logs_action.setStatusTip("View application logs")
        self.logs_action.triggered.connect(self._on_view_logs_triggered)
        self.help_menu.addAction(self.logs_action)
        
        # Report Bug
        self.report_bug_action = QAction("&Report Bug", self)
        self.report_bug_action.setStatusTip("Report a bug on GitHub")
        self.report_bug_action.triggered.connect(self.report_bug)
        self.help_menu.addAction(self.report_bug_action)
        
        # About
        self.about_action = QAction("&About ADM Video Downloader", self)
        self.about_action.setStatusTip("View information about ADM Video Downloader")
        self.about_action.triggered.connect(self.show_about)
        self.help_menu.addAction(self.about_action)
        
    def update_settings(self, app_settings):
        """Update the menu with current app settings."""
        self.app_settings = app_settings
        
        # Update theme toggle action text
        self.theme_toggle_action.setText(
            "Switch to &Light Theme" if self.app_settings["dark_theme"] else "Switch to &Dark Theme"
        )
        
        # Update toggle states
        self.auto_fetch_action.setChecked(self.app_settings["auto_fetch"])
        self.remember_dir_action.setChecked(self.app_settings["remember_directory"])
        
    def apply_theme_styles(self, dark_theme=True):
        """Apply theme-specific styles to the menu bar."""
        if dark_theme:
            self.setStyleSheet("""
                QMenuBar {
                    background-color: #333333;
                    color: #ffffff;
                    padding: 2px;
                }
                QMenuBar::item {
                    background-color: #333333;
                    padding: 4px 10px;
                }
                QMenuBar::item:selected {
                    background-color: #0078d7;
                }
                QMenu {
                    background-color: #333333;
                    color: #ffffff;
                    border: 1px solid #555555;
                }
                QMenu::item {
                    padding: 5px 20px 5px 20px;
                }
                QMenu::item:selected {
                    background-color: #0078d7;
                }
                QMenu::item:disabled {
                    color: #777777;
                    background-color: #333333;
                }
                QMenu::separator {
                    height: 1px;
                    background-color: #555555;
                    margin: 5px 10px;
                }
            """)
        else:
            self.setStyleSheet("""
                QMenuBar {
                    background-color: #f5f5f5;
                    color: #333333;
                    padding: 2px;
                }
                QMenuBar::item {
                    background-color: #f5f5f5;
                    padding: 4px 10px;
                }
                QMenuBar::item:selected {
                    background-color: #0078d7;
                    color: #ffffff;
                }
                QMenu {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #cccccc;
                }
                QMenu::item {
                    padding: 5px 20px 5px 20px;
                }
                QMenu::item:selected {
                    background-color: #0078d7;
                    color: #ffffff;
                }
                QMenu::item:disabled {
                    color: #aaaaaa;
                    background-color: #ffffff;
                }
                QMenu::separator {
                    height: 1px;
                    background-color: #cccccc;
                    margin: 5px 10px;
                }
            """)
    
    # Signal handlers
    def _on_theme_toggle_triggered(self):
        """Handle theme toggle action."""
        self.theme_toggle_triggered.emit()
        
    def _on_default_format_triggered(self):
        """Handle default format action."""
        self.default_format_triggered.emit()
        
    def _on_auto_fetch_toggled(self, checked):
        """Handle auto-fetch toggle."""
        self.auto_fetch_toggled.emit(checked)
        
    def _on_remember_directory_toggled(self, checked):
        """Handle remember directory toggle."""
        self.remember_directory_toggled.emit(checked)
        
    def _on_view_logs_triggered(self):
        """Handle view logs action."""
        self.view_logs_triggered.emit()
        
    def report_bug(self):
        """Open the GitHub issues page to report a bug."""
        webbrowser.open("https://github.com/AymanDeepMind/Video-Downloader/issues")
        
    def show_about(self):
        """Show about information and navigate to GitHub repository."""
        webbrowser.open("https://github.com/AymanDeepMind/Video-Downloader") 