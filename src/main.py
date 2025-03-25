import tkinter as tk
from ttkthemes import ThemedTk
import tkinter.ttk as ttk
import yt_dlp
import os
import configparser
import threading
import queue
import logging
import traceback
from tkinter import filedialog
from collections import defaultdict
import re
import time
import socket
import sys
import subprocess
import ctypes

# Helper function to get the correct path for bundled resources
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=os.path.join(os.path.expanduser("~"), '.yt_downloader.log')
)
logger = logging.getLogger('yt_downloader')

# Add debug logging for FFmpeg path
logger.info(f"FFmpeg path: {ffmpeg_executable}")
if not os.path.exists(ffmpeg_executable):
    logger.error(f"FFmpeg not found at: {ffmpeg_executable}")

# Queue for thread communication
q = queue.Queue()

# Global variables
format_map = {}
title_saved = False
current_download_phase = None
progress_state = [0, None]  # [current phase index, current filename]
download_sequence = []
active_threads = []  # Keep track of active threads

# Config file path
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".yt_downloader_config.ini")

# Global variable to store the last downloaded file path
last_downloaded_file = None

def load_config():
    """Load the download folder from the config file if available."""
    try:
        config = configparser.ConfigParser()
        if os.path.exists(CONFIG_FILE):
            config.read(CONFIG_FILE)
            if 'Settings' in config and 'download_folder' in config['Settings']:
                return config['Settings']['download_folder']
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
    return ""

def save_config(folder):
    """Save the download folder into the config file."""
    try:
        config = configparser.ConfigParser()
        config['Settings'] = {'download_folder': folder}
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        if os.name == 'nt':
            try:
                import ctypes
                FILE_ATTRIBUTE_HIDDEN = 0x02
                ctypes.windll.kernel32.SetFileAttributesW(CONFIG_FILE, FILE_ATTRIBUTE_HIDDEN)
            except Exception as e:
                logger.warning(f"Could not hide config file: {str(e)}")
    except Exception as e:
        logger.error(f"Error saving config: {str(e)}")
        status_label.config(text="Could not save settings")

def format_size(size):
    """Convert bytes to MB for display."""
    try:
        return f"{round(size / 1048576, 2)} MB" if size else "Unknown"
    except (TypeError, ValueError):
        return "Unknown"

def browse_folder():
    """Open a dialog to select the download folder and save it to config."""
    try:
        folder = filedialog.askdirectory()
        if folder:
            folder_entry.delete(0, tk.END)
            folder_entry.insert(0, folder)
            save_config(folder)
    except Exception as e:
        logger.error(f"Error browsing folder: {str(e)}")
        status_label.config(text="Error selecting folder")

def paste_url():
    """Paste clipboard content into URL entry and reset title fields."""
    try:
        clipboard = root.clipboard_get()
        url_var.set(clipboard.strip())
    except tk.TclError:
        status_label.config(text="Nothing to paste from clipboard")
    except Exception as e:
        logger.error(f"Error pasting URL: {str(e)}")
        status_label.config(text="Error pasting URL")
    
    video_title_var.set("")  # Clear title when new URL is pasted
    video_title_entry.config(state="disabled")
    change_title_button.config(state="disabled", text="Edit Title")
    global title_saved
    title_saved = False

def check_network():
    """Check if network is available."""
    try:
        # Try to connect to Google's DNS
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def fetch_formats():
    """Initiate fetching of video formats."""
    url = url_var.get().strip()
    if not url:
        status_label.config(text="Please enter a URL")
        return
    
    # Basic URL validation
    if not (url.startswith('http://') or url.startswith('https://')):
        status_label.config(text="Invalid URL format")
        return
        
    type_choice = type_var.get()
    if type_choice not in ("1", "2", "3"):
        status_label.config(text="Please select a download type")
        return
        
    if not check_network():
        status_label.config(text="Network error - check your connection")
        return
        
    status_label.config(text="Fetching formats...")
    fetch_button.config(state="disabled")
    download_button.config(state="disabled")
    format_combo.set('')
    format_combo['values'] = []
    
    # Create and start the thread
    fetch_thread = threading.Thread(target=fetch_formats_thread, args=(url, type_choice), daemon=True)
    fetch_thread.do_run = True  # Flag for cancellation
    active_threads.append(fetch_thread)
    fetch_thread.start()

