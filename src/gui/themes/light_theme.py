"""
Light theme styling for the Video Downloader application.
"""

class LightTheme:
    """Provides light theme styling for the application."""
    
    @staticmethod
    def get_main_style():
        """Get the main application style for light theme."""
        return """
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 10pt;
                color: #333333;
                background-color: #f5f5f5;
            }
            QLabel {
                font-size: 10pt;
                color: #333333;
                background-color: transparent;
            }
            QPushButton {
                font-size: 10pt;
                padding: 8px 12px;
                background-color: #e0e0e0;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
                border: 1px solid #bbbbbb;
            }
            QPushButton:pressed {
                background-color: #c0c0c0;
            }
            QPushButton:disabled {
                background-color: #f0f0f0;
                color: #aaaaaa;
                border: 1px solid #dddddd;
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
                color: #333333;
                spacing: 8px;
                min-height: 24px;
                background-color: transparent;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
            QProgressBar {
                font-size: 10pt;
                text-align: center;
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 2px;
                color: #333333;
            }
            QProgressBar::chunk {
                background-color: #0078d7;
                border-radius: 3px;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #ffffff;
                color: #333333;
            }
            QLineEdit:focus {
                border: 1px solid #0078d7;
            }
            QFrame[frameShape="4"] { /* HLine */
                color: #cccccc;
                max-height: 1px;
                margin: 5px 0;
            }
        """
    
    @staticmethod
    def get_combo_box_style():
        """Get the combo box style for light theme."""
        return """
            QComboBox {
                padding: 4px 10px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #ffffff;
                color: #333333;
                selection-background-color: #0078d7;
                font-size: 10pt;
                text-align: left;
                min-height: 20px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 30px;
                border-left: 1px solid #cccccc;
                background-color: #f0f0f0;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
                background-color: #0078d7;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                selection-background-color: #0078d7;
                selection-color: #ffffff;
                padding: 6px;
            }
        """
    
    @staticmethod
    def get_menu_bar_style():
        """Get the menu bar style for light theme."""
        return """
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
        """
    
    @staticmethod
    def get_dialog_style():
        """Get the dialog style for light theme."""
        return """
            QDialog {
                background-color: #f5f5f5;
                color: #333333;
            }
            QLabel {
                color: #333333;
                font-size: 10pt;
            }
            QPushButton {
                background-color: #e0e0e0;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QListWidget {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #0078d7;
                color: #ffffff;
            }
        """ 