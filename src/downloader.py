import os
import time
import threading
import logging
import re
import tempfile
import sys
import subprocess
import json
from collections import defaultdict

# Adjust import paths dynamically
if getattr(sys, 'frozen', False):
    # Running as compiled .exe
    from utils import format_size, format_time, ffmpeg_executable, sanitize_filename, logger, get_ytdlp_executable
    from config import load_fragments_config, save_fragments_config
    from phantom import PhantomJSHandler
else:
    # Running directly as .py
    from utils import format_size, format_time, ffmpeg_executable, sanitize_filename, logger, get_ytdlp_executable
    from config import load_fragments_config, save_fragments_config
    from phantom import PhantomJSHandler

class Downloader:
    def __init__(self, queue):
        self.queue = queue
        self.format_map = {}
        self.title_saved = False
        self.active_threads = []
        self.ytdlp_process = None
        self.temp_files = []  # Track temporary files for cleanup
        
        # Get yt-dlp executable path
        self.ytdlp_exe = get_ytdlp_executable()
        if not self.ytdlp_exe:
            logger.error("yt-dlp executable not found!")
            self.queue.put(("error", "yt-dlp executable not found!"))
        
        # Initialize PhantomJS handler
        self.phantom_handler = PhantomJSHandler()

    def execute_ytdlp(self, args, capture_output=True, text=True, timeout=None):
        """Execute yt-dlp binary with given arguments and return the result.
        
        Args:
            args: List of command-line arguments
            capture_output: Whether to capture stdout/stderr
            text: Whether to return output as text (vs bytes)
            timeout: Timeout in seconds
            
        Returns:
            CompletedProcess object with stdout/stderr
        """
        if not self.ytdlp_exe:
            raise FileNotFoundError("yt-dlp executable not found")
            
        command = [self.ytdlp_exe] + args
        logger.info(f"Executing: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                capture_output=capture_output,
                text=text,
                timeout=timeout
            )
            return result
        except subprocess.TimeoutExpired as e:
            logger.error(f"yt-dlp command timed out: {e}")
            raise
        except Exception as e:
            logger.error(f"Error executing yt-dlp: {e}")
            raise

    def start_ytdlp_process(self, args, on_output=None):
        """Start yt-dlp as a background process and process output in real-time.
        
        Args:
            args: List of command-line arguments
            on_output: Callback function to process each line of output
            
        Returns:
            The subprocess.Popen object
        """
        if not self.ytdlp_exe:
            raise FileNotFoundError("yt-dlp executable not found")
            
        command = [self.ytdlp_exe] + args
        logger.info(f"Starting yt-dlp process: {' '.join(command)}")
        
        # Create process with pipes for stdout and stderr
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True,
            encoding='utf-8', # Specify encoding explicitly
            errors='replace'  # Handle potential encoding errors
        )
        
        self.ytdlp_process = process
        
        # Start threads to read output
        if on_output:
            def read_output(stream, stream_name, callback):
                try:
                    for line in iter(stream.readline, ''):
                        if not line:
                            break
                        line = line.strip()
                        # Log the raw line before processing
                        logger.debug(f"yt-dlp {stream_name}: {line}") 
                        if line: # Ensure non-empty line before calling callback
                            callback(line)
                except Exception as e:
                    logger.error(f"Error reading {stream_name} stream: {e}")
                finally:
                    stream.close()
                    
            # Start stdout reader thread
            stdout_thread = threading.Thread(
                target=read_output,
                args=(process.stdout, "stdout", on_output),
                daemon=True
            )
            stdout_thread.start()
            
            # Start stderr reader thread
            stderr_thread = threading.Thread(
                target=read_output,
                args=(process.stderr, "stderr", on_output),
                daemon=True
            )
            stderr_thread.start()
        
        return process

    def parse_progress_output(self, line):
        """Parse a line of yt-dlp output to extract progress information.
        
        Args:
            line: A line of output from yt-dlp
            
        Returns:
            Dict with progress info or None if no progress info found
        """
        # Improved regex to handle spacing and capture units
        progress_pattern = re.compile(
            r"\s*\[download\]\s+"
            r"(?P<percent>\d+\.\d+)%\s+of\s+"
            r"(?P<size>[\d\.]+)\s*(?P<size_unit>KiB|MiB|GiB)\s+at\s+"
            r"(?P<speed>[\d\.]+)\s*(?P<speed_unit>KiB|MiB|GiB)/s\s+"
            r"ETA\s+(?P<eta>\d{1,2}:\d{2}(?::\d{2})?)"
        )
        
        match = progress_pattern.search(line)
        if match:
            data = match.groupdict()
            percent = float(data['percent'])
            speed_val = float(data['speed'])
            speed_unit = data['speed_unit']
            eta_str = data['eta']
            
            # Convert speed to MB/s based on captured unit
            if speed_unit == 'KiB':
                speed_mbps = speed_val / 1024
            elif speed_unit == 'GiB':
                speed_mbps = speed_val * 1024
            else: # MiB
                speed_mbps = speed_val
                
            return {
                'status': 'downloading',
                'percent': percent,
                'speed': round(speed_mbps, 1), # Round for display
                'eta': eta_str
            }
            
        # Check for merging/processing indication
        if '[Merger]' in line or 'Merging formats' in line or 'Merger' in line:
            return {
                'status': 'processing',
                'percent': 100,
                'phase': 'merging'
            }
            
        # Check for download complete indication
        # Example: [download] Destination: video_title.mp4
        # Example: [download] video_title.mp4 has already been downloaded
        if '[download] Destination:' in line or 'has already been downloaded' in line:
            return {
                'status': 'finished',
                'percent': 100
            }
            
        # Check for post-processing (e.g., audio extraction)
        if '[ExtractAudio]' in line or 'Extracting audio' in line or 'Postprocessing' in line or '[FixupM3u8]' in line:
            return {
                'status': 'processing',
                'phase': 'audio' # Treat audio extraction/fixup as part of audio phase
            }
            
        return None

    def fetch_formats(self, url, type_choice):
        """Initiate fetching of video formats."""
        # Create and start the thread
        fetch_thread = threading.Thread(target=self._fetch_formats_thread, args=(url, type_choice), daemon=True)
        fetch_thread.do_run = True  # Flag for cancellation
        self.active_threads.append(fetch_thread)
        fetch_thread.start()

    def _fetch_formats_thread(self, url, type_choice):
        """Fetch video formats in a separate thread using --dump-json."""
        try:
            # Check if PhantomJS is required for this URL
            use_phantom = self.phantom_handler.is_phantom_required(url)
            
            if use_phantom:
                logger.info(f"Using PhantomJS for URL: {url}")
                self.queue.put(("status", "Using PhantomJS to process this URL..."))
                
                # Extract media URLs using PhantomJS
                phantom_result = self.phantom_handler.extract_media_urls(url)
                
                if "error" in phantom_result:
                    self.queue.put(("error", f"PhantomJS error: {phantom_result['error']}"))
                    return
                    
                # Get compatible URLs for yt-dlp
                phantom_urls = self.phantom_handler.get_ytdlp_compatible_urls(phantom_result)
                
                if not phantom_urls:
                    logger.warning("PhantomJS couldn't find any media URLs, falling back to yt-dlp")
                    self.queue.put(("status", "PhantomJS couldn't find content, trying standard method..."))
                    # Fall through to standard method if PhantomJS fails to find URLs
                else:
                    # Use the title from PhantomJS if available
                    if "title" in phantom_result and phantom_result["title"]:
                        self.queue.put(("video_title", phantom_result["title"]))
                    
                    # Process each URL found by PhantomJS
                    self._process_phantom_results(phantom_urls, type_choice)
                    return
            
            # Standard yt-dlp extraction using --dump-json
            try:
                info_args = [
                    '--dump-json',
                    '--no-playlist',
                    '--no-warnings',
                    '--socket-timeout', '30',
                    url
                ]
                
                result = self.execute_ytdlp(info_args, timeout=60)
                
                if result.returncode != 0:
                    logger.error(f"yt-dlp info extraction failed: {result.stderr}")
                    self.queue.put(("error", f"Error: Could not retrieve video information: {result.stderr}"))
                    return
                    
                # Parse the JSON output to get video info and formats
                try:
                    info = json.loads(result.stdout)
                except json.JSONDecodeError:
                    logger.error("Failed to parse yt-dlp JSON output")
                    self.queue.put(("error", "Error: Could not parse video information"))
                    return
                    
                # Get and set the video title
                title = info.get('title', 'Untitled Video')
                self.queue.put(("video_title", title))
                
                # Process formats from the JSON info
                formats_data = info.get('formats', [])
                if not formats_data:
                    self.queue.put(("error", "No formats available for this URL"))
                    return
                    
                # Filter and format based on type_choice
                format_list = []
                self.format_map = {}
                format_groups = defaultdict(list)
                
                if type_choice == '3':  # Audio Only
                    for f in formats_data:
                        if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                            key = f.get('abr')
                            if key:
                                format_groups[key].append(f)
                                
                    # Sort groups by bitrate (abr) descending
                    for key in sorted(format_groups.keys(), reverse=True):
                        group = format_groups[key]
                        best = max(group, key=lambda x: x.get('filesize_approx') or x.get('filesize') or 0)
                        size = best.get('filesize_approx') or best.get('filesize')
                        size_str = format_size(size) if size else "Unknown"
                        abr = best.get('abr', 'Unknown')
                        format_str = f"{abr} kbps - {size_str}"
                        
                        format_list.append(format_str)
                        self.format_map[format_str] = (best['format_id'], best.get('ext', 'm4a'))
                        
                else:  # Video + Audio or Video Only
                    for f in formats_data:
                        # Consider only video formats (may or may not have audio initially)
                        if f.get('vcodec') != 'none' and f.get('height') is not None:
                            key = (f.get('height'), f.get('fps')) # Group by height and fps
                            format_groups[key].append(f)
                            
                    # Sort groups by height descending, then fps descending
                    for key in sorted(format_groups.keys(), key=lambda x: (x[0] or 0, x[1] or 0), reverse=True):
                        group = format_groups[key]
                        # Find best format (e.g., largest filesize_approx)
                        best = max(group, key=lambda x: x.get('filesize_approx') or x.get('filesize') or 0)
                        size = best.get('filesize_approx') or best.get('filesize')
                        size_str = format_size(size) if size else "Unknown"
                        height = best.get('height', '?')
                        fps = best.get('fps', '')
                        fps_str = f" ({fps}fps)" if fps else ""
                        format_str = f"{height}p{fps_str} - {size_str}"
                        
                        format_list.append(format_str)
                        # Store format_id and original extension
                        self.format_map[format_str] = (best['format_id'], best.get('ext', 'mp4')) 

                if not format_list:
                    self.queue.put(("error", f"No compatible {'audio' if type_choice == '3' else 'video'} formats found"))
                    return
                    
                self.queue.put(("formats", format_list))

            except FileNotFoundError:
                logger.error("yt-dlp executable not found")
                self.queue.put(("error", "Error: yt-dlp executable not found"))
            except subprocess.TimeoutExpired:
                logger.error("yt-dlp command timed out")
                self.queue.put(("error", "Error: Command timed out retrieving video info"))
            except Exception as e:
                logger.error(f"Unexpected error in fetch_formats_thread: {str(e)}", exc_info=True)
                self.queue.put(("error", f"Error processing URL: {str(e)}"))
            
        except Exception as e:
            logger.error(f"General error in fetch_formats_thread: {str(e)}", exc_info=True)
            self.queue.put(("error", "Error processing URL"))
        finally:
            # Re-enable the fetch button after completion (success or error)
            self.queue.put(("enable_fetch", None))

    def _process_phantom_results(self, phantom_urls, type_choice):
        """Process the URLs extracted by PhantomJS."""
        try:
            formats = []
            self.format_map = {}
            
            # For each URL, try to extract format information
            for url in phantom_urls:
                try:
                    if "video" in url.lower():
                        format_id = f"phantom:{url}"
                        format_list = [f"Video (Direct) - {url[:30]}..."]
                        self.format_map[format_list[0]] = (format_id, "mp4")
                        formats.extend(format_list)
                    elif "audio" in url.lower():
                        format_id = f"phantom:{url}"
                        format_list = [f"Audio (Direct) - {url[:30]}..."]
                        self.format_map[format_list[0]] = (format_id, "mp3")
                        formats.extend(format_list)
                except Exception as e:
                    logger.warning(f"Error processing phantom URL: {url}, error: {str(e)}")
            
            if formats:
                self.queue.put(("formats", formats))
            else:
                self.queue.put(("error", "No usable formats found in PhantomJS results"))
        except Exception as e:
            logger.error(f"Error in _process_phantom_results: {str(e)}")
            self.queue.put(("error", f"Failed to process extracted content: {str(e)}"))

    def start_download(self, url, type_choice, format_str, folder, user_title):
        try:
            # Extract format information from the selected format string
            if format_str not in self.format_map:
                return False, "Selected format is not available"
            
            format_id, format_ext = self.format_map[format_str]
            
            logger.info(f"Starting download: {url}, type: {type_choice}, format: {format_id}")
            
            # Process the format part (for filename)
            if type_choice == '3':  # Audio
                format_part = format_str.split(' - ')[0].strip() + " kbps"
            else:  # Video
                format_part = format_str.split(' - ')[0].strip()
            
            # Check if it's a PhantomJS URL
            is_phantom_url = format_id.startswith("phantom:")
            
            # Common flags for all downloads
            common_flags = [
                '--progress',       # Force progress updates
                '--newline',        # Ensure progress is on new lines
                '--no-warnings',
                '--no-playlist',
                '--socket-timeout', '30',
                '--retries', '5',
                '--ffmpeg-location', ffmpeg_executable,
            ]
            
            if is_phantom_url:
                # Direct download using the PhantomJS extracted URL
                if "Video" in format_str:
                    # No specific action needed for sequence here anymore
                    pass
                else:
                    # No specific action needed for sequence here anymore
                    pass
                
                direct_url = format_id.replace("phantom:", "")
                expected_ext = format_ext
                
                if type_choice == '3' and "Audio" in format_str:
                    # Audio download
                    command_args = [
                        *common_flags,
                        '--extract-audio',
                        '--audio-format', 'mp3',
                        '--audio-quality', '0', 
                    ]
                    expected_ext = 'mp3'
                    is_video_only = False # Phantom URLs are treated as single stream
                else:
                    # Video download
                    command_args = [
                        *common_flags,
                        '--format', 'best', # Let yt-dlp choose best for direct URL
                    ]
                    is_video_only = True # Phantom URLs are treated as single stream
                    
                # Override the URL with the direct URL from PhantomJS
                direct_download_url = direct_url
            else:
                # Standard yt-dlp download
                direct_download_url = url
                is_video_only = False
                
                if type_choice == '1':
                    # No specific action needed for sequence here anymore
                    expected_ext = 'mp4'
                    command_args = [
                        *common_flags,
                        '--format', f"{format_id}+bestaudio",
                        '--merge-output-format', 'mp4',
                    ]
                elif type_choice == '2':
                    # No specific action needed for sequence here anymore
                    expected_ext = format_ext
                    command_args = [
                        *common_flags,
                        '--format', format_id,
                    ]
                    is_video_only = True
                elif type_choice == '3':
                    # No specific action needed for sequence here anymore
                    expected_ext = 'mp3'
                    command_args = [
                        *common_flags,
                        '--format', format_id,
                        '--extract-audio',
                        '--audio-format', 'mp3',
                        '--audio-quality', '0',
                    ]
            
            # Create base filename with appropriate suffix
            # Use is_video_only flag which is now correctly set for Phantom/Standard
            if is_video_only:
                base_filename = sanitize_filename(f"{user_title} - {format_part} [Video only]")
            else:  # Audio only or Video+Audio
                base_filename = sanitize_filename(f"{user_title} - {format_part}")
            
            # Use expected_ext which is now correctly set for all modes
            full_filename = os.path.join(folder, f"{base_filename}.{expected_ext}")
            
            # Validate the download path
            valid, error_msg = self.validate_download_path(folder, full_filename)
            if not valid:
                return False, error_msg
            
            command_args.extend(['--output', os.path.join(folder, f"{base_filename}.%(ext)s")])
            self.ytdlp_process = None
            self.queue.put(("status", "Starting download..."))
            
            download_thread_obj = threading.Thread(
                target=self._download_thread, 
                args=(direct_download_url, command_args, folder, base_filename, expected_ext, is_phantom_url), 
                daemon=True
            )
            download_thread_obj.do_run = True
            self.active_threads.append(download_thread_obj)
            download_thread_obj.start()
            
            return True, None
        except Exception as e:
            logger.error(f"Error starting download: {str(e)}")
            return False, f"Error starting download: {str(e)}"

    def _download_thread(self, url, command_args, folder, base_filename, expected_ext, is_phantom_url=False):
        # Note: Removed type_choice from args as it's not needed here anymore
        try:
            # Log whether we're using PhantomJS URL
            if is_phantom_url:
                logger.info(f"Downloading using PhantomJS extracted URL: {url}")
            
            full_command_args = command_args + [url]
            
            # Define a callback to handle output lines (simplified)
            def process_output(line):
                progress_info = self.parse_progress_output(line)
                if progress_info:
                    self._handle_progress_info(progress_info)
                elif "Merging formats" in line:
                    # Send a status update for merging
                    self.queue.put(("status", "Merging formats..."))
                
            # Start the yt-dlp process
            process = self.start_ytdlp_process(full_command_args, on_output=process_output)
            self.ytdlp_process = process
            
            # Wait for the process to complete
            return_code = process.wait()
            
            # Check if download succeeded
            if return_code != 0:
                error = process.stderr.read() if process.stderr else "Unknown error"
                logger.error(f"yt-dlp process failed with code {return_code}: {error}")
                self.queue.put(("download_error", f"Download failed with error code {return_code}"))
                return
            
            # Simplified filename finding for Video+Audio (just look for mp4)
            if "+bestaudio" in str(command_args): # Crude check if it was video+audio mode
                filename = os.path.join(folder, f"{base_filename}.mp4")
            elif ".mp3" in str(command_args): # Check if audio only mode
                 filename = os.path.join(folder, f"{base_filename}.mp3")
            else: # Video only mode
                filename = os.path.join(folder, f"{base_filename}.{expected_ext}")
                
            # Fallback if expected file not found
            if not os.path.exists(filename):
                 for file in os.listdir(folder):
                    if file.startswith(base_filename) and os.path.isfile(os.path.join(folder, file)):
                        filename = os.path.join(folder, file)
                        logger.info(f"Found output file via fallback search: {filename}")
                        break
                        
            # Verify file exists after download
            if not os.path.exists(filename):
                self.queue.put(("download_error", "Download failed: File not found after download"))
                return
            
            # Set file modification time to current time
            current_time = time.time()
            os.utime(filename, (current_time, current_time))
            
            self.queue.put(("download_complete", filename))
            
        except Exception as e:
            logger.error(f"Error in download thread: {str(e)}")
            self.queue.put(("download_error", f"Download failed: {str(e)}"))

    def _handle_progress_info(self, progress_info):
        """Handle progress information from yt-dlp output (simplified)."""
        status = progress_info.get('status')
        logger.debug(f"Handling progress info: {progress_info}")
        
        if status == 'downloading':
            percent = progress_info.get('percent', 0)
            speed = progress_info.get('speed')
            eta = progress_info.get('eta', '')
            logger.debug(f"Sending progress update: {percent}%" )
            # Send simplified progress tuple: (percent, speed, eta)
            self.queue.put(("progress", percent, speed, eta))
            
        elif status == 'finished':
            # Could potentially send 100% update here if needed
            # self.queue.put(("progress", 100, None, None))
            logger.info("Detected 'finished' status.")
            
        elif status == 'processing':
            # Merging is now handled by checking the raw line in process_output
            # We might still get audio extraction messages here
            logger.info(f"Detected 'processing' status: {progress_info.get('phase')}")
            # Optionally send a status update if needed for other processing types
            # self.queue.put(("status", "Processing...")) 

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
            
    def cancel_active_process(self):
        """Cancel any active yt-dlp processes."""
        try:
            if self.ytdlp_process and self.ytdlp_process.poll() is None:
                # Process is still running, terminate it
                logger.info("Terminating active yt-dlp process")
                self.ytdlp_process.terminate()
                # Give it a moment to terminate
                time.sleep(0.5)
                # If it's still running, kill it forcefully
                if self.ytdlp_process.poll() is None:
                    self.ytdlp_process.kill()
                return True
            return False
        except Exception as e:
            logger.error(f"Error cancelling yt-dlp process: {str(e)}")
            return False

    def cleanup(self):
        """Clean up temporary files."""
        try:
            # Clean up temp files
            for temp_file in self.temp_files:
                if os.path.exists(temp_file):
                    if os.path.isdir(temp_file):
                        import shutil
                        shutil.rmtree(temp_file, ignore_errors=True)
                    else:
                        os.remove(temp_file)
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()
        self.cancel_active_process() 