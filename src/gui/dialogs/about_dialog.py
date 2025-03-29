"""
About dialog for the Video Downloader application.
"""

import webbrowser

def show_about_dialog():
    """
    Show about information by opening the GitHub repository.
    
    This is implemented as a simple function rather than a dialog class
    because the original implementation just opens the GitHub page.
    """
    webbrowser.open("https://github.com/AymanDeepMind/Video-Downloader") 