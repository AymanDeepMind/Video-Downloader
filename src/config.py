import os
import configparser
import logging
from utils import logger

# Config file path
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".yt_downloader_config.ini")

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
        return False
    return True 