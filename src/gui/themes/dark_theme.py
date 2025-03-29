"""
Dark theme styling for the Video Downloader application.
"""

class DarkTheme:
    """Provides dark theme styling for the application."""
    
    @staticmethod
    def get_main_style():
        """Get the main application style for dark theme."""
        return """
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 10pt;
                color: #ffffff;
            }
            QLabel {
                font-size: 10pt;
                color: #ffffff;
            }
            QPushButton {
                font-size: 10pt;
                padding: 8px 12px;
                background-color: #424242;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4f4f4f;
                border: 1px solid #666666;
            }
            QPushButton:pressed {
                background-color: #383838;
            }
            QPushButton:disabled {
                background-color: #353535;
                color: #777777;
                border: 1px solid #444444;
            }
            QPushButton:default {
                background-color: #0078d7;
                color: white;
                border: 1px solid #0067b8;
            }
            QPushButton:default:hover {
                background-color: #1889e0;
            }
            QPushButton:default:pressed {
                background-color: #006cc1;
            }
            QRadioButton {
                font-size: 10pt;
                color: #ffffff;
                spacing: 8px;
                min-height: 24px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
            QProgressBar {
                font-size: 10pt;
                text-align: center;
                background-color: #323232;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 2px;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #0078d7;
                border-radius: 3px;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #555555;
                border-radius: 4px;
                background-color: #2a2a2a;
                color: #ffffff;
            }
            QLineEdit:focus {
                border: 1px solid #0078d7;
            }
            QFrame[frameShape="4"] { /* HLine */
                color: #555555;
                max-height: 1px;
                margin: 5px 0;
            }
        """
    
    @staticmethod
    def get_combo_box_style():
        """Get the combo box style for dark theme."""
        return """
            QComboBox {
                padding: 4px 10px;
                border: 1px solid #555555;
                border-radius: 4px;
                background-color: #2a2a2a;
                color: #ffffff;
                selection-background-color: #0078d7;
                font-size: 10pt;
                text-align: left;
                min-height: 20px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 30px;
                border-left: 1px solid #555555;
                background-color: #333333;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
                background-color: #0078d7;
            }
            QComboBox QAbstractItemView {
                background-color: #2a2a2a;
                border: 1px solid #555555;
                selection-background-color: #0078d7;
                selection-color: #ffffff;
                padding: 6px;
            }
        """
    
    @staticmethod
    def get_menu_bar_style():
        """Get the menu bar style for dark theme."""
        return """
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
        """
    
    @staticmethod
    def get_dialog_style():
        """Get the dialog style for dark theme."""
        return """
            QDialog {
                background-color: #333333;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 10pt;
            }
            QPushButton {
                background-color: #424242;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #4f4f4f;
            }
            QListWidget {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #0078d7;
            }
        """ 