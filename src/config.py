import os
import configparser
import logging
import sys

# Adjust import paths dynamically
if getattr(sys, 'frozen', False):
    # Running as compiled .exe
    from utils import logger
else:
    # Running directly as .py
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
        if os.path.exists(CONFIG_FILE):
            config.read(CONFIG_FILE)
        
        if 'Settings' not in config:
            config['Settings'] = {}
            
        config['Settings']['download_folder'] = folder
        
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

def load_fragments_config():
    """Load the optimal fragments count from the config file if available."""
    try:
        config = configparser.ConfigParser()
        if os.path.exists(CONFIG_FILE):
            config.read(CONFIG_FILE)
            if 'Settings' in config and 'optimal_fragments' in config['Settings']:
                return int(config['Settings']['optimal_fragments'])
    except Exception as e:
        logger.error(f"Error loading fragments config: {str(e)}")
    return None  # Return None if not found or error occurs

def save_fragments_config(fragments):
    """Save the optimal fragments count into the config file."""
    try:
        config = configparser.ConfigParser()
        if os.path.exists(CONFIG_FILE):
            config.read(CONFIG_FILE)
            
        if 'Settings' not in config:
            config['Settings'] = {}
            
        config['Settings']['optimal_fragments'] = str(fragments)
        
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
        logger.error(f"Error saving fragments config: {str(e)}")
        return False
    return True 