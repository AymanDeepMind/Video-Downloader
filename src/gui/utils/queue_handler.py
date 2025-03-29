"""
Queue handler for the Video Downloader application.
Processes messages from the download queue and dispatches them to appropriate components.
"""

import queue
from PyQt5.QtCore import QObject, pyqtSignal

class QueueHandler(QObject):
    """
    Handles processing messages from the downloader queue.
    Uses Qt signals to notify GUI components of new events.
    """
    
    # Define signals for different message types
    formats_signal = pyqtSignal(object)
    video_title_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    enable_fetch_signal = pyqtSignal(object)
    start_phase_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(object, str)
    phase_complete_signal = pyqtSignal(object)
    download_complete_signal = pyqtSignal(object)
    merge_failed_signal = pyqtSignal(str)
    download_error_signal = pyqtSignal(str)
    calibration_progress_signal = pyqtSignal(str)
    calibration_complete_signal = pyqtSignal(int)
    # Add signal for PhantomJS status messages
    status_signal = pyqtSignal(str)
    
    def __init__(self, download_queue):
        """
        Initialize the queue handler.
        
        Args:
            download_queue: Queue for receiving messages from the downloader
        """
        super().__init__()
        self.queue = download_queue
        self.current_download_phase = None
    
    def check_queue(self):
        """Process all pending messages in the queue using signals."""
        try:
            while not self.queue.empty():
                message = self.queue.get_nowait()
                
                message_type = message[0]
                
                # Special case for the download phase
                if message_type == "set_phase":
                    self.current_download_phase = message[1]
                
                # Emit signals based on message type
                if message_type == "formats":
                    # Ensure we always emit a list for formats
                    formats_data = message[1]
                    if not isinstance(formats_data, list):
                        formats_data = [formats_data] if formats_data else []
                    self.formats_signal.emit(formats_data)
                elif message_type == "video_title":
                    self.video_title_signal.emit(message[1])
                elif message_type == "error":
                    self.error_signal.emit(message[1])
                elif message_type == "enable_fetch":
                    self.enable_fetch_signal.emit(message[1])
                elif message_type == "start_phase":
                    self.start_phase_signal.emit(message[1])
                elif message_type == "progress":
                    # Progress message has structure ("progress", percent, speed_mbps, eta_str)
                    # Create a list with all the values for consistent handling
                    progress_data = [message[1]]  # First data item is percent
                    if len(message) > 2:
                        progress_data.append(message[2])  # Speed
                    if len(message) > 3:
                        progress_data.append(message[3])  # ETA
                    self.progress_signal.emit(progress_data, self.current_download_phase)
                elif message_type == "phase_complete":
                    self.phase_complete_signal.emit(message[1])
                elif message_type == "download_complete":
                    self.download_complete_signal.emit(message[1])
                elif message_type == "merge_failed":
                    self.merge_failed_signal.emit(message[1])
                elif message_type == "download_error":
                    self.download_error_signal.emit(message[1])
                elif message_type == "calibration_progress":
                    self.calibration_progress_signal.emit(message[1])
                elif message_type == "calibration_complete":
                    self.calibration_complete_signal.emit(message[1])
                # Handle status messages for PhantomJS
                elif message_type == "status":
                    self.status_signal.emit(message[1])
                # Handle progress updates when total size is unknown
                elif message_type == "progress_unknown":
                    downloaded_mb = message[1]
                    progress_data = [0, f"{downloaded_mb}", ""]  # Use indeterminate progress (0%) but show downloaded size
                    self.progress_signal.emit(progress_data, self.current_download_phase)
                
        except queue.Empty:
            pass
        except Exception as e:
            print(f"Error in queue handler: {str(e)}")
            
    def reset(self):
        """Reset the download phase."""
        self.current_download_phase = None 