def fetch_formats_thread(url, type_choice):
    """Fetch video formats in a separate thread."""
    try:
        # Use 'getpass_getuser()' to get the current user's username
        opts = {
            'quiet': True,
            'socket_timeout': 30,
            'retries': 3
        }
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
        if not info:
            q.put(("error", "Could not retrieve video information"))
            return
            
        q.put(("video_title", info.get('title', '')))
        
        if 'formats' not in info or not info['formats']:
            q.put(("error", "No formats available for this URL"))
            return
            
        formats = info['formats']
        format_groups = defaultdict(list)
        
        if type_choice in ("1", "2"):  # Video + Audio or Video Only
            for f in sorted(formats, key=lambda x: (x.get('height') or 0, x.get('fps') or 0), reverse=True):
                if f.get('vcodec') != 'none' and f.get('acodec') == 'none':
                    key = (f.get('height'), f.get('fps'))
                    format_groups[key].append(f)
        elif type_choice == "3":  # Audio Only
            for f in sorted(formats, key=lambda x: x.get('abr') or 0, reverse=True):
                if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                    key = f.get('abr')
                    format_groups[key].append(f)
                    
        if not format_groups:
            q.put(("error", f"No compatible {'audio' if type_choice == '3' else 'video'} formats found"))
            return
            
        format_list = []
        global format_map
        format_map = {}
        
        for key, group in format_groups.items():
            try:
                best = max(group, key=lambda x: (x.get('filesize') or x.get('filesize_approx') or 0))
                size = best.get('filesize') or best.get('filesize_approx')
                size_str = format_size(size)
                
                if type_choice == '3':
                    abr = best.get('abr', 'Unknown')
                    format_str = f"{abr} kbps - {size_str}"
                else:
                    height = best.get('height', '?')
                    fps = best.get('fps', '')
                    fps_str = f" ({fps}fps)" if fps else ""
                    format_str = f"{height}p{fps_str} - {size_str}"
                    
                format_list.append(format_str)
                format_map[format_str] = (best['format_id'], best.get('ext', 'mp4'))
            except (KeyError, ValueError) as e:
                logger.warning(f"Error processing format: {str(e)}")
                continue
                
        q.put(("formats", format_list))
        
    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Download error: {str(e)}")
        q.put(("error", f"Error: {str(e)}"))
    except yt_dlp.utils.ExtractorError as e:
        logger.error(f"Extractor error: {str(e)}")
        q.put(("error", f"This URL is not supported"))
    except socket.timeout:
        logger.error("Network timeout")
        q.put(("error", "Network timeout - please try again"))
    except Exception as e:
        logger.error(f"Unexpected error in fetch_formats_thread: {str(e)}")
        logger.error(traceback.format_exc())
        q.put(("error", "Error processing URL"))
    finally:
        # Re-enable the fetch button after completion (success or error)
        q.put(("enable_fetch", None))

def toggle_title_edit():
    """Toggle video title entry between editable and locked states."""
    global title_saved
    try:
        if change_title_button['text'] == "Edit title":
            video_title_entry.config(state="normal")
            change_title_button.config(text="Save Title")
            title_saved = False
            status_label.config(text="Edit the title and click 'Save Title'.")
        else:
            if not video_title_var.get().strip():
                status_label.config(text="Title cannot be empty!")
                return
                
            video_title_entry.config(state="disabled")
            change_title_button.config(text="Edit title")
            title_saved = True
            status_label.config(text="Title saved.")
    except Exception as e:
        logger.error(f"Error toggling title edit: {str(e)}")
        status_label.config(text="Error changing title")

def validate_download_path(folder, filename):
    """Validate the download path and create directory if needed."""
    try:
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
            
        # Check if path is writable
        test_file = os.path.join(folder, ".write_test")
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except (PermissionError, OSError):
            return False, "No write permission for this folder"
            
        # Check if file already exists
        if os.path.exists(filename):
            return False, "This file already exists in the directory"
            
        # Check for disk space (rough estimate - 1GB free minimum)
        if os.name == 'posix':
            import shutil
            stats = shutil.disk_usage(folder)
            if stats.free < 1073741824:  # 1GB in bytes
                return False, "Not enough disk space"
                
        return True, ""
    except Exception as e:
        logger.error(f"Error validating download path: {str(e)}")
        return False, "Error validating download path"

