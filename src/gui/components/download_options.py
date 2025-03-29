"""
Download options component for the Video Downloader application.
Handles the radio buttons for selecting download type (video+audio, video only, or audio only).
"""

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLabel, QRadioButton, 
                           QButtonGroup, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot

class DownloadOptionsComponent(QWidget):
    """
    Component for selecting download type options.
    Provides radio buttons for video+audio, video only, or audio only.
    """
    
    # Signals
    option_changed = pyqtSignal(int)  # Emits the selected type ID
    
    def __init__(self, parent=None):
        """Initialize the download options component."""
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the user interface for this component."""
        # Main layout
        type_layout = QHBoxLayout(self)
        type_layout.setContentsMargins(0, 0, 0, 0)
        
        # Type label
        type_label = QLabel("Download Type:")
        type_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        type_label.setMinimumWidth(100)
        
        # Radio button group in its own frame
        radio_frame = QFrame()
        radio_frame.setFrameShape(QFrame.NoFrame)
        radio_layout = QHBoxLayout(radio_frame)
        radio_layout.setContentsMargins(0, 0, 0, 0)
        radio_layout.setSpacing(20)
        
        # Create button group and radio buttons
        self.type_group = QButtonGroup(self)
        
        self.radio1 = QRadioButton("Video+Audio (MP4)")
        self.radio1.setCursor(Qt.PointingHandCursor)
        self.radio1.setMinimumHeight(35)
        self.radio1.setChecked(True)
        
        self.radio2 = QRadioButton("Video Only (MP4)")
        self.radio2.setCursor(Qt.PointingHandCursor)
        self.radio2.setMinimumHeight(35)
        
        self.radio3 = QRadioButton("Audio Only (MP3)")
        self.radio3.setCursor(Qt.PointingHandCursor)
        self.radio3.setMinimumHeight(35)
        
        # Add buttons to group with IDs
        self.type_group.addButton(self.radio1, 1)
        self.type_group.addButton(self.radio2, 2)
        self.type_group.addButton(self.radio3, 3)
        
        # Connect signal
        self.type_group.buttonClicked.connect(self._on_option_changed)
        
        # Add radio buttons to layout
        radio_layout.addWidget(self.radio1)
        radio_layout.addWidget(self.radio2)
        radio_layout.addWidget(self.radio3)
        radio_layout.addStretch()
        
        # Add widgets to main layout
        type_layout.addWidget(type_label)
        type_layout.addWidget(radio_frame)
        
        self.setLayout(type_layout)
        
    def _on_option_changed(self, button):
        """Handle radio button selection changes."""
        self.option_changed.emit(self.type_group.id(button))
        
    def get_selected_option(self):
        """Get the currently selected option ID."""
        return self.type_group.checkedId()
    
    def set_selected_option(self, option_id):
        """Set the selected option by ID."""
        if option_id == 1:
            self.radio1.setChecked(True)
        elif option_id == 2:
            self.radio2.setChecked(True)
        elif option_id == 3:
            self.radio3.setChecked(True) 