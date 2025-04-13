import subprocess
import os
import threading

def run_yt_dlp_updater():
    """Run the yt-dlp_updater.exe binary in a separate thread."""
    def updater_thread():
        try:
            updater_path = os.path.join(os.path.dirname(__file__), 'assets', 'yt-dlp_updater.exe')
            subprocess.run([updater_path], check=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
        except subprocess.CalledProcessError as e:
            print(f"Error running yt-dlp updater: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    thread = threading.Thread(target=updater_thread)
    thread.start()