def start_download():
    """Start the download with selected options."""
    try:
        global download_sequence, progress_state, current_download_phase
        
        if not title_saved:
            status_label.config(text="Please save the title first.")
            return
            
        url = url_var.get().strip()
        type_choice = type_var.get()
        format_str = format_combo.get()
        folder = folder_entry.get().strip()
        user_title = video_title_var.get().strip()
        
        if not all([url, type_choice, format_str, folder]):
            status_label.config(text="Please fill all fields")
            return
            
        if user_title == "":
            status_label.config(text="Title cannot be empty")
            return
            
        if not os.path.isdir(folder):
            try:
                os.makedirs(folder, exist_ok=True)
            except Exception:
                status_label.config(text="Cannot create download folder")
                return
                
        if not format_str in format_map:
            status_label.config(text="Invalid format selected")
            return
            
        format_id, format_ext = format_map.get(format_str)
        if not format_id:
            status_label.config(text="Invalid format selected")
            return
            
        user_title = sanitize_filename(user_title)
        format_part = format_str.split(" - ")[0]
        
        global download_sequence, progress_state, current_download_phase
        
        if type_choice == '1':
            download_sequence = ["video", "audio"]
            expected_ext = 'mp4'
            ydl_opts = {
                'format': f"{format_id}+bestaudio",
                'merge_output_format': 'mp4',
                'progress_hooks': [progress_hook],
                'no_mtime': True,
                'socket_timeout': 30,
                'retries': 5,
                'ffmpeg_location': ffmpeg_executable,  # Use bundled FFmpeg
            }
        elif type_choice == '2':
            download_sequence = ["video"]
            expected_ext = format_ext
            ydl_opts = {
                'format': format_id,
                'progress_hooks': [progress_hook],
                'no_mtime': True,
                'socket_timeout': 30,
                'retries': 5,
                'ffmpeg_location': ffmpeg_executable,  # Use bundled FFmpeg
            }
        elif type_choice == '3':
            download_sequence = ["audio"]
            expected_ext = 'mp3'
            ydl_opts = {
                'format': format_id,
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
                'progress_hooks': [progress_hook],
                'no_mtime': True,
                'socket_timeout': 30,
                'retries': 5,
                'ffmpeg_location': ffmpeg_executable,  # Use bundled FFmpeg
            }
            
        base_filename = sanitize_filename(f"{user_title} - {format_part}")
        full_filename = os.path.join(folder, f"{base_filename}.{expected_ext}")
        
        # Validate the download path
        valid, error_msg = validate_download_path(folder, full_filename)
        if not valid:
            status_label.config(text=error_msg)
            return
            
        ydl_opts['outtmpl'] = os.path.join(folder, f"{base_filename}.%(ext)s")
        
        if not check_network():
            status_label.config(text="Network error - check your connection")
            return
            
        progress_state = [0, None]
        current_download_phase = None
        status_label.config(text="Starting download...")
        download_button.config(state="disabled")
        
        # Set the initial phase immediately
        current_download_phase = download_sequence[0]
        q.put(("start_phase", current_download_phase))
        progress['value'] = 0
        
        # Create and start the thread
        download_thread_obj = threading.Thread(
            target=download_thread, 
            args=(url, ydl_opts, type_choice, folder, base_filename, expected_ext), 
            daemon=True
        )
        download_thread_obj.do_run = True  # Flag for cancellation
        active_threads.append(download_thread_obj)
        download_thread_obj.start()
        
    except Exception as e:
        logger.error(f"Error starting download: {str(e)}")
        logger.error(traceback.format_exc())
        status_label.config(text="Error starting download")
        download_button.config(state="normal")

