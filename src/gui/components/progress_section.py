"""
Progress section component for the Video Downloader application.
Handles the progress bar and status messages.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QLabel
from PyQt5.QtCore import Qt

class ProgressSectionComponent(QWidget):
    """
    Component for displaying download progress and status.
    Shows a progress bar and status message.
    """
    
    def __init__(self, parent=None):
        """Initialize the progress section component."""
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the user interface for this component."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setMinimumHeight(25)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setMinimumHeight(25)
        
        # Version label (remove calibration tip)
        self.version_label = QLabel("github.com/aymanibnezakir") # Or just version/link
        self.version_label.setAlignment(Qt.AlignCenter)
        
        # Add widgets to layout
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.version_label)
        
        self.setLayout(main_layout)
        
    def set_progress(self, value):
        """Set the progress bar value (0-100)."""
        self.progress_bar.setValue(value)
        
    def set_status(self, message):
        """Set the status label text."""
        self.status_label.setText(message)
        
    def reset(self):
        """Reset the progress bar and clear the status message."""
        self.progress_bar.setValue(0)
        self.status_label.setText("")
        
    def update_download_progress(self, percent, speed_mbps, eta_str=""):
        """Update the progress display with generic download information."""
        self.progress_bar.setValue(int(percent))
        
        phase_text = "Downloading"
        
        # Check if merging (based on percent, as merging happens after 100% download)
        if percent >= 100:
             # Check if the status message already indicates merging from the downloader
            if "Merging" in self.status_label.text():
                 phase_text = "Merging formats"
            else: # If not explicitly merging, assume download finished
                 phase_text = "Finishing"
                 # Don't return yet, show 100% progress if needed

        # Format speed display    
        if isinstance(speed_mbps, (int, float)):
            speed_display = f"{speed_mbps:.1f} MB/s"
        elif isinstance(speed_mbps, str) and speed_mbps.replace('.', '', 1).isdigit():
            # It's a numeric string, add MB/s
            speed_display = f"{speed_mbps} MB/s"
        else:
            # It's not numeric or empty, might be ETA string or other status
            speed_display = f"{speed_mbps if speed_mbps else ''}"
            
        # Combine status text
        if phase_text == "Merging formats" or phase_text == "Finishing":
            status_text = f"{phase_text}..."
        elif speed_display and eta_str:
            status_text = f"{phase_text}... ({speed_display} - ETA: {eta_str})"
        elif speed_display:
            status_text = f"{phase_text}... ({speed_display})"
        else:
            status_text = f"{phase_text}... "
        
        self.status_label.setText(status_text)
        
    def set_status_message(self, message):
        """Set a status message (used for PhantomJS and other status updates)."""
        # Don't overwrite progress messages if download is active
        if "Downloading" not in self.status_label.text() and "Merging" not in self.status_label.text():
             self.status_label.setText(message) 