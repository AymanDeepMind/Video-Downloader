import os
import sys
import ctypes
import threading
import queue
import traceback
import subprocess
import webbrowser
import json
import re
import clipboard
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QRadioButton, QComboBox, QProgressBar, 
                            QFileDialog, QButtonGroup, QFrame, QApplication, QMessageBox,
                            QSizePolicy, QAction, QMenu, QMenuBar, QDialog, QVBoxLayout,
                            QListWidget, QListWidgetItem, QCheckBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QIcon, QClipboard, QFont, QPalette, QColor

# Adjust import paths dynamically
if getattr(sys, 'frozen', False):
    # Running as compiled .exe
    from utils import resource_path, logger, check_network
    from config import load_config, save_config
    from downloader import Downloader
else:
    # Running directly as .py
    from utils import resource_path, logger, check_network
    from config import load_config, save_config
    from downloader import Downloader

# Add SETTINGS_FILE constant
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".adm_video_downloader_settings.json")

class VideoDownloaderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.queue = queue.Queue()
        self.title_saved = False
        self.downloader = Downloader(self.queue)
        self.last_downloaded_file = None
        self.current_download_phase = None
        
        # Initialize application settings with defaults
        self.app_settings = {
            "default_format_idx": 0,      # Default to first format
            "dark_theme": True,           # Default to dark theme
            "auto_fetch": False,           # Default to auto-fetch disabled
            "remember_directory": True    # Default to remember directory
        }
        
        # Load settings first
        self.load_app_settings()
        self.setup_ui()
        self.create_menu_bar()
        self.load_saved_config()
        
        # Start queue checking timer
        self.queue_timer = QTimer()
        self.queue_timer.setInterval(100)
        self.queue_timer.timeout.connect(self.check_queue)
        self.queue_timer.start()
        
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("ADM Video Downloader v.1.1.0")
        self.setMinimumSize(600, 500)  # Increased height
        self.setMaximumSize(600, 500)  # Increased height
        
        # Set application icon
        self.setup_app_icon()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)  # Increased overall spacing
        main_layout.setContentsMargins(25, 25, 25, 25)  # Increased margins
        
        # URL Input
        url_layout = QHBoxLayout()
        url_label = QLabel("Video URL:")
        url_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        url_label.setMinimumWidth(100)
        self.url_entry = QLineEdit()
        self.url_entry.setMinimumHeight(35)  # Set minimum height
        self.url_entry.setPlaceholderText("YouTube, Facebook, Instagram or other video URL")
        paste_button = QPushButton("Paste")
        paste_button.setMinimumHeight(35)  # Match height with entry
        paste_button.setMinimumWidth(80)  # Set minimum width
        paste_button.setCursor(Qt.PointingHandCursor)
        paste_button.clicked.connect(self.paste_url)
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_entry, 1)
        url_layout.addWidget(paste_button)
        main_layout.addLayout(url_layout)
        
        # Video Title
        title_layout = QHBoxLayout()
        title_label = QLabel("Video Title:")
        title_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        title_label.setMinimumWidth(100)
        self.video_title_entry = QLineEdit()
        self.video_title_entry.setMinimumHeight(35)  # Set minimum height
        self.video_title_entry.setEnabled(True)  # Always editable by default
        self.video_title_entry.setPlaceholderText("Video title will appear here automatically")
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.video_title_entry, 1)
        main_layout.addLayout(title_layout)
        
        # Add spacing
        main_layout.addSpacing(10)
        
        # Download Type Radio Buttons
        type_layout = QHBoxLayout()
        type_label = QLabel("Download Type:")
        type_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        type_label.setMinimumWidth(100)
        
        # Radio button group in its own layout with proper spacing
        radio_frame = QFrame()
        radio_frame.setFrameShape(QFrame.NoFrame)
        radio_layout = QHBoxLayout(radio_frame)  # Changed to QHBoxLayout
        radio_layout.setContentsMargins(0, 0, 0, 0)  # Reduced margins
        radio_layout.setSpacing(20)  # Increased spacing between radio buttons
        
        self.type_group = QButtonGroup(self)
        self.radio1 = QRadioButton("Video+Audio (MP4)")
        self.radio1.setCursor(Qt.PointingHandCursor)
        self.radio1.setMinimumHeight(35)  # Match height with other elements
        self.radio1.setChecked(True)
        self.radio2 = QRadioButton("Video Only (MP4)")
        self.radio2.setCursor(Qt.PointingHandCursor)
        self.radio2.setMinimumHeight(35)  # Match height with other elements
        self.radio3 = QRadioButton("Audio Only (MP3)")
        self.radio3.setCursor(Qt.PointingHandCursor)
        self.radio3.setMinimumHeight(35)  # Match height with other elements
        
        self.type_group.addButton(self.radio1, 1)
        self.type_group.addButton(self.radio2, 2)
        self.type_group.addButton(self.radio3, 3)
        
        type_layout.addWidget(type_label)
        radio_layout.addWidget(self.radio1)
        radio_layout.addWidget(self.radio2)
        radio_layout.addWidget(self.radio3)
        radio_layout.addStretch()  # Add stretch at the end
        
        type_layout.addWidget(radio_frame)
        main_layout.addLayout(type_layout)
        
        # Add separator line with margins
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        
        # Add spacing
        main_layout.addSpacing(5)
        
        # Fetch Formats button (Calibrate button removed, moved to menu)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)  # Add spacing between buttons
        self.fetch_button = QPushButton("Fetch Formats")
        self.fetch_button.setMinimumHeight(35)  # Set minimum height
        self.fetch_button.setMinimumWidth(120)  # Set minimum width
        self.fetch_button.setCursor(Qt.PointingHandCursor)
        self.fetch_button.clicked.connect(self.fetch_formats)
        
        # Set the fetch button as default/primary action
        self.fetch_button.setDefault(True)
        
        button_layout.addStretch()
        button_layout.addWidget(self.fetch_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        # Add spacing
        main_layout.addSpacing(5)
        
        # Format Selection
        format_layout = QHBoxLayout()
        format_label = QLabel("Select Format:")
        format_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        format_label.setMinimumWidth(100)
        
        # Create the format combo box with increased height and proper styling
        self.format_combo = QComboBox()
        self.format_combo.setMinimumHeight(40)  # Reduced from 60px to 40px
        self.format_combo.setMaximumHeight(40)  # Set maximum height for consistency
        self.format_combo.setMinimumWidth(350)
        self.format_combo.setCursor(Qt.PointingHandCursor)
        self.format_combo.setPlaceholderText("Available formats will appear here")
        
        # Set a specific style just for this combo box to ensure text visibility
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
        main_layout.addLayout(format_layout)
        
        # Download Folder
        folder_layout = QHBoxLayout()
        folder_label = QLabel("Download Folder:")
        folder_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        folder_label.setMinimumWidth(100)
        self.folder_entry = QLineEdit()
        self.folder_entry.setMinimumHeight(35)  # Set minimum height
        self.folder_entry.setPlaceholderText("Select download destination folder")
        browse_button = QPushButton("Browse")
        browse_button.setMinimumHeight(35)  # Match height with entry
        browse_button.setMinimumWidth(80)  # Set minimum width
        browse_button.setCursor(Qt.PointingHandCursor)
        browse_button.clicked.connect(self.browse_folder)
        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(self.folder_entry, 1)
        folder_layout.addWidget(browse_button)
        main_layout.addLayout(folder_layout)
        
        # Add spacing between folder input and separator line
        main_layout.addSpacing(15)
        
        # Add separator line with margins
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line2)
        
        # Reduced spacing after the line to keep buttons closer to it
        main_layout.addSpacing(2)
        
        # Download and Open Folder Buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)  # Add spacing between buttons
        open_folder_button = QPushButton("Open Folder")
        open_folder_button.setMinimumHeight(35)  # Set minimum height
        open_folder_button.setMinimumWidth(120)
        open_folder_button.setCursor(Qt.PointingHandCursor)
        open_folder_button.clicked.connect(self.open_download_folder)
        
        self.download_button = QPushButton("Download")
        self.download_button.setMinimumHeight(35)  # Set minimum height
        self.download_button.setMinimumWidth(120)
        self.download_button.setCursor(Qt.PointingHandCursor)
        self.download_button.clicked.connect(self.start_download)
        self.download_button.setEnabled(False)
        
        action_layout.addStretch()
        action_layout.addWidget(open_folder_button)
        action_layout.addWidget(self.download_button)
        action_layout.addStretch()
        main_layout.addLayout(action_layout)
        
        # Add less spacing between buttons and progress bar to compensate for added spacing above
        main_layout.addSpacing(10)
        
        # Progress Bar and Status
        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat("%p%")
        self.progress.setMinimumHeight(25)
        main_layout.addWidget(self.progress)
        
        # Add minimal spacing between progress bar and status label
        main_layout.addSpacing(5)
        
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setMinimumHeight(25)  # Set minimum height
        main_layout.addWidget(self.status_label)
        
        # Version label at bottom
        version_layout = QHBoxLayout()
        version_label = QLabel("TIP: Calibrate regularly to enhance download speeds. github.com/aymandeepmind")
        version_label.setAlignment(Qt.AlignCenter)
        version_layout.addWidget(version_label)
        main_layout.addLayout(version_layout)
        
        # Styling
        self.setup_styles()
        
        # After UI setup, apply the correct theme
        if not self.app_settings["dark_theme"]:
            self.apply_light_theme()
        
        # Apply default download type
        format_idx = self.app_settings["default_format_idx"]
        if format_idx == 0:
            self.radio1.setChecked(True)
        elif format_idx == 1:
            self.radio2.setChecked(True)
        elif format_idx == 2:
            self.radio3.setChecked(True)
        
    def setup_app_icon(self):
        """Set application icon for both taskbar and window title."""
        try:
            # Determine icon path based on whether we're running in frozen mode
            if getattr(sys, 'frozen', False):
                # Running as compiled exe
                icon_path = resource_path('assets/icon.ico')
            else:
                # Running in development environment
                icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'icon.ico')
            
            # Set window icon
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            
            # Set taskbar icon (Windows only)
            if os.name == 'nt':
                # Create a unique app ID for Windows taskbar
                app_id = 'adm.videodownloader.1.0'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception as e:
            logger.error(f"Failed to set application icon: {str(e)}")
            
    def setup_styles(self):
        """Apply custom styles to the application."""
        self.setStyleSheet("""
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
            /* QComboBox styling moved to individual widget */
            QFrame[frameShape="4"] { /* HLine */
                color: #555555;
                max-height: 1px;
                margin: 5px 0;
            }
        """)
        
    def load_saved_config(self):
        """Load the saved configuration."""
        try:
            saved_folder = load_config()
            if saved_folder and os.path.exists(saved_folder):
                self.folder_entry.setText(saved_folder)
        except Exception as e:
            logger.error(f"Error loading saved folder: {str(e)}")
            
    def check_queue(self):
        """Process queue updates from threads."""
        try:
            while not self.queue.empty():
                message = self.queue.get_nowait()
                
                if message[0] == "formats":
                    format_list = message[1]
                    self.format_combo.clear()
                    self.format_combo.addItems(format_list)
                    if format_list:
                        # Automatically select the first (top) format
                        self.format_combo.setCurrentIndex(0)
                        self.status_label.setText("Formats fetched. Select a format.")
                        self.download_button.setEnabled(True)
                    else:
                        self.status_label.setText("No formats available.")
                        
                elif message[0] == "video_title":
                    self.video_title_entry.setText(message[1])
                    # Keep title field enabled for editing
                    self.title_saved = True
                    
                elif message[0] == "error":
                    self.status_label.setText(f"Error: {message[1]}")
                    self.fetch_button.setEnabled(True)
                    
                elif message[0] == "enable_fetch":
                    self.fetch_button.setEnabled(True)
                    
                elif message[0] == "start_phase":
                    phase = message[1]
                    
                    if phase in ("video", "audio"):
                        self.status_label.setText(f"Downloading {phase}... 0.0%")
                        self.progress.setValue(0)
                    elif phase == "merging":
                        self.status_label.setText("Merging formats...")
                        self.progress.setValue(100)
                        
                elif message[0] == "progress":
                    percent, speed_mbps, eta_str = message[1], message[2], message[3] if len(message) > 3 else ""
                    self.progress.setValue(int(percent))
                    
                    if self.current_download_phase == "video":
                        phase_text = "Downloading video"
                    elif self.current_download_phase == "audio":
                        phase_text = "Downloading audio"
                    else:
                        phase_text = "Downloading"
                        
                    status_text = f"{phase_text}... {percent:.1f}% ({speed_mbps} MB/s)"
                    if eta_str:
                        status_text += f" - ETA: {eta_str}"
                    self.status_label.setText(status_text)
                    
                elif message[0] == "phase_complete":
                    self.progress.setValue(100)
                    
                elif message[0] == "download_complete":
                    self.progress.setValue(100)
                    self.status_label.setText("Download completed!")
                    
                    # Re-enable buttons and title field
                    self.fetch_button.setEnabled(True)
                    self.download_button.setEnabled(True)
                    self.video_title_entry.setEnabled(True)
                    
                    file_path = message[1]
                    self.last_downloaded_file = file_path
                    
                elif message[0] == "merge_failed":
                    self.progress.setValue(0)
                    self.status_label.setText("Error: Failed to merge formats")
                    
                    # Re-enable buttons and title field
                    self.fetch_button.setEnabled(True)
                    self.download_button.setEnabled(True)
                    self.video_title_entry.setEnabled(True)
                    
                elif message[0] == "calibration_progress":
                    percent = message[1]
                    self.progress.setValue(int(percent))
                    self.status_label.setText(f"Calibrating... {percent:.1f}%")
                    
                elif message[0] == "calibration_complete":
                    optimal_fragments = message[1]
                    self.progress.setValue(100)
                    self.status_label.setText(f"Calibration complete. Optimal fragments: {optimal_fragments}")
                    
                    # Re-enable buttons
                    self.fetch_button.setEnabled(True)
                    
                elif message[0] == "download_error":
                    error_msg = message[1]
                    self.progress.setValue(0)
                    self.status_label.setText(f"Error: {error_msg}")
                    
                    # Re-enable buttons and title field
                    self.fetch_button.setEnabled(True)
                    self.download_button.setEnabled(True)
                    self.video_title_entry.setEnabled(True)
                    
                elif message[0] == "set_phase":
                    self.current_download_phase = message[1]
                
        except Exception as e:
            logger.error(f"Error in check_queue: {str(e)}")
    
    @pyqtSlot()
    def browse_folder(self):
        """Open a folder browser dialog to select the download location."""
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder", self.folder_entry.text())
        if folder:
            self.folder_entry.setText(folder)
            # Only save to config if remember_directory is enabled
            if self.app_settings["remember_directory"]:
                save_config(folder)
    
    @pyqtSlot()
    def paste_url(self):
        """Paste from clipboard into the URL entry field if content is a valid URL."""
        try:
            # Get clipboard content using the clipboard library
            clipboard_text = clipboard.paste()
            
            # Define a regex pattern to validate URLs
            url_pattern = re.compile(
                r'^(https?://|www\.|youtube\.|youtu\.be|vimeo\.|dailymotion\.|twitch\.|facebook\.com/.*video)'
                r'[a-zA-Z0-9./?=_&%\-+~#;:,]+$'
            )
            
            if clipboard_text and url_pattern.match(clipboard_text.strip()):
                # This is a valid URL, paste it
                self.url_entry.setText(clipboard_text.strip())
                
                # Clear format selection when URL changes
                self.format_combo.clear()
                self.download_button.setEnabled(False)
                
                # Auto-fetch if URL seems valid and auto-fetch is enabled
                url = self.url_entry.text().strip()
                if self.app_settings["auto_fetch"] and any(domain in url for domain in ["youtube.com/watch", "youtu.be/", "vimeo.com/", "dailymotion.com/"]):
                    self.fetch_formats()
            else:
                # Not a valid URL
                self.status_label.setText("Clipboard content is not a valid URL.")
        except Exception as e:
            logger.error(f"Error in paste_url: {str(e)}")
            self.status_label.setText("Error accessing clipboard.")
    
    @pyqtSlot()
    def fetch_formats(self):
        """Fetch available formats for the entered URL."""
        url = self.url_entry.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a video URL")
            return
            
        # Validate URL
        if not any(domain in url for domain in ["youtube.com", "youtu.be", "vimeo.com", "dailymotion.com"]):
            response = QMessageBox.question(
                self,
                "URL Validation",
                "The URL doesn't appear to be from a known video site. Continue anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            if response == QMessageBox.No:
                return
                
        # Check network
        if not check_network():
            QMessageBox.warning(self, "Error", "No internet connection. Please check your network settings.")
            return
            
        # Clear previous formats
        self.format_combo.clear()
        self.download_button.setEnabled(False)
        
        # Set status
        self.status_label.setText("Fetching available formats...")
        
        # Disable fetch button during operation
        self.fetch_button.setEnabled(False)
        
        # Get selected type
        type_choice = str(self.type_group.checkedId())
        
        # Start the fetch process
        self.downloader.fetch_formats(url, type_choice)
    
    @pyqtSlot()
    def start_calibration(self):
        """Start the calibration process."""
        # Check network
        if not check_network():
            QMessageBox.warning(self, "Error", "No internet connection. Please check your network settings.")
            return
            
        # Confirm with user
        response = QMessageBox.question(
            self,
            "Start Calibration",
            "Calibration will test your connection to find optimal download settings. Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        if response == QMessageBox.No:
            return
            
        # Set status
        self.progress.setValue(0)
        self.status_label.setText("Starting calibration...")
        
        # Disable buttons during calibration
        self.fetch_button.setEnabled(False)
        
        # Start the calibration process
        self.downloader.start_calibration()
    
    @pyqtSlot()
    def start_download(self):
        """Start the download with selected options."""
        url = self.url_entry.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a video URL")
            return
            
        format_str = self.format_combo.currentText()
        if not format_str:
            QMessageBox.warning(self, "Error", "Please select a format")
            return
            
        folder = self.folder_entry.text().strip()
        if not folder:
            QMessageBox.warning(self, "Error", "Please select a download folder")
            return
            
        # Check if folder exists or can be created
        if not os.path.exists(folder):
            try:
                os.makedirs(folder, exist_ok=True)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not create folder: {str(e)}")
                return
                
        # Save the selected folder
        save_config(folder)
        
        # Get selected type and title
        type_choice = str(self.type_group.checkedId())
        user_title = self.video_title_entry.text().strip()
        
        # Disable editing during download
        self.video_title_entry.setEnabled(False)
        
        # Disable buttons during download
        self.download_button.setEnabled(False)
        self.fetch_button.setEnabled(False)
        
        # Start the download
        success, error_msg = self.downloader.start_download(url, type_choice, format_str, folder, user_title)
        if not success:
            QMessageBox.warning(self, "Error", error_msg)
            # Re-enable buttons and title editing
            self.fetch_button.setEnabled(True)
            self.video_title_entry.setEnabled(True)
    
    @pyqtSlot()    
    def open_download_folder(self):
        """Open the download folder in file explorer."""
        folder = self.folder_entry.text().strip()
        if not folder:
            QMessageBox.warning(self, "Error", "Please select a download folder first")
            return
            
        if not os.path.exists(folder):
            try:
                os.makedirs(folder, exist_ok=True)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not create folder: {str(e)}")
                return
                
        try:
            # Open folder in file explorer
            if os.name == 'nt':  # Windows
                os.startfile(folder)
            elif os.name == 'posix':  # macOS and Linux
                if sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', folder])
                else:  # Linux
                    subprocess.run(['xdg-open', folder])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open folder: {str(e)}")
            
    def closeEvent(self, event):
        """Handle closing the application."""
        # Clean up any resources
        try:
            self.downloader.cleanup()
            for thread in threading.enumerate():
                if thread != threading.current_thread() and not thread.daemon:
                    thread.join(0.1)
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
        event.accept()

    def create_menu_bar(self):
        """Create the menu bar with Tools, Settings, and Help menus"""
        # Create menubar
        menu_bar = self.menuBar()
        
        # Tools Menu
        tools_menu = menu_bar.addMenu("&Tools")
        
        # Calibrate Action
        calibrate_action = QAction("&Calibrate Connection", self)
        calibrate_action.setStatusTip("Calibrate your connection for optimal download speed")
        calibrate_action.triggered.connect(self.start_calibration)
        tools_menu.addAction(calibrate_action)
        
        # Settings Menu
        settings_menu = menu_bar.addMenu("&Settings")
        
        # Default Download Format
        default_format_action = QAction("Default Download &Format", self)
        default_format_action.setStatusTip("Set the default download format")
        default_format_action.triggered.connect(self.select_default_format)
        settings_menu.addAction(default_format_action)
        
        # Light/Dark Toggle
        self.theme_toggle_action = QAction("Switch to &Light Theme" if self.app_settings["dark_theme"] else "Switch to &Dark Theme", self)
        self.theme_toggle_action.setStatusTip("Switch between light and dark themes")
        self.theme_toggle_action.triggered.connect(self.toggle_theme)
        settings_menu.addAction(self.theme_toggle_action)
        
        settings_menu.addSeparator()
        
        # Auto-fetch toggle
        self.auto_fetch_action = QAction("&Auto-fetch formats when URL is entered", self)
        self.auto_fetch_action.setStatusTip("Automatically fetch formats when URL is entered")
        self.auto_fetch_action.setCheckable(True)
        self.auto_fetch_action.setChecked(self.app_settings["auto_fetch"])
        self.auto_fetch_action.triggered.connect(self.toggle_auto_fetch)
        settings_menu.addAction(self.auto_fetch_action)
        
        # Remember last directory toggle
        self.remember_dir_action = QAction("&Remember last used directory", self)
        self.remember_dir_action.setStatusTip("Remember the last used download directory")
        self.remember_dir_action.setCheckable(True)
        self.remember_dir_action.setChecked(self.app_settings["remember_directory"])
        self.remember_dir_action.triggered.connect(self.toggle_remember_directory)
        settings_menu.addAction(self.remember_dir_action)
        
        # Help Menu
        help_menu = menu_bar.addMenu("&Help")
        
        # View Logs
        logs_action = QAction("View &Logs", self)
        logs_action.setStatusTip("View application logs")
        logs_action.triggered.connect(self.view_logs)
        help_menu.addAction(logs_action)
        
        # Report Bug
        report_bug_action = QAction("&Report Bug", self)
        report_bug_action.setStatusTip("Report a bug on GitHub")
        report_bug_action.triggered.connect(self.report_bug)
        help_menu.addAction(report_bug_action)
        
        # About
        about_action = QAction("&About ADM Video Downloader", self)
        about_action.setStatusTip("View information about ADM Video Downloader")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # Apply styling to menu bar based on current theme
        if self.app_settings["dark_theme"]:
            menu_bar.setStyleSheet("""
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
            menu_bar.setStyleSheet("""
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

    def report_bug(self):
        """Open the GitHub issues page to report a bug"""
        webbrowser.open("https://github.com/AymanDeepMind/Video-Downloader/issues")
        
    def show_about(self):
        """Show about information and navigate to GitHub repository"""
        webbrowser.open("https://github.com/AymanDeepMind/Video-Downloader")

    def load_app_settings(self):
        """Load application settings from settings file."""
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    loaded_settings = json.load(f)
                    # Update with loaded settings
                    self.app_settings.update(loaded_settings)
        except Exception as e:
            logger.error(f"Error loading application settings: {str(e)}")
            # If there's an error, we'll use the defaults initialized in __init__

    def save_app_settings(self):
        """Save application settings to settings file."""
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(self.app_settings, f)
        except Exception as e:
            logger.error(f"Error saving application settings: {str(e)}")
            QMessageBox.warning(self, "Settings Error", f"Could not save settings: {str(e)}")

    def select_default_format(self):
        """Open dialog to select default download format."""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("Select Default Format")
            dialog.setMinimumWidth(350)
            dialog.setMinimumHeight(200)
            
            layout = QVBoxLayout(dialog)
            
            # Create list widget with format options
            format_list = QListWidget()
            format_list.addItem("Video + Audio (MP4)")
            format_list.addItem("Video Only (MP4)")
            format_list.addItem("Audio Only (MP3)")
            
            # Set current selection
            format_list.setCurrentRow(self.app_settings["default_format_idx"])
            
            layout.addWidget(QLabel("Select default download format:"))
            layout.addWidget(format_list)
            
            # Add buttons
            button_layout = QHBoxLayout()
            save_button = QPushButton("Save")
            cancel_button = QPushButton("Cancel")
            
            save_button.clicked.connect(lambda: self.save_default_format(format_list.currentRow(), dialog))
            cancel_button.clicked.connect(dialog.reject)
            
            button_layout.addStretch()
            button_layout.addWidget(save_button)
            button_layout.addWidget(cancel_button)
            
            layout.addLayout(button_layout)
            
            dialog.setStyleSheet("""
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
            """)
            
            dialog.exec_()
        except Exception as e:
            logger.error(f"Error showing format dialog: {str(e)}")
            QMessageBox.warning(self, "Error", f"Could not open format selection: {str(e)}")

    def save_default_format(self, format_idx, dialog):
        """Save the selected default format."""
        try:
            self.app_settings["default_format_idx"] = format_idx
            
            # Apply the format selection to UI
            if format_idx == 0:
                self.radio1.setChecked(True)
            elif format_idx == 1:
                self.radio2.setChecked(True)
            elif format_idx == 2:
                self.radio3.setChecked(True)
            
            self.save_app_settings()
            dialog.accept()
        except Exception as e:
            logger.error(f"Error saving default format: {str(e)}")
            QMessageBox.warning(self, "Settings Error", f"Could not save format selection: {str(e)}")

    def toggle_theme(self):
        """Toggle between light and dark themes."""
        try:
            # Toggle the setting
            self.app_settings["dark_theme"] = not self.app_settings["dark_theme"]
            
            # Apply the theme
            if self.app_settings["dark_theme"]:
                self.apply_dark_theme()
            else:
                self.apply_light_theme()
            
            # Save settings
            self.save_app_settings()
            
            # Update the menu checkmarks
            self.theme_toggle_action.setText("Switch to Light Theme" if self.app_settings["dark_theme"] else "Switch to Dark Theme")
        except Exception as e:
            logger.error(f"Error toggling theme: {str(e)}")
            QMessageBox.warning(self, "Settings Error", f"Could not change theme: {str(e)}")

    def apply_dark_theme(self):
        """Apply dark theme to the application."""
        try:
            self.setup_styles()  # Current styling is already dark
            
            # Apply dark styling to the format_combo specifically
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
        except Exception as e:
            logger.error(f"Error applying dark theme: {str(e)}")

    def apply_light_theme(self):
        """Apply light theme to the application."""
        try:
            self.setStyleSheet("""
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
            
            # Apply light styling to the format_combo specifically
            self.format_combo.setStyleSheet("""
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
            """)
        except Exception as e:
            logger.error(f"Error applying light theme: {str(e)}")

    def toggle_auto_fetch(self):
        """Toggle auto-fetch setting."""
        try:
            self.app_settings["auto_fetch"] = self.auto_fetch_action.isChecked()
            self.save_app_settings()
        except Exception as e:
            logger.error(f"Error toggling auto-fetch: {str(e)}")
            QMessageBox.warning(self, "Settings Error", f"Could not change auto-fetch setting: {str(e)}")

    def toggle_remember_directory(self):
        """Toggle remember directory setting."""
        try:
            self.app_settings["remember_directory"] = self.remember_dir_action.isChecked()
            self.save_app_settings()
            
            # If remember directory is disabled, clear the saved directory
            if not self.app_settings["remember_directory"]:
                save_config("")
        except Exception as e:
            logger.error(f"Error toggling remember directory: {str(e)}")
            QMessageBox.warning(self, "Settings Error", f"Could not change directory setting: {str(e)}")

    def view_logs(self):
        """Open the log file if it exists."""
        try:
            log_file = os.path.join(os.path.expanduser("~"), '.yt_downloader.log')
            
            if not os.path.exists(log_file):
                QMessageBox.information(self, "Logs", "No log file found.")
                return
                
            # Open log file with default text editor
            if os.name == 'nt':  # Windows
                os.startfile(log_file)
            elif os.name == 'posix':  # macOS and Linux
                if sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', log_file])
                else:  # Linux
                    subprocess.run(['xdg-open', log_file])
        except Exception as e:
            logger.error(f"Error opening log file: {str(e)}")
            QMessageBox.warning(self, "Error", f"Could not open log file: {str(e)}") 