def download_thread(url, ydl_opts, type_choice, folder, base_filename, expected_ext):
    """Perform the download in a separate thread and set modification time after download."""
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
                
            if not info:
                q.put(("download_error", "Download failed: No video information"))
                return
                
            if type_choice == '3':  # Audio only
                filename = os.path.join(folder, f"{base_filename}.mp3")
            else:
                filename = ydl.prepare_filename(info)
                if type_choice == '1':  # For video+audio, force mp4 extension
                    filename = filename.replace('.webm', '.mp4').replace('.mkv', '.mp4')
                    
            # Verify file exists after download
            if not os.path.exists(filename):
                alternative = os.path.join(folder, f"{base_filename}.{expected_ext}")
                if os.path.exists(alternative):
                    filename = alternative
                else:
                    # Find any file with this base name
                    possible_files = [f for f in os.listdir(folder) if f.startswith(base_filename)]
                    if possible_files:
                        filename = os.path.join(folder, possible_files[0])
                    else:
                        q.put(("download_error", "Download failed: File not found after download"))
                        return
                        
            # Set file modification time to current time
            current_time = time.time()
            os.utime(filename, (current_time, current_time))
            
            q.put(("download_complete", filename))
            
    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Download error: {str(e)}")
        q.put(("download_error", f"Download failed: {str(e)}"))
    except Exception as e:
        logger.error(f"Unexpected error in download_thread: {str(e)}")
        logger.error(traceback.format_exc())
        q.put(("download_error", f"Download failed: {str(e)}"))

def progress_hook(d):
    """Update download progress with phase-specific messages."""
    global progress_state, download_sequence, current_download_phase
    try:
        if d['status'] == 'downloading':
            # If not already set, set the current phase on first downloading event
            if current_download_phase is None and progress_state[0] < len(download_sequence):
                current_download_phase = download_sequence[progress_state[0]]
                q.put(("start_phase", current_download_phase))
                
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            
            if total:
                percent = min((downloaded / total) * 100, 100)  # Cap at 100%
                speed = d.get('speed')
                speed_mbps = round(speed / 1048576, 1) if speed else None
                eta = d.get('eta')
                eta_str = f" - ETA: {format_time(eta)}" if eta else ""
                
                q.put(("progress", percent, speed_mbps, eta_str))
            else:
                downloaded_mb = round(downloaded / 1048576, 1)
                q.put(("progress_unknown", downloaded_mb))
                
        elif d['status'] == 'finished':
            # Advance to the next phase if available; otherwise, switch to merging.
            if progress_state[0] < len(download_sequence) - 1:
                progress_state[0] += 1
                current_download_phase = download_sequence[progress_state[0]]
                q.put(("start_phase", current_download_phase))
            else:
                q.put(("start_phase", "merging"))
                
        elif d['status'] == 'processing':
            q.put(("start_phase", "merging"))
            
    except Exception as e:
        logger.error(f"Error in progress_hook: {str(e)}")

def format_time(seconds):
    """Format seconds into mm:ss format."""
    if not seconds:
        return "??:??"
    minutes, seconds = divmod(seconds, 60)
    return f"{int(minutes):02d}:{int(seconds):02d}"

def check_queue():
    """Process queue updates from threads."""
    global title_saved, current_download_phase
    try:
        while True:
            message = q.get_nowait()
            
            if message[0] == "formats":
                format_list = message[1]
                format_combo['values'] = format_list
                if format_list:
                    format_combo.current(0)
                    status_label.config(text="Formats fetched. Select a format.")
                    download_button.config(state="normal")
                else:
                    status_label.config(text="No formats available.")
                    
            elif message[0] == "video_title":
                video_title_var.set(message[1])
                video_title_entry.config(state="disabled")
                change_title_button.config(state="normal", text="Edit title")
                title_saved = True
                
            elif message[0] == "error":
                status_label.config(text=f"Error: {message[1]}")
                fetch_button.config(state="normal")
                
            elif message[0] == "enable_fetch":
                fetch_button.config(state="normal")
                
            elif message[0] == "start_phase":
                phase = message[1]
                current_download_phase = phase
                
                if phase in ("video", "audio"):
                    status_label.config(text=f"Downloading {phase}... 0.0%")
                    progress['value'] = 0
                elif phase == "merging":
                    status_label.config(text="Merging formats...")
                    progress['value'] = 100
                    
            elif message[0] == "progress":
                percent, speed_mbps, eta_str = message[1], message[2], message[3] if len(message) > 3 else ""
                
                if current_download_phase in ("video", "audio"):
                    if speed_mbps is not None:
                        status_label.config(text=f"Downloading {current_download_phase}... {percent:.1f}% ({speed_mbps} MB/s){eta_str}")
                    else:
                        status_label.config(text=f"Downloading {current_download_phase}... {percent:.1f}%{eta_str}")
                    progress['value'] = percent
                    
            elif message[0] == "progress_unknown":
                downloaded_mb = message[1]
                status_label.config(text=f"Downloading {current_download_phase}... {downloaded_mb} MB downloaded (size unknown)")
                
            elif message[0] == "download_complete":
                filename = message[1] if len(message) > 1 else ""
                status_label.config(text="Download successful!")
                progress['value'] = 100
                download_button.config(state="normal")
                fetch_button.config(state="normal")  # Re-enable fetch button after download
                
                # Store the last downloaded file path
                if filename and os.path.exists(filename):
                    global last_downloaded_file
                    last_downloaded_file = filename
                        
            elif message[0] == "download_error":
                error_msg = message[1] if len(message) > 1 else "Unknown error"
                status_label.config(text=f"Error: {error_msg}")
                download_button.config(state="normal")
                fetch_button.config(state="normal")  # Re-enable fetch button on error
                
    except queue.Empty:
        pass
    finally:
        root.after(100, check_queue)

