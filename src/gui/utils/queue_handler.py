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
    progress_signal = pyqtSignal(object)
    download_complete_signal = pyqtSignal(object)
    merge_failed_signal = pyqtSignal(str)
    download_error_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    
    def __init__(self, download_queue):
        """
        Initialize the queue handler.
        
        Args:
            download_queue: Queue for receiving messages from the downloader
        """
        super().__init__()
        self.queue = download_queue
    
    def check_queue(self):
        """Process all pending messages in the queue using signals."""
        try:
            while not self.queue.empty():
                message = self.queue.get_nowait()
                
                message_type = message[0]
                message_data = message[1] if len(message) > 1 else None
                
                # Emit signals based on message type
                if message_type == "formats":
                    formats_data = message_data
                    if not isinstance(formats_data, list):
                        formats_data = [formats_data] if formats_data else []
                    self.formats_signal.emit(formats_data)
                elif message_type == "video_title":
                    self.video_title_signal.emit(message_data)
                elif message_type == "error":
                    self.error_signal.emit(message_data)
                elif message_type == "enable_fetch":
                    self.enable_fetch_signal.emit(message_data)
                elif message_type == "progress":
                    # Progress message structure is now: ("progress", percent, speed, eta)
                    progress_data = [message[1]]  # Percent
                    if len(message) > 2: progress_data.append(message[2]) # Speed
                    if len(message) > 3: progress_data.append(message[3]) # ETA
                    self.progress_signal.emit(progress_data) # Emit without phase
                elif message_type == "download_complete":
                    self.download_complete_signal.emit(message_data)
                elif message_type == "merge_failed":
                    self.merge_failed_signal.emit(message_data)
                elif message_type == "download_error":
                    self.download_error_signal.emit(message_data)
                elif message_type == "status":
                    # Handle specific status updates like Merging
                    if isinstance(message_data, str) and "Merging" in message_data:
                         self.status_signal.emit("Merging formats...")
                    else:
                         self.status_signal.emit(message_data)
                elif message_type == "progress_unknown":
                    downloaded_mb = message_data
                    progress_data = [0, f"{downloaded_mb}", ""] 
                    self.progress_signal.emit(progress_data)
                
        except queue.Empty:
            pass
        except Exception as e:
            print(f"Error in queue handler: {str(e)}")
            
    def reset(self):
        """Reset internal state (if any)."""
        pass 