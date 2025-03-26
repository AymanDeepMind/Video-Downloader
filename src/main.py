import tkinter as tk
from ttkthemes import ThemedTk
import queue
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