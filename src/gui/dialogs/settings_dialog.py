"""
Settings dialogs for the Video Downloader application.
"""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QListWidget, QHBoxLayout, QPushButton

class FormatSelectionDialog(QDialog):
    """Dialog for selecting the default download format."""
    
    def __init__(self, parent=None, current_format_idx=0, theme_manager=None):
        """
        Initialize the format selection dialog.
        
        Args:
            parent: Parent widget
            current_format_idx: Currently selected format index
            theme_manager: The application's theme manager for styling
        """
        super().__init__(parent)
        
        self.selected_format_idx = current_format_idx
        self.theme_manager = theme_manager
        
        self._setup_ui()
        
        # Apply theme if available
        if theme_manager:
            self.setStyleSheet(theme_manager.get_dialog_style())
        
    def _setup_ui(self):
        """Set up the user interface for this dialog."""
        self.setWindowTitle("Select Default Format")
        self.setMinimumWidth(350)
        self.setMinimumHeight(200)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Create list widget with format options
        self.format_list = QListWidget()
        self.format_list.addItem("Video + Audio (MP4)")
        self.format_list.addItem("Video Only (MP4)")
        self.format_list.addItem("Audio Only (MP3)")
        
        # Set current selection
        self.format_list.setCurrentRow(self.selected_format_idx)
        
        # Add widgets to layout
        layout.addWidget(QLabel("Select default download format:"))
        layout.addWidget(self.format_list)
        
        # Add buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def get_selected_format(self):
        """Get the selected format index."""
        return self.format_list.currentRow() 