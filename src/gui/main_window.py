"""
Main window for the Video Downloader application.
Integrates all components and handles the application flow.
"""

import os
import sys
import json
import queue
import threading

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLineEdit, QLabel, QPushButton
from PyQt5.QtCore import QTimer, Qt, pyqtSlot

# Import components
from .components.url_input import URLInputComponent
from .components.download_options import DownloadOptionsComponent
from .components.format_selector import FormatSelectorComponent
from .components.progress_section import ProgressSectionComponent
from .components.menu_bar import MenuBarComponent

# Import dialogs
from .dialogs.settings_dialog import FormatSelectionDialog
from .dialogs.about_dialog import show_about_dialog

# Import utilities
from .utils.queue_handler import QueueHandler
from .utils.ui_helpers import UIHelpers

# Import theme management
from .themes.theme_manager import ThemeManager

# Adjust import paths dynamically
if getattr(sys, 'frozen', False):
    # Running as compiled .exe
    from downloader import Downloader
    from config import load_config, save_config
    from utils import check_network
else:
    # Running directly as .py
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from downloader import Downloader
    from config import load_config, save_config
    from utils import check_network

# Add SETTINGS_FILE constant
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".adm_video_downloader_settings.json")

class VideoDownloaderApp(QMainWindow):
    """
    Main application window for the Video Downloader.
    Integrates all components and handles the application flow.
    """
    
    def __init__(self):
        """Initialize the Video Downloader application."""
        super().__init__()
        
        # Initialize application settings with defaults
        self.app_settings = {
            "default_format_idx": 0,      # Default to first format
            "dark_theme": True,           # Default to dark theme
            "auto_fetch": False,          # Default to auto-fetch disabled
            "remember_directory": True    # Default to remember directory
        }
        
        # Set up the download queue and downloader
        self.download_queue = queue.Queue()
        self.downloader = Downloader(self.download_queue)
        self.last_downloaded_file = None
        
        # Initialize queue handler
        self.queue_handler = QueueHandler(self.download_queue)
        
        # Load settings first
        self.load_app_settings()
        
        # Set up theme manager
        self.theme_manager = ThemeManager(self, self.app_settings)
        
        # Set up UI
        self.setup_ui()
        
        # Apply theme
        self.theme_manager.apply_theme()
        
        # Connect queue handler signals
        self.setup_queue_handlers()
        
        # Start queue checking timer
        self.queue_timer = QTimer()
        self.queue_timer.setInterval(100)
        self.queue_timer.timeout.connect(self.check_queue)
        self.queue_timer.start()
        
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("ADM Video Downloader v2.1.0")
        self.setMinimumSize(600, 500)
        self.setMaximumSize(600, 500)
        
        # Set application icon
        UIHelpers.setup_app_icon(self)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 12, 20, 20)
        
        # Add menu bar
        self.menu_bar = MenuBarComponent(self)
        self.menu_bar.update_settings(self.app_settings)
        self.setMenuBar(self.menu_bar)
        
        # Connect menu bar signals
        self.connect_menu_signals()
        
        # URL Input Component
        self.url_input = URLInputComponent()
        self.url_input.setContentsMargins(0, 0, 0, 0)  # Remove internal margins
        main_layout.addWidget(self.url_input)
        
        # Video Title
        title_layout = QHBoxLayout()
        title_label = QLabel("Video Title:")
        title_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        title_label.setMinimumWidth(100)
        self.video_title_entry = QLineEdit()
        self.video_title_entry.setMinimumHeight(35)
        self.video_title_entry.setEnabled(True)
        self.video_title_entry.setPlaceholderText("Video title will appear here automatically")
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.video_title_entry, 1)
        main_layout.addLayout(title_layout)
        
        # Add spacing
        main_layout.addSpacing(10)
        
        # Download Options Component
        self.download_options = DownloadOptionsComponent()
        main_layout.addWidget(self.download_options)
        
        # Add separator line with margins
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        
        # Add spacing
        main_layout.addSpacing(5)
        
        # Format Selector Component
        self.format_selector = FormatSelectorComponent()
        main_layout.addWidget(self.format_selector)
        
        # Download Folder
        folder_layout = QHBoxLayout()
        folder_label = QLabel("Download Folder:")
        folder_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        folder_label.setMinimumWidth(100)
        self.folder_entry = QLineEdit()
        self.folder_entry.setMinimumHeight(35)
        self.folder_entry.setPlaceholderText("Select download destination folder")
        browse_button = QPushButton("Browse")
        browse_button.setMinimumHeight(35)
        browse_button.setMinimumWidth(80)
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
        action_layout.setSpacing(10)
        open_folder_button = QPushButton("Open Folder")
        open_folder_button.setMinimumHeight(35)
        open_folder_button.setMinimumWidth(120)
        open_folder_button.setCursor(Qt.PointingHandCursor)
        open_folder_button.clicked.connect(self.open_download_folder)
        
        self.download_button = QPushButton("Download")
        self.download_button.setMinimumHeight(35)
        self.download_button.setMinimumWidth(120)
        self.download_button.setCursor(Qt.PointingHandCursor)
        self.download_button.clicked.connect(self.start_download)
        self.download_button.setEnabled(False)
        
        action_layout.addStretch()
        action_layout.addWidget(open_folder_button)
        action_layout.addWidget(self.download_button)
        action_layout.addStretch()
        main_layout.addLayout(action_layout)
        
        # Add less spacing between buttons and progress bar
        main_layout.addSpacing(10)
        
        # Progress Section Component
        self.progress_section = ProgressSectionComponent()
        main_layout.addWidget(self.progress_section)
        
        # Connect component signals
        self.connect_component_signals()
        
        # Load saved configuration
        self.load_saved_config()
        
        # Set default selected option from settings
        self.download_options.set_selected_option(
            self.app_settings["default_format_idx"] + 1  # +1 because IDs are 1-based
        )
        
        # Register components with theme manager
        self.register_theme_components()
        
    def connect_menu_signals(self):
        """Connect signals from the menu bar."""
        # Remove calibration connection
        # self.menu_bar.calibrate_triggered.connect(self.start_calibration)
        self.menu_bar.theme_toggle_triggered.connect(self.toggle_theme)
        self.menu_bar.default_format_triggered.connect(self.select_default_format)
        self.menu_bar.auto_fetch_toggled.connect(self.toggle_auto_fetch)
        self.menu_bar.remember_directory_toggled.connect(self.toggle_remember_directory)
        self.menu_bar.view_logs_triggered.connect(UIHelpers.open_log_file)
        
    def connect_component_signals(self):
        """Connect signals from UI components."""
        # URL input signals
        self.url_input.url_changed.connect(self.on_url_changed)
        self.url_input.url_pasted.connect(self.on_url_pasted)
        
        # Format selector signals
        self.format_selector.fetch_clicked.connect(self.fetch_formats)
        self.format_selector.format_selected.connect(self.on_format_selected)
        
    def setup_queue_handlers(self):
        """Connect signals from the queue handler to UI slots."""
        self.queue_handler.formats_signal.connect(self.handle_formats)
        self.queue_handler.video_title_signal.connect(self.handle_video_title)
        self.queue_handler.error_signal.connect(self.handle_error)
        self.queue_handler.enable_fetch_signal.connect(self.handle_enable_fetch)
        self.queue_handler.progress_signal.connect(self.handle_progress)
        self.queue_handler.download_complete_signal.connect(self.handle_download_complete)
        self.queue_handler.merge_failed_signal.connect(self.handle_merge_failed)
        self.queue_handler.download_error_signal.connect(self.handle_download_error)
        self.queue_handler.status_signal.connect(self.handle_status)
        
    def register_theme_components(self):
        """Register components with the theme manager."""
        self.theme_manager.register_component(self.menu_bar)
        self.theme_manager.register_component(self.url_input)
        self.theme_manager.register_component(self.format_selector)
        self.theme_manager.register_component(self.progress_section)
        
    def check_queue(self):
        """Check the queue for messages from the downloader thread."""
        self.queue_handler.check_queue()
        
    def load_app_settings(self):
        """Load application settings from settings file."""
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    loaded_settings = json.load(f)
                    # Update with loaded settings
                    self.app_settings.update(loaded_settings)
        except Exception as e:
            print(f"Error loading application settings: {str(e)}")
            # If there's an error, we'll use the defaults initialized in __init__
            
    def save_app_settings(self):
        """Save application settings to settings file."""
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(self.app_settings, f)
        except Exception as e:
            print(f"Error saving application settings: {str(e)}")
            UIHelpers.show_warning(self, "Settings Error", f"Could not save settings: {str(e)}")
            
    def load_saved_config(self):
        """Load the saved download folder configuration."""
        try:
            saved_folder = load_config()
            if saved_folder and os.path.exists(saved_folder):
                self.folder_entry.setText(saved_folder)
        except Exception as e:
            print(f"Error loading saved folder: {str(e)}")
            
    # Handler methods for queue messages
    def handle_formats(self, data):
        """Handle formats message from queue."""
        # Ensure format_list is always a list, even if we receive a string
        if isinstance(data, str):
            format_list = [data]
        else:
            format_list = data if isinstance(data, list) else []
            
        self.format_selector.set_formats(format_list)
        if format_list:
            self.progress_section.set_status("Formats fetched. Select a format.")
            self.download_button.setEnabled(True)
        else:
            self.progress_section.set_status("No formats available.")
            
        # Re-enable fetch button using correct state
        self.format_selector.set_fetching_state(False)
            
    def handle_video_title(self, data):
        """Handle video title message from queue."""
        # The data is already the title string, not a list
        if isinstance(data, str):
            self.video_title_entry.setText(data)
            self.video_title_entry.setCursorPosition(0)  # Move cursor to the start
        else:
            # Fallback in case it's a list
            title = data[0] if isinstance(data, (list, tuple)) and data else ""
            self.video_title_entry.setText(title)
            self.video_title_entry.setCursorPosition(0)  # Move cursor to the start
            
    def handle_error(self, data):
        """Handle error message from queue."""
        error_msg = data[0] if data else "Unknown error"
        self.progress_section.set_status(f"Error: {error_msg}")
        self.format_selector.set_fetching_state(False)
            
    def handle_enable_fetch(self, data):
        """Handle enable fetch message from queue."""
        self.format_selector.set_fetching_state(False) # Assuming enable_fetch means fetching is done
            
    def handle_progress(self, data):
        """Handle progress message from queue (without phase)."""
        # Data structure is now a list: [percent, speed, eta]
        percent = data[0] if len(data) >= 1 else 0
        speed_mbps = data[1] if len(data) >= 2 else None # Can be float or string
        eta_str = data[2] if len(data) > 2 else ""
        
        self.progress_section.update_download_progress(percent, speed_mbps, eta_str)
            
    def handle_download_complete(self, data):
        """Handle download complete message from queue."""
        self.progress_section.set_progress(100)
        self.progress_section.set_status("Download completed!")
        
        # Re-enable buttons and title field
        self.format_selector.enable_fetch(True)
        self.download_button.setEnabled(True)
        self.video_title_entry.setEnabled(True)
        
        if data:
            file_path = data[0]
            self.last_downloaded_file = file_path
            
    def handle_merge_failed(self, data):
        """Handle merge failed message from queue."""
        self.progress_section.set_progress(0)
        self.progress_section.set_status("Error: Failed to merge formats")
        
        # Re-enable buttons and title field
        self.format_selector.enable_fetch(True)
        self.download_button.setEnabled(True)
        self.video_title_entry.setEnabled(True)
            
    def handle_download_error(self, data):
        """Handle download error message from queue."""
        error_msg = data[0] if data else "Unknown error"
        self.progress_section.set_progress(0)
        self.progress_section.set_status(f"Error: {error_msg}")
        
        # Re-enable buttons and title field
        self.format_selector.enable_fetch(True)
        self.download_button.setEnabled(True)
        self.video_title_entry.setEnabled(True)
            
    def handle_status(self, data):
        """Handle status update messages, including PhantomJS updates."""
        # Update status in the progress section
        self.progress_section.set_status_message(data)
        
    # Slot methods for UI events
    @pyqtSlot(str)
    def on_url_changed(self, url):
        """Handle URL text changes."""
        self.url_input.url_entry.setText(url)
        self.url_input.url_entry.setCursorPosition(0)  # Move cursor to the start
        # Clear format selection when URL changes
        self.format_selector.clear_formats()
        self.download_button.setEnabled(False)
        
        # Auto-fetch if enabled and URL seems valid
        if self.app_settings["auto_fetch"] and url and any(
            domain in url for domain in ["youtube.com/watch", "youtu.be/", "vimeo.com/", "dailymotion.com/"]
        ):
            self.fetch_formats()
            
    @pyqtSlot(str)
    def on_url_pasted(self, url):
        """Handle URL pasted event."""
        # Clear format selection when URL changes
        self.format_selector.clear_formats()
        self.download_button.setEnabled(False)
        
        # Auto-fetch if enabled
        if self.app_settings["auto_fetch"]:
            self.fetch_formats()
            
    @pyqtSlot(str)
    def on_format_selected(self, format_str):
        """Handle format selection changes."""
        if format_str:
            self.download_button.setEnabled(True)
            
    @pyqtSlot()
    def browse_folder(self):
        """Open a folder browser dialog to select the download location."""
        folder = UIHelpers.browse_folder(self, "Select Download Folder", self.folder_entry.text())
        if folder:
            self.folder_entry.setText(folder)
            # Only save to config if remember_directory is enabled
            if self.app_settings["remember_directory"]:
                save_config(folder)
                
    @pyqtSlot()
    def open_download_folder(self):
        """Open the download folder in file explorer."""
        folder = self.folder_entry.text().strip()
        if not folder:
            UIHelpers.show_warning(self, "Error", "Please select a download folder first")
            return
            
        UIHelpers.open_folder(folder)
            
    @pyqtSlot()
    def fetch_formats(self):
        """Fetch available formats for the entered URL."""
        url = self.url_input.get_url()
        if not url:
            UIHelpers.show_warning(self, "Error", "Please enter a video URL")
            return
            
        # Validate URL
        if not any(domain in url for domain in ["youtube.com", "youtu.be", "vimeo.com", "dailymotion.com"]):
            if not UIHelpers.show_question(
                self,
                "URL Validation",
                "The URL doesn't appear to be from a known video site. Continue anyway?"
            ):
                return
                
        # Check network
        if not check_network():
            UIHelpers.show_warning(self, "Error", "No internet connection. Please check your network settings.")
            return
            
        # Clear previous formats
        self.format_selector.clear_formats()
        self.download_button.setEnabled(False)
        
        # Set status and disable fetch button (using fetching state)
        self.progress_section.set_status("Fetching available formats...")
        self.format_selector.set_fetching_state(True)
        
        # Get selected type
        type_choice = str(self.download_options.get_selected_option())
        
        # Start the fetch process
        self.downloader.fetch_formats(url, type_choice)
            
    @pyqtSlot()
    def start_download(self):
        """Start the download with selected options."""
        url = self.url_input.get_url()
        if not url:
            UIHelpers.show_warning(self, "Error", "Please enter a video URL")
            return
            
        format_str = self.format_selector.get_selected_format()
        if not format_str:
            UIHelpers.show_warning(self, "Error", "Please select a format")
            return
            
        folder = self.folder_entry.text().strip()
        if not folder:
            UIHelpers.show_warning(self, "Error", "Please select a download folder")
            return
            
        # Check if folder exists or can be created
        if not os.path.exists(folder):
            try:
                os.makedirs(folder, exist_ok=True)
            except Exception as e:
                UIHelpers.show_warning(self, "Error", f"Could not create folder: {str(e)}")
                return
                
        # Save the selected folder
        save_config(folder)
        
        # Get selected type and title
        type_choice = str(self.download_options.get_selected_option())
        user_title = self.video_title_entry.text().strip()
        
        # Update status to show we're starting the download
        self.progress_section.set_status("Starting download...")
        self.progress_section.set_progress(0)
        
        # Disable editing during download
        self.video_title_entry.setEnabled(False)
        
        # Disable buttons during download (use enable_fetch for fetch button)
        self.download_button.setEnabled(False)
        self.format_selector.enable_fetch(False)
        
        # Start the download
        success, error_msg = self.downloader.start_download(url, type_choice, format_str, folder, user_title)
        if not success:
            UIHelpers.show_warning(self, "Error", error_msg)
            # Re-enable fetch button (not fetching state)
            self.format_selector.enable_fetch(True)
            # Re-enable buttons and title editing
            self.download_button.setEnabled(True)
            self.format_selector.set_fetching_state(False)
            self.video_title_entry.setEnabled(True)
            # Reset progress
            self.progress_section.set_status(f"Error: {error_msg}")
            self.progress_section.set_progress(0)
            
    @pyqtSlot()
    def select_default_format(self):
        """Open dialog to select default download format."""
        try:
            dialog = FormatSelectionDialog(
                self,
                current_format_idx=self.app_settings["default_format_idx"],
                theme_manager=self.theme_manager
            )
            
            if dialog.exec_():
                format_idx = dialog.get_selected_format()
                self.app_settings["default_format_idx"] = format_idx
                
                # Apply the format selection to UI - IDs are 1-based
                self.download_options.set_selected_option(format_idx + 1)
                
                self.save_app_settings()
        except Exception as e:
            print(f"Error showing format dialog: {str(e)}")
            UIHelpers.show_warning(self, "Error", f"Could not open format selection: {str(e)}")
            
    @pyqtSlot()
    def toggle_theme(self):
        """Toggle between light and dark themes."""
        try:
            # Toggle the theme using the theme manager
            is_dark = self.theme_manager.toggle_theme()
            
            # Update the app settings
            self.app_settings["dark_theme"] = is_dark
            
            # Update menu text
            self.menu_bar.update_settings(self.app_settings)
            
            # Save settings
            self.save_app_settings()
        except Exception as e:
            print(f"Error toggling theme: {str(e)}")
            UIHelpers.show_warning(self, "Settings Error", f"Could not change theme: {str(e)}")
            
    @pyqtSlot(bool)
    def toggle_auto_fetch(self, checked):
        """Toggle auto-fetch setting."""
        try:
            self.app_settings["auto_fetch"] = checked
            self.save_app_settings()
        except Exception as e:
            print(f"Error toggling auto-fetch: {str(e)}")
            UIHelpers.show_warning(self, "Settings Error", f"Could not change auto-fetch setting: {str(e)}")
            
    @pyqtSlot(bool)
    def toggle_remember_directory(self, checked):
        """Toggle remember directory setting."""
        try:
            self.app_settings["remember_directory"] = checked
            self.save_app_settings()
            
            # If remember directory is disabled, clear the saved directory
            if not checked:
                save_config("")
        except Exception as e:
            print(f"Error toggling remember directory: {str(e)}")
            UIHelpers.show_warning(self, "Settings Error", f"Could not change directory setting: {str(e)}")
            
    def closeEvent(self, event):
        """Handle closing the application."""
        # Clean up any resources
        try:
            self.downloader.cleanup()
            for thread in threading.enumerate():
                if thread != threading.current_thread() and not thread.daemon:
                    thread.join(0.1)
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
            
        event.accept()