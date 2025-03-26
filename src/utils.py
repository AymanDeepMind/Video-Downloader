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
        # If not running as exe, use the src directory's parent
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
    try:
        # First try _MEIPASS path (PyInstaller temp directory)
        ffmpeg_path = os.path.join(sys._MEIPASS, 'assets', 'ffmpeg', 'ffmpeg.exe')
        if not os.path.exists(ffmpeg_path):
            # If not found, try relative to executable
            ffmpeg_path = os.path.join(os.path.dirname(sys.executable), 'assets', 'ffmpeg', 'ffmpeg.exe')
    except Exception as e:
        logger.error(f"Error setting ffmpeg path in frozen state: {str(e)}")
        ffmpeg_path = None
else:
    # Running in development environment
    try:
        # When running directly, ffmpeg should be in src/assets/ffmpeg
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ffmpeg_path = os.path.join(current_dir, 'assets', 'ffmpeg', 'ffmpeg.exe')
    except Exception as e:
        logger.error(f"Error setting ffmpeg path in development: {str(e)}")
        ffmpeg_path = None

# Add FFmpeg directory to environment path for this process only
if ffmpeg_path and os.path.exists(ffmpeg_path):
    ffmpeg_dir = os.path.dirname(ffmpeg_path)
    os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ["PATH"]
    ffmpeg_executable = ffmpeg_path
    logger.info(f"FFmpeg found at: {ffmpeg_executable}")
else:
    logger.error("FFmpeg not found in expected locations")
    # Try to find ffmpeg in the current directory structure
    ffmpeg_executable = None
    search_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
    for root, dirs, files in os.walk(search_dir):
        if 'ffmpeg.exe' in files:
            ffmpeg_executable = os.path.join(root, 'ffmpeg.exe')
            logger.info(f"Found FFmpeg at alternate location: {ffmpeg_executable}")
            # Update PATH with the found location
            os.environ["PATH"] = os.path.dirname(ffmpeg_executable) + os.pathsep + os.environ["PATH"]
            break
    
    if not ffmpeg_executable:
        logger.error("FFmpeg not found anywhere in the application directory") 