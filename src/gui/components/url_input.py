"""
URL input component for the Video Downloader application.
Handles URL entry and paste functionality.
"""

import re
import clipboard
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer, QEvent
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
        self._original_text = ""
        self._is_preview = False
        self._paste_button_clicked = False
        self._fade_timer = None
        self._fade_step = 0
        self._fade_direction = 1  # 1 for fade-in, -1 for fade-out
        
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
        self.paste_button = QPushButton("Paste")
        self.paste_button.setMinimumHeight(35)
        self.paste_button.setMinimumWidth(80)
        self.paste_button.setCursor(Qt.PointingHandCursor)
        self.paste_button.clicked.connect(self._on_paste_button_clicked)
        # Install event filter for hover events
        self.paste_button.installEventFilter(self)
        
        # Add widgets to layout
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_entry, 1)
        url_layout.addWidget(self.paste_button)
        
        self.setLayout(url_layout)
        
    def eventFilter(self, obj, event):
        """Handle events for the paste button."""
        if obj == self.paste_button:
            if event.type() == QEvent.Enter:
                self._on_paste_button_hover_enter()
            elif event.type() == QEvent.Leave:
                self._on_paste_button_hover_leave()
        return super().eventFilter(obj, event)
        
    def _on_paste_button_hover_enter(self):
        """Handle mouse enter event for paste button."""
        # Check if clipboard contains valid URL
        if self._is_preview:
            return
            
        clipboard_url = self._get_clipboard_url()
        if clipboard_url:
            # Store original text
            self._original_text = self.url_entry.text()
            # Show clipboard URL with fade in effect
            self.url_entry.setText(clipboard_url)
            self._is_preview = True
            self._start_fade_animation(True)  # Fade in
    
    def _on_paste_button_hover_leave(self):
        """Handle mouse leave event for paste button."""
        if not self._is_preview or self._paste_button_clicked:
            # Reset flag if it was set
            self._paste_button_clicked = False
            return
            
        # Restore original text with fade out effect
        self._start_fade_animation(False)  # Fade out
        
    def _start_fade_animation(self, fade_in):
        """Start a fade animation for the text.
        
        Args:
            fade_in: True for fade in, False for fade out
        """
        # Stop any existing animation
        if self._fade_timer is not None:
            self._fade_timer.stop()
            self._fade_timer = None
            
        # Set up the animation
        self._fade_direction = 1 if fade_in else -1
        self._fade_step = 0 if fade_in else 10
        
        # Create and start timer for animation
        self._fade_timer = QTimer(self)
        self._fade_timer.setInterval(10)  # 10ms per step for ~100ms total
        self._fade_timer.timeout.connect(self._fade_step_animation)
        self._fade_timer.start()
        
        # Set initial opacity
        if fade_in:
            self.url_entry.setStyleSheet("QLineEdit { color: rgba(255, 255, 255, 0); }")
        
    def _fade_step_animation(self):
        """Perform one step of the fade animation."""
        if self._fade_direction > 0:  # Fade in
            self._fade_step += 1
            opacity = self._fade_step / 10.0  # 0.0 to 1.0
            
            if self._fade_step >= 10:
                # Fade in complete
                self.url_entry.setStyleSheet("")  # Reset to default style
                self._fade_timer.stop()
                self._fade_timer = None
                return
        else:  # Fade out
            self._fade_step -= 1
            opacity = self._fade_step / 10.0  # 1.0 to 0.0
            
            if self._fade_step <= 0:
                # Fade out complete, restore original text
                self.url_entry.setText(self._original_text)
                self.url_entry.setStyleSheet("")  # Reset to default style
                self._is_preview = False
                self._fade_timer.stop()
                self._fade_timer = None
                return
                
        # Apply the opacity to text color (white with varying opacity)
        self.url_entry.setStyleSheet(f"QLineEdit {{ color: rgba(255, 255, 255, {opacity}); }}")
        
    def _on_paste_button_clicked(self):
        """Handle paste button click event."""
        self._paste_button_clicked = True
        # Stop any active fade animation
        if self._fade_timer is not None:
            self._fade_timer.stop()
            self._fade_timer = None
            
        # Reset style to ensure text is fully visible
        self.url_entry.setStyleSheet("")
        
        self.paste_url()
        
    @pyqtSlot()
    def paste_url(self):
        """Paste from clipboard into the URL entry field if content is a valid URL."""
        try:
            # Get clipboard content
            clipboard_text = clipboard.paste()
            
            # Check if it's a valid URL
            if clipboard_text and self._is_valid_url(clipboard_text.strip()):
                # This is a valid URL, paste it
                self.url_entry.setText(clipboard_text.strip())
                # Emit that a valid URL was pasted
                self.url_pasted.emit(clipboard_text.strip())
                self._is_preview = False
                return True
            else:
                # Not a valid URL
                return False
        except Exception as e:
            print(f"Error in paste_url: {str(e)}")
            return False
            
    def _get_clipboard_url(self):
        """Get a valid URL from clipboard if present."""
        try:
            clipboard_text = clipboard.paste()
            if clipboard_text and self._is_valid_url(clipboard_text.strip()):
                return clipboard_text.strip()
        except Exception as e:
            print(f"Error getting clipboard content: {str(e)}")
        return None
        
    def _is_valid_url(self, text):
        """Check if the text is a valid URL using the existing pattern."""
        url_pattern = re.compile(
            r'^(https?://|www\.|youtube\.|youtu\.be|vimeo\.|dailymotion\.|twitch\.|facebook\.com/.*video)'
            r'[a-zA-Z0-9./?=_&%\-+~#;:,]+$'
        )
        return bool(url_pattern.match(text))
            
    def _on_url_changed(self, text):
        """Handle URL text changes and emit the url_changed signal."""
        # Only emit if not in preview mode
        if not self._is_preview:
            self.url_changed.emit(text.strip())
        
    def get_url(self):
        """Get the current URL text."""
        return self.url_entry.text().strip()
        
    def set_url(self, url):
        """Set the URL text."""
        self.url_entry.setText(url)
        self._is_preview = False
        # Reset any styling
        self.url_entry.setStyleSheet("")
        
    def clear(self):
        """Clear the URL field."""
        self.url_entry.clear()
        self._is_preview = False
        # Reset any styling
        self.url_entry.setStyleSheet("") 