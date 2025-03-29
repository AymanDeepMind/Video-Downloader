"""
UI helper functions for the Video Downloader application.
"""

import os
import sys
import subprocess
import ctypes
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox, QFileDialog

class UIHelpers:
    """
    Provides common UI helper functions for the application.
    """
    
    @staticmethod
    def setup_app_icon(window, app_id="adm.videodownloader.1.0"):
        """
        Set application icon for both taskbar and window title.
        
        Args:
            window: The window to set the icon for
            app_id: Application ID for Windows taskbar
        """
        try:
            # Determine icon path based on whether we're running in frozen mode
            if getattr(sys, 'frozen', False):
                # Running as compiled exe
                icon_path = os.path.join(sys._MEIPASS, 'assets', 'icon.ico')
            else:
                # Running in development environment
                current_dir = os.path.dirname(os.path.abspath(__file__))
                gui_dir = os.path.dirname(os.path.dirname(current_dir))
                src_dir = os.path.dirname(gui_dir)
                icon_path = os.path.join(src_dir, 'assets', 'icon.ico')
            
            # Set window icon
            if os.path.exists(icon_path):
                window.setWindowIcon(QIcon(icon_path))
            
            # Set taskbar icon (Windows only)
            if os.name == 'nt':
                # Create a unique app ID for Windows taskbar
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception as e:
            print(f"Failed to set application icon: {str(e)}")
            
    @staticmethod
    def browse_folder(parent, title="Select Folder", start_dir=""):
        """
        Show a folder browser dialog.
        
        Args:
            parent: Parent window
            title: Dialog title
            start_dir: Starting directory
            
        Returns:
            Selected folder path or empty string if canceled
        """
        folder = QFileDialog.getExistingDirectory(parent, title, start_dir)
        return folder
    
    @staticmethod
    def show_error(parent, title, message):
        """
        Show an error message dialog.
        
        Args:
            parent: Parent window
            title: Dialog title
            message: Error message
        """
        QMessageBox.critical(parent, title, message)
        
    @staticmethod
    def show_warning(parent, title, message):
        """
        Show a warning message dialog.
        
        Args:
            parent: Parent window
            title: Dialog title
            message: Warning message
        """
        QMessageBox.warning(parent, title, message)
        
    @staticmethod
    def show_info(parent, title, message):
        """
        Show an information message dialog.
        
        Args:
            parent: Parent window
            title: Dialog title
            message: Information message
        """
        QMessageBox.information(parent, title, message)
        
    @staticmethod
    def show_question(parent, title, message):
        """
        Show a question message dialog.
        
        Args:
            parent: Parent window
            title: Dialog title
            message: Question message
            
        Returns:
            True if Yes was clicked, False otherwise
        """
        reply = QMessageBox.question(
            parent, title, message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return reply == QMessageBox.Yes
    
    @staticmethod
    def open_folder(folder_path):
        """
        Open a folder in the file explorer.
        
        Args:
            folder_path: Path to the folder to open
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(folder_path):
                os.makedirs(folder_path, exist_ok=True)
                
            # Open folder in file explorer
            if os.name == 'nt':  # Windows
                os.startfile(folder_path)
            elif os.name == 'posix':  # macOS and Linux
                if sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', folder_path])
                else:  # Linux
                    subprocess.run(['xdg-open', folder_path])
            return True
        except Exception as e:
            print(f"Could not open folder: {str(e)}")
            return False
    
    @staticmethod
    def open_log_file():
        """
        Open the application log file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            log_file = os.path.join(os.path.expanduser("~"), '.yt_downloader.log')
            
            if not os.path.exists(log_file):
                return False
                
            # Open log file with default text editor
            if os.name == 'nt':  # Windows
                os.startfile(log_file)
            elif os.name == 'posix':  # macOS and Linux
                if sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', log_file])
                else:  # Linux
                    subprocess.run(['xdg-open', log_file])
            return True
        except Exception as e:
            print(f"Error opening log file: {str(e)}")
            return False 