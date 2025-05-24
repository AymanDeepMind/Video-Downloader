import subprocess
import os
import threading
import sys

def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        # Nuitka/pyinstaller: sys.executable is the exe in main.dist
        base_path = os.path.dirname(sys.executable)
        return os.path.join(base_path, relative_path)
    return os.path.join(os.path.dirname(__file__), relative_path)

def run_yt_dlp_updater():
    """Run the yt-dlp_updater.exe binary in a separate thread."""
    def updater_thread():
        try:
            updater_path = resource_path(os.path.join('assets', 'yt-dlp_updater.exe'))
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
