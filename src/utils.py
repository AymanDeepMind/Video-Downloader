import os
import re
import sys
import socket
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=os.path.join(os.path.expanduser("~"), '.yt_downloader.log')
)
logger = logging.getLogger('yt_downloader')

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def format_size(size):
    """Convert bytes to MB for display."""
    try:
        return f"{round(size / 1048576, 2)} MB" if size else "Unknown"
    except (TypeError, ValueError):
        return "Unknown"

def format_time(seconds):
    """Format seconds into mm:ss format."""
    if not seconds:
        return "??:??"
    minutes, seconds = divmod(seconds, 60)
    return f"{int(minutes):02d}:{int(seconds):02d}"

def check_network():
    """Check if network is available."""
    try:
        # Try to connect to Google's DNS
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def sanitize_filename(name):
    """Replace invalid filename characters with underscores."""
    if not name:
        return "download"
    # First, replace common problematic characters
    sanitized = re.sub(r'[\\/*?:"<>|]', "_", name)
    # Then handle any other special cases or control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f]', "", sanitized)
    # Limit length to avoid path too long errors
    if len(sanitized) > 150:
        sanitized = sanitized[:147] + "..."
    return sanitized

# Set up FFmpeg location for bundled version
if getattr(sys, 'frozen', False):
    # Running as compiled exe
    ffmpeg_path = resource_path('assets/ffmpeg/ffmpeg.exe')
else:
    # Running in development environment
    ffmpeg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'ffmpeg', 'ffmpeg.exe')

# Add FFmpeg directory to environment path for this process only
ffmpeg_dir = os.path.dirname(ffmpeg_path)
os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ["PATH"]

# Set FFmpeg executable path
ffmpeg_executable = ffmpeg_path

# Add debug logging for FFmpeg path
logger.info(f"FFmpeg path: {ffmpeg_executable}")
if not os.path.exists(ffmpeg_executable):
    logger.error(f"FFmpeg not found at: {ffmpeg_executable}") 