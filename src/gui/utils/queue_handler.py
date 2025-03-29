"""
Queue handler for the Video Downloader application.
Processes messages from the download queue and dispatches them to appropriate components.
"""

import queue

class QueueHandler:
    """
    Handles processing messages from the downloader queue.
    Dispatches messages to appropriate handlers in the UI.
    """
    
    def __init__(self, download_queue):
        """
        Initialize the queue handler.
        
        Args:
            download_queue: Queue for receiving messages from the downloader
        """
        self.queue = download_queue
        self.handlers = {}
        self.current_download_phase = None
        
    def register_handler(self, message_type, handler_function):
        """
        Register a handler function for a specific message type.
        
        Args:
            message_type: Type of message to handle (e.g., 'formats', 'progress')
            handler_function: Function to call when this message type is received
        """
        self.handlers[message_type] = handler_function
        
    def process_queue(self):
        """Process all pending messages in the queue."""
        try:
            while not self.queue.empty():
                message = self.queue.get_nowait()
                
                message_type = message[0]
                
                # Special case for the download phase
                if message_type == "set_phase":
                    self.current_download_phase = message[1]
                
                # Handle messages based on their type
                if message_type in self.handlers:
                    if message_type == "progress":
                        # For progress updates, also pass the current phase
                        self.handlers[message_type](message[1:], self.current_download_phase)
                    else:
                        # For other message types, just pass the payload
                        self.handlers[message_type](message[1:])
                
        except queue.Empty:
            pass
        except Exception as e:
            print(f"Error in queue handler: {str(e)}")
            
    def reset(self):
        """Reset the download phase."""
        self.current_download_phase = None 