import tkinter as tk
from ttkthemes import ThemedTk
import tkinter.ttk as ttk
import os
import sys
import ctypes
import threading
import queue
import traceback
import subprocess
from tkinter import filedialog

from utils import resource_path, logger, check_network
from config import load_config, save_config
from downloader import Downloader

class VideoDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.queue = queue.Queue()
        self.title_saved = False
        self.downloader = Downloader(self.queue)
        self.last_downloaded_file = None
        
        self.setup_ui()
        self.load_saved_config()
        
        # Start queue checking
        self.root.after(100, self.check_queue)
        
    def setup_ui(self):
        """Set up the user interface."""
        self.root.title("ADM Video Downloader v.1.1.0")
        self.root.minsize(500, 370)
        self.root.resizable(False, False)
        
        # Set application icon
        self.setup_app_icon()
        
        # Set the title bar color to match the theme (Windows only)
        self.setup_title_bar()
        
        # Configure styles
        self.setup_styles()
        
        # Configure grid
        self.root.columnconfigure(1, weight=1)
        
        # Create widgets
        self.create_widgets()
        
    def setup_app_icon(self):
        """Set application icon for both taskbar and window title."""
        try:
            # Determine icon path based on whether we're running in frozen mode
            if getattr(sys, 'frozen', False):
                # Running as compiled exe
                icon_path = resource_path('assets/icon.ico')
            else:
                # Running in development environment
                icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'icon.ico')
            
            # Set window icon
            self.root.iconbitmap(icon_path)
            
            # Set taskbar icon (Windows only)
            if os.name == 'nt':
                # Create a unique app ID for Windows taskbar
                app_id = 'adm.videodownloader.1.0'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception as e:
            logger.error(f"Failed to set application icon: {str(e)}")
            
    def setup_title_bar(self):
        """Set the title bar color to match the theme (Windows only)."""
        if os.name == 'nt':
            try:
                self.root.attributes("-transparentcolor", "")  # Reset any transparent color
                style = ttk.Style()
                bg_color = style.lookup('TFrame', 'background')
                self.root.configure(bg=bg_color)
                # Use the theme's background color
                self.root.update()
                HWND = ctypes.windll.user32.GetParent(self.root.winfo_id())
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
                
    def setup_styles(self):
        """Configure the ttk styles."""
        style = ttk.Style()
        bg_color = style.lookup('TFrame', 'background')
        self.root.configure(bg=bg_color)
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("TRadiobutton", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
        
    def create_widgets(self):
        """Create and place all UI widgets."""
        # URL Input
        url_label = ttk.Label(self.root, text="Video URL:")
        url_label.grid(row=1, column=0, sticky="e", padx=5, pady=2)
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(self.root, textvariable=self.url_var, width=40)
        self.url_entry.grid(row=1, column=1, padx=5, pady=2)
        paste_button = ttk.Button(self.root, text="Paste", command=self.paste_url)
        paste_button.grid(row=1, column=2, padx=5, pady=2)

        # Video Title
        video_title_label = ttk.Label(self.root, text="Video Title:")
        video_title_label.grid(row=2, column=0, sticky="e", padx=5, pady=2)
        self.video_title_var = tk.StringVar()
        self.video_title_entry = ttk.Entry(self.root, textvariable=self.video_title_var, width=40, state="disabled")
        self.video_title_entry.grid(row=2, column=1, padx=5, pady=2)
        self.change_title_button = ttk.Button(self.root, text="Edit title", command=self.toggle_title_edit, state="disabled")
        self.change_title_button.grid(row=2, column=2, padx=5, pady=2)

        # Download Type Radio Buttons
        type_label = ttk.Label(self.root, text="Download Type:")
        type_label.grid(row=3, column=0, sticky="e", padx=5, pady=2)
        self.type_var = tk.StringVar(value="1")
        radio1 = ttk.Radiobutton(self.root, text="Video + Audio (MP4)", variable=self.type_var, value="1")
        radio1.grid(row=4, column=1, sticky="w", padx=5, pady=2)
        radio2 = ttk.Radiobutton(self.root, text="Video Only (MP4)", variable=self.type_var, value="2")
        radio2.grid(row=5, column=1, sticky="w", padx=5, pady=2)
        radio3 = ttk.Radiobutton(self.root, text="Audio Only (MP3)", variable=self.type_var, value="3")
        radio3.grid(row=6, column=1, sticky="w", padx=5, pady=2)

        # Create a frame for the buttons in row 7
        button_frame = ttk.Frame(self.root)
        button_frame.grid(row=7, column=1, padx=5, pady=2, sticky="ew")
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        # Add Calibrate and Fetch Formats buttons to the frame
        self.calibrate_button = ttk.Button(button_frame, text="Calibrate", command=self.start_calibration)
        self.calibrate_button.grid(row=0, column=0, padx=(0, 5), sticky="e")

        self.fetch_button = ttk.Button(button_frame, text="Fetch Formats", command=self.fetch_formats)
        self.fetch_button.grid(row=0, column=1, padx=(5, 0), sticky="w")

        # Format Selection
        format_label = ttk.Label(self.root, text="Select Format:")
        format_label.grid(row=8, column=0, sticky="e", padx=5, pady=2)
        self.format_combo = ttk.Combobox(self.root, state="readonly", width=40)
        self.format_combo.grid(row=8, column=1, padx=5, pady=2)

        # Download Folder
        folder_label = ttk.Label(self.root, text="Download Folder:")
        folder_label.grid(row=9, column=0, sticky="e", padx=5, pady=2)
        self.folder_entry = ttk.Entry(self.root, width=40)
        self.folder_entry.grid(row=9, column=1, padx=5, pady=2)
        browse_button = ttk.Button(self.root, text="Browse", command=self.browse_folder)
        browse_button.grid(row=9, column=2, padx=5, pady=2)

        # Create a frame to center the buttons
        action_button_frame = ttk.Frame(self.root)
        action_button_frame.grid(row=10, column=0, columnspan=3, pady=10)

        # Download and Open Folder Buttons
        open_folder_button = ttk.Button(action_button_frame, text="Open Folder", command=self.open_download_folder)
        open_folder_button.pack(side=tk.LEFT, padx=10)
        self.download_button = ttk.Button(action_button_frame, text="Download", command=self.start_download, state="disabled")
        self.download_button.pack(side=tk.LEFT, padx=10)

        # Progress Bar and Status
        self.progress = ttk.Progressbar(self.root, orient="horizontal", mode="determinate")
        self.progress.grid(row=11, column=0, columnspan=3, sticky="ew", padx=5, pady=2)
        self.status_label = ttk.Label(self.root, text="")
        self.status_label.grid(row=12, column=0, columnspan=3, padx=5, pady=2)

        # Create a version label centered
        version_label = ttk.Label(
            self.root, 
            text="                 Calibrate regularly to enhance download speeds. github.com/aymandeepmind", 
            font=("Segoe UI", 8)
        )
        version_label.grid(row=13, column=0, columnspan=3, pady=2, sticky="ew")
        
    def load_saved_config(self):
        """Load the saved configuration."""
        try:
            saved_folder = load_config()
            if saved_folder and os.path.exists(saved_folder):
                self.folder_entry.delete(0, tk.END)
                self.folder_entry.insert(0, saved_folder)
        except Exception as e:
            logger.error(f"Error loading saved folder: {str(e)}")
            
    def check_queue(self):
        """Process queue updates from threads."""
        try:
            while True:
                message = self.queue.get_nowait()
                
                if message[0] == "formats":
                    format_list = message[1]
                    self.format_combo['values'] = format_list
                    if format_list:
                        self.format_combo.current(0)
                        self.status_label.config(text="Formats fetched. Select a format.")
                        self.download_button.config(state="normal")
                    else:
                        self.status_label.config(text="No formats available.")
                        
                elif message[0] == "video_title":
                    self.video_title_var.set(message[1])
                    self.video_title_entry.config(state="disabled")
                    self.change_title_button.config(state="normal", text="Edit title")
                    self.title_saved = True
                    
                elif message[0] == "error":
                    self.status_label.config(text=f"Error: {message[1]}")
                    self.fetch_button.config(state="normal")
                    self.calibrate_button.config(state="normal")
                    
                elif message[0] == "enable_fetch":
                    self.fetch_button.config(state="normal")
                    
                elif message[0] == "start_phase":
                    phase = message[1]
                    
                    if phase in ("video", "audio"):
                        self.status_label.config(text=f"Downloading {phase}... 0.0%")
                        self.progress['value'] = 0
                    elif phase == "merging":
                        self.status_label.config(text="Merging formats...")
                        self.progress['value'] = 100
                        
                elif message[0] == "progress":
                    percent, speed_mbps, eta_str = message[1], message[2], message[3] if len(message) > 3 else ""
                    
                    current_phase = self.downloader.current_download_phase
                    if current_phase in ("video", "audio"):
                        if speed_mbps is not None:
                            self.status_label.config(text=f"Downloading {current_phase}... {percent:.1f}% ({speed_mbps} MB/s){eta_str}")
                        else:
                            self.status_label.config(text=f"Downloading {current_phase}... {percent:.1f}%{eta_str}")
                        self.progress['value'] = percent
                        
                elif message[0] == "progress_unknown":
                    downloaded_mb = message[1]
                    current_phase = self.downloader.current_download_phase
                    self.status_label.config(text=f"Downloading {current_phase}... {downloaded_mb} MB downloaded (size unknown)")
                    
                elif message[0] == "download_complete":
                    filename = message[1] if len(message) > 1 else ""
                    self.status_label.config(text="Download successful!")
                    self.progress['value'] = 100
                    self.download_button.config(state="normal")
                    self.fetch_button.config(state="normal")
                    self.calibrate_button.config(state="normal")
                    
                    # Store the last downloaded file path
                    if filename and os.path.exists(filename):
                        self.last_downloaded_file = filename
                            
                elif message[0] == "download_error":
                    error_msg = message[1] if len(message) > 1 else "Unknown error"
                    self.status_label.config(text=f"Error: {error_msg}")
                    self.download_button.config(state="normal")
                    self.fetch_button.config(state="normal")
                    self.calibrate_button.config(state="normal")
                    
                # Handle calibration messages
                elif message[0] == "calibrate_start":
                    self.calibrate_button.config(state="disabled")
                    self.fetch_button.config(state="disabled")
                    self.download_button.config(state="disabled")
                    self.progress['value'] = 0
                    self.status_label.config(text="Starting calibration...")
                    
                elif message[0] == "calibrate_end":
                    self.calibrate_button.config(state="normal")
                    self.fetch_button.config(state="normal")
                    
                elif message[0] == "calibration_progress":
                    percent = message[1]
                    status_text = message[2] if len(message) > 2 else f"Calibrating internet... ({percent:.2f}%)"
                    self.progress['value'] = percent
                    self.status_label.config(text=status_text)
                    
                elif message[0] == "calibration_result":
                    fragments = message[1]
                    speed = message[2] if len(message) > 2 else 0
                    self.progress['value'] = 100
                    self.status_label.config(text=f"Calibration complete! Optimal setting: {fragments} fragments ({speed:.1f} MB/s)")
                    
                elif message[0] == "calibration_error":
                    error_msg = message[1]
                    self.status_label.config(text=f"Calibration error: {error_msg}")
                    self.calibrate_button.config(state="normal")
                    self.fetch_button.config(state="normal")
                    self.progress['value'] = 0
                    
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.check_queue)
            
    def browse_folder(self):
        """Open a dialog to select the download folder and save it to config."""
        try:
            folder = filedialog.askdirectory()
            if folder:
                self.folder_entry.delete(0, tk.END)
                self.folder_entry.insert(0, folder)
                save_config(folder)
        except Exception as e:
            logger.error(f"Error browsing folder: {str(e)}")
            self.status_label.config(text="Error selecting folder")
            
    def paste_url(self):
        """Paste clipboard content into URL entry and reset title fields."""
        try:
            clipboard = self.root.clipboard_get()
            self.url_var.set(clipboard.strip())
        except tk.TclError:
            self.status_label.config(text="Nothing to paste from clipboard")
        except Exception as e:
            logger.error(f"Error pasting URL: {str(e)}")
            self.status_label.config(text="Error pasting URL")
        
        self.video_title_var.set("")  # Clear title when new URL is pasted
        self.video_title_entry.config(state="disabled")
        self.change_title_button.config(state="disabled", text="Edit Title")
        self.title_saved = False
        
    def toggle_title_edit(self):
        """Toggle video title entry between editable and locked states."""
        try:
            if self.change_title_button['text'] == "Edit title":
                self.video_title_entry.config(state="normal")
                self.change_title_button.config(text="Save Title")
                self.title_saved = False
                self.status_label.config(text="Edit the title and click 'Save Title'.")
            else:
                if not self.video_title_var.get().strip():
                    self.status_label.config(text="Title cannot be empty!")
                    return
                    
                self.video_title_entry.config(state="disabled")
                self.change_title_button.config(text="Edit title")
                self.title_saved = True
                self.status_label.config(text="Title saved.")
        except Exception as e:
            logger.error(f"Error toggling title edit: {str(e)}")
            self.status_label.config(text="Error changing title")
            
    def fetch_formats(self):
        """Initiate fetching of video formats."""
        url = self.url_var.get().strip()
        if not url:
            self.status_label.config(text="Please enter a URL")
            return
        
        # Basic URL validation
        if not (url.startswith('http://') or url.startswith('https://')):
            self.status_label.config(text="Invalid URL format")
            return
            
        type_choice = self.type_var.get()
        if type_choice not in ("1", "2", "3"):
            self.status_label.config(text="Please select a download type")
            return
            
        if not check_network():
            self.status_label.config(text="Network error - check your connection")
            return
            
        self.status_label.config(text="Fetching formats...")
        self.fetch_button.config(state="disabled")
        self.calibrate_button.config(state="disabled")
        self.download_button.config(state="disabled")
        self.format_combo.set('')
        self.format_combo['values'] = []
        
        # Start fetching formats
        self.downloader.fetch_formats(url, type_choice)
        
    def start_calibration(self):
        """Start the internet speed calibration process."""
        if not check_network():
            self.status_label.config(text="Network error - check your connection")
            return
            
        success, error_msg = self.downloader.start_calibration()
        
        if not success:
            self.status_label.config(text=error_msg)
        
    def start_download(self):
        """Start the download with selected options."""
        try:
            if not self.title_saved:
                self.status_label.config(text="Please save the title first.")
                return
                
            url = self.url_var.get().strip()
            type_choice = self.type_var.get()
            format_str = self.format_combo.get()
            folder = self.folder_entry.get().strip()
            user_title = self.video_title_var.get().strip()
            
            if not all([url, type_choice, format_str, folder]):
                self.status_label.config(text="Please fill all fields")
                return
                
            if user_title == "":
                self.status_label.config(text="Title cannot be empty")
                return
                
            if not os.path.isdir(folder):
                try:
                    os.makedirs(folder, exist_ok=True)
                except Exception:
                    self.status_label.config(text="Cannot create download folder")
                    return
                    
            if not check_network():
                self.status_label.config(text="Network error - check your connection")
                return
                
            # Initialize and start download
            success, error_msg = self.downloader.start_download(url, type_choice, format_str, folder, user_title)
            
            if not success:
                self.status_label.config(text=error_msg)
                return
                
            self.status_label.config(text="Starting download...")
            self.download_button.config(state="disabled")
            self.calibrate_button.config(state="disabled")
            self.progress['value'] = 0
            
        except Exception as e:
            logger.error(f"Error starting download: {str(e)}")
            logger.error(traceback.format_exc())
            self.status_label.config(text="Error starting download")
            self.download_button.config(state="normal")
            self.calibrate_button.config(state="normal")
            
    def open_download_folder(self):
        """Open the folder specified in the download folder entry."""
        try:
            # Get the folder from the entry field
            folder = self.folder_entry.get().strip()
            
            if folder and os.path.exists(folder):
                if os.name == 'nt':  # Windows
                    # Using subprocess instead of os.system for better handling of paths
                    subprocess.Popen(f'explorer "{os.path.normpath(folder)}"', shell=True)
                elif os.name == 'posix':  # macOS or Linux
                    if sys.platform == 'darwin':  # macOS
                        os.system(f'open "{folder}"')
                    else:  # Linux
                        os.system(f'xdg-open "{folder}"')
                self.status_label.config(text=f"Opened folder: {folder}")
            else:
                # If folder doesn't exist, prompt the user to select one
                self.status_label.config(text="Please select a valid download folder")
                self.browse_folder()
                
        except Exception as e:
            logger.error(f"Error opening folder: {str(e)}")
            self.status_label.config(text="Could not open folder")
            
    def on_closing(self):
        """Save folder path on exit and clean up threads."""
        try:
            current_folder = self.folder_entry.get().strip()
            if current_folder:
                save_config(current_folder)
            
            # Clean up any temporary files
            self.downloader.cleanup()
                
            # Clean up log handlers
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
                
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")
        finally:
            self.root.destroy() 