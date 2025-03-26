import tkinter as tk
from ttkthemes import ThemedTk
import queue
import sys
import os

# Adjust import paths dynamically
if getattr(sys, 'frozen', False):
    # Running as compiled .exe
    from src.gui import VideoDownloaderApp
else:
    # Running directly as .py
    # Add the parent directory to sys.path to make imports work
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    from gui import VideoDownloaderApp

def main():
    """Main entry point for the application."""
    # Setup main window with theme
    root = ThemedTk(theme="equilux")
    
    # Create app
    app = VideoDownloaderApp(root)
    
    # Set closing protocol
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start main loop
    root.mainloop()

if __name__ == "__main__":
    main() 