def on_closing():
    """Save folder path on exit and clean up threads."""
    try:
        current_folder = folder_entry.get().strip()
        if current_folder:
            save_config(current_folder)
            
        # Clean up log handlers
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
            
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")
    finally:
        root.destroy()

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

def open_download_folder():
    """Open the folder specified in the download folder entry."""
    try:
        # Get the folder from the entry field
        folder = folder_entry.get().strip()
        
        if folder and os.path.exists(folder):
            if os.name == 'nt':  # Windows
                # Using subprocess instead of os.system for better handling of paths
                subprocess.Popen(f'explorer "{os.path.normpath(folder)}"', shell=True)
            elif os.name == 'posix':  # macOS or Linux
                if sys.platform == 'darwin':  # macOS
                    os.system(f'open "{folder}"')
                else:  # Linux
                    os.system(f'xdg-open "{folder}"')
            status_label.config(text=f"Opened folder: {folder}")
        else:
            # If folder doesn't exist, prompt the user to select one
            status_label.config(text="Please select a valid download folder")
            browse_folder()
            
    except Exception as e:
        logger.error(f"Error opening folder: {str(e)}")
        status_label.config(text="Could not open folder")

# Setup main window
root = ThemedTk(theme="equilux")
root.title("ADM Video Downloader")
root.minsize(500, 370)
root.resizable(False, False)

# Set application icon for both taskbar and window title
try:
    # Determine icon path based on whether we're running in frozen mode
    icon_path = resource_path('icon.ico') if getattr(sys, 'frozen', False) else 'icon.ico'
    
    # Set window icon
    root.iconbitmap(icon_path)
    
    # Set taskbar icon (Windows only)
    if os.name == 'nt':
        # Create a unique app ID for Windows taskbar
        app_id = 'adm.videodownloader.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
except Exception as e:
    logger.error(f"Failed to set application icon: {str(e)}")

# Set the title bar color to match the theme (Windows only)
if os.name == 'nt':
    try:
        root.attributes("-transparentcolor", "")  # Reset any transparent color
        style = ttk.Style()
        bg_color = style.lookup('TFrame', 'background')
        root.configure(bg=bg_color)
        # Use the theme's background color
        root.update()
        HWND = ctypes.windll.user32.GetParent(root.winfo_id())
        DWMWA_CAPTION_COLOR = 35
        # Convert from #RRGGBB to COLORREF (0x00BBGGRR)
        if bg_color.startswith('#'):
            r = int(bg_color[1:3], 16)
            g = int(bg_color[3:5], 16)
            b = int(bg_color[5:7], 16)
            color = ctypes.c_int(r | (g << 8) | (b << 16))
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                HWND, DWMWA_CAPTION_COLOR, ctypes.byref(color), ctypes.sizeof(color)
            )
    except Exception as e:
        # If this fails, it's not critical - just log and continue
        logger.error(f"Failed to set title bar color: {str(e)}")

style = ttk.Style()
bg_color = style.lookup('TFrame', 'background')
root.configure(bg=bg_color)
style.configure("TLabel", font=("Segoe UI", 10))
style.configure("TButton", font=("Segoe UI", 10))
style.configure("TRadiobutton", font=("Segoe UI", 10))
style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))

