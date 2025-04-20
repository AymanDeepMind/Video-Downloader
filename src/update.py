import subprocess
import os
import threading
import sys

def run_yt_dlp_updater():
    """Run the yt-dlp_updater.exe binary in a separate thread."""
    def updater_thread():
        try:
            if getattr(sys, 'frozen', False):
                # Running in a PyInstaller bundle
                base_path = sys._MEIPASS
                updater_path = os.path.join(base_path, 'assets', 'yt-dlp_updater.exe')
            else:
                # Running in normal Python environment
                base_path = os.path.join(os.path.dirname(__file__), 'assets')
                updater_path = os.path.join(base_path, 'yt-dlp_updater.exe')

            subprocess.run(
                [updater_path],
                check=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=os.path.dirname(updater_path)
            )
        except subprocess.CalledProcessError as e:
            pass  # Optionally handle error or show GUI message
        except Exception as e:
            pass  # Optionally handle error or show GUI message

    thread = threading.Thread(target=updater_thread)
    thread.start()
