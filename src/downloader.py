import yt_dlp
import os
import time
import threading
import logging
import random
import tempfile
import sys
from collections import defaultdict

# Adjust import paths dynamically
if getattr(sys, 'frozen', False):
    # Running as compiled .exe
    from utils import format_size, format_time, ffmpeg_executable, sanitize_filename, logger
    from config import load_fragments_config, save_fragments_config
else:
    # Running directly as .py
    from utils import format_size, format_time, ffmpeg_executable, sanitize_filename, logger
    from config import load_fragments_config, save_fragments_config

class Downloader:
    def __init__(self, queue):
        self.queue = queue
        self.format_map = {}
        self.title_saved = False
        self.current_download_phase = None
        self.progress_state = [0, None]  # [current phase index, current filename]
        self.download_sequence = []
        self.active_threads = []
        self.calibration_lock = threading.Lock()
        self.is_calibrating = False
        
        # Load saved optimal fragments from config, or use default if not found
        saved_fragments = load_fragments_config()
        self.optimal_fragments = saved_fragments if saved_fragments is not None else 3
        logger.info(f"Loaded optimal fragments setting: {self.optimal_fragments}")
        
        self.temp_files = []  # Track temporary files for cleanup

    def fetch_formats(self, url, type_choice):
        """Initiate fetching of video formats."""
        # Create and start the thread
        fetch_thread = threading.Thread(target=self._fetch_formats_thread, args=(url, type_choice), daemon=True)
        fetch_thread.do_run = True  # Flag for cancellation
        self.active_threads.append(fetch_thread)
        fetch_thread.start()

    def _fetch_formats_thread(self, url, type_choice):
        """Fetch video formats in a separate thread."""
        try:
            opts = {
                'quiet': True,
                'socket_timeout': 30,
                'retries': 3
            }
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
            if not info:
                self.queue.put(("error", "Could not retrieve video information"))
                return
                
            self.queue.put(("video_title", info.get('title', '')))
            
            if 'formats' not in info or not info['formats']:
                self.queue.put(("error", "No formats available for this URL"))
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
                self.queue.put(("error", f"No compatible {'audio' if type_choice == '3' else 'video'} formats found"))
                return
                
            format_list = []
            self.format_map = {}
            
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
                    self.format_map[format_str] = (best['format_id'], best.get('ext', 'mp4'))
                except (KeyError, ValueError) as e:
                    logger.warning(f"Error processing format: {str(e)}")
                    continue
                    
            self.queue.put(("formats", format_list))
            
        except yt_dlp.utils.DownloadError as e:
            logger.error(f"Download error: {str(e)}")
            self.queue.put(("error", f"Error: {str(e)}"))
        except yt_dlp.utils.ExtractorError as e:
            logger.error(f"Extractor error: {str(e)}")
            self.queue.put(("error", f"This URL is not supported"))
        except Exception as e:
            logger.error(f"Unexpected error in fetch_formats_thread: {str(e)}")
            self.queue.put(("error", "Error processing URL"))
        finally:
            # Re-enable the fetch button after completion (success or error)
            self.queue.put(("enable_fetch", None))
            
    def start_download(self, url, type_choice, format_str, folder, user_title):
        """Start the download with selected options."""
        # Check if calibration is running
        if self.is_calibrating:
            return False, "Please wait for calibration to complete"
            
        # Create and start the thread
        if format_str not in self.format_map:
            return False, "Invalid format selected"
            
        format_id, format_ext = self.format_map.get(format_str)
        if not format_id:
            return False, "Invalid format selected"
            
        user_title = sanitize_filename(user_title)
        format_part = format_str.split(" - ")[0]
        
        if type_choice == '1':
            self.download_sequence = ["video", "audio"]
            expected_ext = 'mp4'
            ydl_opts = {
                'format': f"{format_id}+bestaudio",
                'merge_output_format': 'mp4',
                'progress_hooks': [self.progress_hook],
                'no_mtime': True,
                'socket_timeout': 30,
                'retries': 5,
                'ffmpeg_location': ffmpeg_executable,
                'concurrent_fragment_downloads': self.optimal_fragments,
            }
        elif type_choice == '2':
            self.download_sequence = ["video"]
            expected_ext = format_ext
            ydl_opts = {
                'format': format_id,
                'progress_hooks': [self.progress_hook],
                'no_mtime': True,
                'socket_timeout': 30,
                'retries': 5,
                'ffmpeg_location': ffmpeg_executable,
                'concurrent_fragment_downloads': self.optimal_fragments,
            }
        elif type_choice == '3':
            self.download_sequence = ["audio"]
            expected_ext = 'mp3'
            ydl_opts = {
                'format': format_id,
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
                'progress_hooks': [self.progress_hook],
                'no_mtime': True,
                'socket_timeout': 30,
                'retries': 5,
                'ffmpeg_location': ffmpeg_executable,
                'concurrent_fragment_downloads': self.optimal_fragments,
            }
            
        base_filename = sanitize_filename(f"{user_title} - {format_part}")
        full_filename = os.path.join(folder, f"{base_filename}.{expected_ext}")
        
        # Validate the download path
        valid, error_msg = self.validate_download_path(folder, full_filename)
        if not valid:
            return False, error_msg
            
        ydl_opts['outtmpl'] = os.path.join(folder, f"{base_filename}.%(ext)s")
        
        self.progress_state = [0, None]
        self.current_download_phase = None
        
        # Set the initial phase immediately
        self.current_download_phase = self.download_sequence[0]
        self.queue.put(("start_phase", self.current_download_phase))
        
        # Create and start the thread
        download_thread_obj = threading.Thread(
            target=self._download_thread, 
            args=(url, ydl_opts, type_choice, folder, base_filename, expected_ext), 
            daemon=True
        )
        download_thread_obj.do_run = True  # Flag for cancellation
        self.active_threads.append(download_thread_obj)
        download_thread_obj.start()
        
        return True, None
        
    def validate_download_path(self, folder, filename):
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
            
    def _download_thread(self, url, ydl_opts, type_choice, folder, base_filename, expected_ext):
        """Perform the download in a separate thread and set modification time after download."""
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                    
                if not info:
                    self.queue.put(("download_error", "Download failed: No video information"))
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
                            self.queue.put(("download_error", "Download failed: File not found after download"))
                            return
                            
                # Set file modification time to current time
                current_time = time.time()
                os.utime(filename, (current_time, current_time))
                
                self.queue.put(("download_complete", filename))
                
        except yt_dlp.utils.DownloadError as e:
            logger.error(f"Download error: {str(e)}")
            self.queue.put(("download_error", f"Download failed: {str(e)}"))
        except Exception as e:
            logger.error(f"Unexpected error in download_thread: {str(e)}")
            self.queue.put(("download_error", f"Download failed: {str(e)}"))

    def progress_hook(self, d):
        """Update download progress with phase-specific messages."""
        try:
            if d['status'] == 'downloading':
                # If not already set, set the current phase on first downloading event
                if self.current_download_phase is None and self.progress_state[0] < len(self.download_sequence):
                    self.current_download_phase = self.download_sequence[self.progress_state[0]]
                    self.queue.put(("start_phase", self.current_download_phase))
                    
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate')
                
                if total:
                    percent = min((downloaded / total) * 100, 100)  # Cap at 100%
                    speed = d.get('speed')
                    speed_mbps = round(speed / 1048576, 1) if speed else None
                    eta = d.get('eta')
                    eta_str = f" - ETA: {format_time(eta)}" if eta else ""
                    
                    self.queue.put(("progress", percent, speed_mbps, eta_str))
                else:
                    downloaded_mb = round(downloaded / 1048576, 1)
                    self.queue.put(("progress_unknown", downloaded_mb))
                    
            elif d['status'] == 'finished':
                # Advance to the next phase if available; otherwise, switch to merging.
                if self.progress_state[0] < len(self.download_sequence) - 1:
                    self.progress_state[0] += 1
                    self.current_download_phase = self.download_sequence[self.progress_state[0]]
                    self.queue.put(("start_phase", self.current_download_phase))
                else:
                    self.queue.put(("start_phase", "merging"))
                    
            elif d['status'] == 'processing':
                self.queue.put(("start_phase", "merging"))
                
        except Exception as e:
            logger.error(f"Error in progress_hook: {str(e)}")
            
    def start_calibration(self):
        """Start the Internet speed calibration process."""
        if self.is_calibrating:
            return False, "Calibration already in progress"
            
        self.queue.put(("calibrate_start", None))
        
        # Create and start the calibration thread
        calibrate_thread = threading.Thread(target=self._calibration_thread, daemon=True)
        calibrate_thread.do_run = True  # Flag for cancellation
        self.active_threads.append(calibrate_thread)
        calibrate_thread.start()
        
        return True, None
        
    def _calibration_thread(self):
        """Perform internet speed calibration in a separate thread."""
        # Store the current value in case calibration fails
        previous_fragments = self.optimal_fragments
        
        try:
            with self.calibration_lock:
                self.is_calibrating = True
                
                # We'll use a set of sample videos to test download speed
                # These are very short videos that are commonly used for testing
                test_videos = [
                    'https://www.youtube.com/watch?v=jNQXAC9IVRw',  # First YouTube video
                    'https://www.youtube.com/watch?v=2lAe1cqCOXo',  # Short YouTube video
                    'https://www.youtube.com/watch?v=dQw4w9WgXcQ',  # Another common test video
                ]
                
                # Use only one random video for speed test
                test_video = random.choice(test_videos)
                
                # Create temp directory for calibration downloads
                temp_dir = tempfile.mkdtemp(prefix="yt_calibration_")
                self.temp_files.append(temp_dir)  # Track for cleanup
                
                # Test with different concurrent fragment counts
                fragments_to_test = [1, 3, 5, 8, 10]
                speeds = {}
                
                # First get video info
                info_opts = {
                    'quiet': True,
                    'format': 'best[height<=480]',  # Use a small format for testing
                    'socket_timeout': 15,
                    'retries': 2,
                    'skip_download': True,
                }
                
                with yt_dlp.YoutubeDL(info_opts) as ydl:
                    self.queue.put(("calibration_progress", 5, "Preparing calibration..."))
                    info = ydl.extract_info(test_video, download=False)
                    
                if not info:
                    self.queue.put(("calibration_error", "Could not retrieve test video information"))
                    self.optimal_fragments = previous_fragments  # Restore previous value
                    return
                
                # Perform tests with different fragment counts
                total_tests = len(fragments_to_test)
                for i, fragments in enumerate(fragments_to_test):
                    # Update progress based on which test we're running
                    progress_percent = 5 + (i / total_tests) * 90  # 5-95% progress
                    self.queue.put(("calibration_progress", progress_percent, 
                                   f"Calibrating internet... ({fragments} fragments)"))
                    
                    # Configure download options
                    test_opts = {
                        'quiet': True,
                        'format': 'best[height<=480]',  # Use a small format for testing
                        'progress_hooks': [self._calibration_hook],
                        'socket_timeout': 15,
                        'retries': 2,
                        'max_downloads': 1,
                        'concurrent_fragment_downloads': fragments,
                        'outtmpl': os.path.join(temp_dir, f'test_{fragments}_%(id)s.%(ext)s'),
                    }
                    
                    self.test_speed = 0
                    start_time = time.time()
                    
                    # Download first 10 seconds only
                    try:
                        with yt_dlp.YoutubeDL(test_opts) as ydl:
                            ydl.download([f"{test_video}"])
                    except Exception as e:
                        logger.error(f"Error during calibration with {fragments} fragments: {str(e)}")
                        # Continue with other tests
                        
                    # Record the maximum speed achieved
                    speeds[fragments] = self.test_speed
                
                # Determine optimal fragment count based on speed tests
                if speeds:
                    # Choose the fragment count that gave the highest speed
                    optimal_fragments = max(speeds.items(), key=lambda x: x[1])[0]
                    self.optimal_fragments = optimal_fragments
                    
                    # Save the optimal fragments to config file
                    save_fragments_config(optimal_fragments)
                    
                    # Log the results
                    logger.info(f"Calibration results: {speeds}")
                    logger.info(f"Optimal fragments: {optimal_fragments} (saved to config)")
                    
                    self.queue.put(("calibration_progress", 100, f"Calibration complete!"))
                    self.queue.put(("calibration_result", optimal_fragments, max(speeds.values())))
                else:
                    # If all tests failed, use the previous value or default
                    self.optimal_fragments = previous_fragments
                    self.queue.put(("calibration_error", "Calibration failed, using previous settings"))
                
                # Clean up temp directory
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                    self.temp_files.remove(temp_dir)
                except Exception as e:
                    logger.error(f"Error cleaning up temp directory: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error during calibration: {str(e)}")
            self.queue.put(("calibration_error", f"Calibration failed: {str(e)}"))
            # Restore previous value if calibration fails
            self.optimal_fragments = previous_fragments
        finally:
            self.is_calibrating = False
            self.queue.put(("calibrate_end", None))
            
    def _calibration_hook(self, d):
        """Hook to capture speed during calibration."""
        if d['status'] == 'downloading':
            speed = d.get('speed', 0)
            if speed:
                # Convert to MB/s and update max speed
                speed_mbps = speed / 1048576
                self.test_speed = max(self.test_speed, speed_mbps)
                
    def cleanup(self):
        """Clean up temporary files and resources."""
        try:
            # Clean up any temp files
            for temp_path in self.temp_files:
                if os.path.exists(temp_path):
                    if os.path.isdir(temp_path):
                        import shutil
                        try:
                            shutil.rmtree(temp_path)
                        except Exception as e:
                            logger.error(f"Error removing temp directory {temp_path}: {str(e)}")
                    else:
                        try:
                            os.remove(temp_path)
                        except Exception as e:
                            logger.error(f"Error removing temp file {temp_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}") 