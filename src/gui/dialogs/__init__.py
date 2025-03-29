"""
Dialog windows for the Video Downloader application.
These are separate windows used for settings and other interactions.
"""

from .settings_dialog import FormatSelectionDialog
from .about_dialog import show_about_dialog

__all__ = [
    'FormatSelectionDialog',
    'show_about_dialog'
] 