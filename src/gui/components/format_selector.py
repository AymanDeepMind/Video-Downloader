"""
Format selector component for the Video Downloader application.
Handles the format selection dropdown and fetch button.
"""

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                           QComboBox, QPushButton)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot

class FormatSelectorComponent(QWidget):
    """
    Component for fetching and selecting download formats.
    Provides a fetch button and format selection dropdown.
    """
    
    # Signals
    fetch_clicked = pyqtSignal()
    format_selected = pyqtSignal(str)  # Emits the selected format string
    
    def __init__(self, parent=None):
        """Initialize the format selector component."""
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the user interface for this component."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)
        
        # Fetch button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.fetch_button = QPushButton("Fetch Formats")
        self.fetch_button.setMinimumHeight(35)
        self.fetch_button.setMinimumWidth(120)
        self.fetch_button.setCursor(Qt.PointingHandCursor)
        self.fetch_button.clicked.connect(self._on_fetch_clicked)
        self.fetch_button.setDefault(True)
        
        button_layout.addStretch()
        button_layout.addWidget(self.fetch_button)
        button_layout.addStretch()
        
        # Format selection layout
        format_layout = QHBoxLayout()
        
        format_label = QLabel("Select Format:")
        format_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        format_label.setMinimumWidth(100)
        
        self.format_combo = QComboBox()
        self.format_combo.setMinimumHeight(40)
        self.format_combo.setMaximumHeight(40)
        self.format_combo.setMinimumWidth(350)
        self.format_combo.setCursor(Qt.PointingHandCursor)
        self.format_combo.setPlaceholderText("Available formats will appear here")
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        
        # Set specific style for the combo box
        self.format_combo.setStyleSheet("""
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
        """)
        
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo, 1)
        
        # Add layouts to main layout
        main_layout.addLayout(button_layout)
        main_layout.addLayout(format_layout)
        
        self.setLayout(main_layout)
        
    @pyqtSlot()
    def _on_fetch_clicked(self):
        """Handle fetch button click."""
        self.fetch_clicked.emit()
        
    def _on_format_changed(self, format_text):
        """Handle format selection changes."""
        if format_text:  # Only emit if an actual format is selected
            self.format_selected.emit(format_text)
        
    def set_formats(self, format_list):
        """Set the available formats in the dropdown."""
        self.format_combo.clear()
        if format_list:
            self.format_combo.addItems(format_list)
            self.format_combo.setCurrentIndex(0)  # Select first item
        
    def get_selected_format(self):
        """Get the currently selected format."""
        return self.format_combo.currentText()
    
    def clear_formats(self):
        """Clear the format dropdown."""
        self.format_combo.clear()
        
    def enable_fetch(self, enabled=True):
        """Enable or disable the fetch button."""
        self.fetch_button.setEnabled(enabled)
        
    def enable_format_selection(self, enabled=True):
        """Enable or disable the format dropdown."""
        self.format_combo.setEnabled(enabled) 