root.columnconfigure(1, weight=1)

url_label = ttk.Label(root, text="Video URL:")
url_label.grid(row=1, column=0, sticky="e", padx=5, pady=2)
url_var = tk.StringVar()
url_entry = ttk.Entry(root, textvariable=url_var, width=40, state="disabled")
url_entry.grid(row=1, column=1, padx=5, pady=2)
paste_button = ttk.Button(root, text="Paste", command=paste_url)
paste_button.grid(row=1, column=2, padx=5, pady=2)

video_title_label = ttk.Label(root, text="Video Title:")
video_title_label.grid(row=2, column=0, sticky="e", padx=5, pady=2)
video_title_var = tk.StringVar()
video_title_entry = ttk.Entry(root, textvariable=video_title_var, width=40, state="disabled")
video_title_entry.grid(row=2, column=1, padx=5, pady=2)
change_title_button = ttk.Button(root, text="Edit title", command=toggle_title_edit, state="disabled")
change_title_button.grid(row=2, column=2, padx=5, pady=2)

type_label = ttk.Label(root, text="Download Type:")
type_label.grid(row=3, column=0, sticky="e", padx=5, pady=2)
type_var = tk.StringVar(value="1")
radio1 = ttk.Radiobutton(root, text="Video + Audio (MP4)", variable=type_var, value="1")
radio1.grid(row=4, column=1, sticky="w", padx=5, pady=2)
radio2 = ttk.Radiobutton(root, text="Video Only (MP4)", variable=type_var, value="2")
radio2.grid(row=5, column=1, sticky="w", padx=5, pady=2)
radio3 = ttk.Radiobutton(root, text="Audio Only (MP3)", variable=type_var, value="3")
radio3.grid(row=6, column=1, sticky="w", padx=5, pady=2)

fetch_button = ttk.Button(root, text="Fetch Formats", command=fetch_formats)
fetch_button.grid(row=7, column=1, padx=5, pady=2)

format_label = ttk.Label(root, text="Select Format:")
format_label.grid(row=8, column=0, sticky="e", padx=5, pady=2)
format_combo = ttk.Combobox(root, state="readonly", width=40)
format_combo.grid(row=8, column=1, padx=5, pady=2)

folder_label = ttk.Label(root, text="Download Folder:")
folder_label.grid(row=9, column=0, sticky="e", padx=5, pady=2)
folder_entry = ttk.Entry(root, width=40)
folder_entry.grid(row=9, column=1, padx=5, pady=2)
browse_button = ttk.Button(root, text="Browse", command=browse_folder)
browse_button.grid(row=9, column=2, padx=5, pady=2)

saved_folder = load_config()
if saved_folder:
    folder_entry.insert(0, saved_folder)

# Create a frame to center the buttons
button_frame = ttk.Frame(root)
button_frame.grid(row=10, column=0, columnspan=3, pady=10)

# Add both buttons to the frame with a small gap between them
open_folder_button = ttk.Button(button_frame, text="Open Folder", command=open_download_folder)
open_folder_button.pack(side=tk.LEFT, padx=10)

download_button = ttk.Button(button_frame, text="Download", command=start_download, state="disabled")
download_button.pack(side=tk.LEFT, padx=10)

progress = ttk.Progressbar(root, orient="horizontal", mode="determinate")
progress.grid(row=11, column=0, columnspan=3, sticky="ew", padx=5, pady=2)
status_label = ttk.Label(root, text="")
status_label.grid(row=12, column=0, columnspan=3, padx=5, pady=2)

# Create a version label centered
version_label = ttk.Label(root, text="github.com/aymandeepmind", font=("Segoe UI", 8))
version_label.grid(row=13, column=0, columnspan=3, pady=2)

root.after(100, check_queue)
root.protocol("WM_DELETE_WINDOW", on_closing)

# Try to load the saved folder on startup
try:
    saved_folder = load_config()
    if saved_folder and os.path.exists(saved_folder):
        folder_entry.delete(0, tk.END)
        folder_entry.insert(0, saved_folder)
except Exception as e:
    logger.error(f"Error loading saved folder: {str(e)}")

root.mainloop()
