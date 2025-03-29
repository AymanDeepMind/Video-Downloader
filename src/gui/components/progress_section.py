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
        
        # Version label
        self.version_label = QLabel("TIP: Calibrate regularly to enhance download speeds. github.com/aymandeepmind")
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
        
    def update_download_progress(self, percent, speed_mbps, eta_str="", phase=None):
        """Update the progress display with download information."""
        self.progress_bar.setValue(int(percent))
        
        if phase == "video":
            phase_text = "Downloading video"
        elif phase == "audio":
            phase_text = "Downloading audio"
        elif phase == "merging":
            phase_text = "Merging formats"
            self.progress_bar.setValue(100)
            return
        else:
            phase_text = "Downloading"
            
        status_text = f"{phase_text}... {percent:.1f}% ({speed_mbps} MB/s)"
        if eta_str:
            status_text += f" - ETA: {eta_str}"
            
        self.status_label.setText(status_text)
        
    def show_calibration_progress(self, percent):
        """Show calibration progress."""
        self.progress_bar.setValue(int(percent))
        self.status_label.setText(f"Calibrating... {percent:.1f}%") 