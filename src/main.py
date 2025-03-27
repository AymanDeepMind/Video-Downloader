import sys
import os
import ctypes
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

# Adjust import paths dynamically
if getattr(sys, 'frozen', False):
    # Running as compiled .exe
    from gui import VideoDownloaderApp
else:
    # Running directly as .py
    # Add the parent directory to sys.path to make imports work
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    from gui import VideoDownloaderApp

def apply_dark_theme(app):
    """Apply a dark theme to the application."""
    dark_palette = QPalette()
    
    # Set color roles from dark to light
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(35, 35, 35))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)
    
    # Apply the palette
    app.setPalette(dark_palette)
    
    # Additional styling
    app.setStyleSheet("""
        QToolTip { 
            color: #ffffff; 
            background-color: #2a2a2a; 
            border: 1px solid #767676; 
        }
        QMessageBox { 
            background-color: #2d2d2d; 
        }
    """)
    
    # Apply dark title bar on Windows
    if os.name == 'nt':
        try:
            # Enable dark title bar on Windows 10 1809 or later
            app.setProperty("darkMode", True)
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            try:
                # Try to use the dark mode API available in newer Windows 10/11 versions
                hwnd = int(app.activeWindow().winId())
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    DWMWA_USE_IMMERSIVE_DARK_MODE,
                    ctypes.byref(ctypes.c_bool(True)),
                    ctypes.sizeof(ctypes.c_bool)
                )
            except:
                # Fallback to older method
                app.setStyle("fusion")
        except Exception as e:
            print(f"Error applying dark title bar: {e}")

def main():
    """Main entry point for the application."""
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Set application style to Fusion for more modern look
    app.setStyle('Fusion')
    
    # Apply dark theme
    apply_dark_theme(app)
    
    # Create app window
    window = VideoDownloaderApp()
    
    # Apply dark title bar specifically to the window (for Windows)
    if os.name == 'nt':
        try:
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            hwnd = int(window.winId())
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(ctypes.c_bool(True)),
                ctypes.sizeof(ctypes.c_bool)
            )
        except Exception as e:
            print(f"Error applying dark title bar to window: {e}")
    
    window.show()
    
    # Start main loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 