"""
URL input component for the Video Downloader application.
Handles URL entry and paste functionality.
"""

import re
import clipboard
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon

class URLInputComponent(QWidget):
    """
    Component for entering and pasting video URLs.
    Emits signals when a valid URL is entered or pasted.
    """
    
    # Signals
    url_changed = pyqtSignal(str)
    url_pasted = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """Initialize the URL input component."""
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the user interface for this component."""
        # Main layout
        url_layout = QHBoxLayout(self)
        url_layout.setContentsMargins(0, 0, 0, 0)
        
        # URL label
        url_label = QLabel("Video URL:")
        url_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        url_label.setMinimumWidth(100)
        
        # URL text entry
        self.url_entry = QLineEdit()
        self.url_entry.setMinimumHeight(35)
        self.url_entry.setPlaceholderText("YouTube, Facebook, Instagram or other video URL")
        self.url_entry.textChanged.connect(self._on_url_changed)
        
        # Paste button
        paste_button = QPushButton("Paste")
        paste_button.setMinimumHeight(35)
        paste_button.setMinimumWidth(80)
        paste_button.setCursor(Qt.PointingHandCursor)
        paste_button.clicked.connect(self.paste_url)
        
        # Add widgets to layout
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_entry, 1)
        url_layout.addWidget(paste_button)
        
        self.setLayout(url_layout)
        
    @pyqtSlot()
    def paste_url(self):
        """Paste from clipboard into the URL entry field if content is a valid URL."""
        try:
            # Get clipboard content
            clipboard_text = clipboard.paste()
            
            # Define a regex pattern to validate URLs
            url_pattern = re.compile(
                r'^(https?://|www\.|youtube\.|youtu\.be|vimeo\.|dailymotion\.|twitch\.|facebook\.com/.*video)'
                r'[a-zA-Z0-9./?=_&%\-+~#;:,]+$'
            )
            
            if clipboard_text and url_pattern.match(clipboard_text.strip()):
                # This is a valid URL, paste it
                self.url_entry.setText(clipboard_text.strip())
                # Emit that a valid URL was pasted
                self.url_pasted.emit(clipboard_text.strip())
                return True
            else:
                # Not a valid URL
                return False
        except Exception as e:
            print(f"Error in paste_url: {str(e)}")
            return False
            
    def _on_url_changed(self, text):
        """Handle URL text changes and emit the url_changed signal."""
        self.url_changed.emit(text.strip())
        
    def get_url(self):
        """Get the current URL text."""
        return self.url_entry.text().strip()
        
    def set_url(self, url):
        """Set the URL text."""
        self.url_entry.setText(url)
        
    def clear(self):
        """Clear the URL field."""
        self.url_entry.clear() 