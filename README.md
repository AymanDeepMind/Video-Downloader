# ADM Video Downloader

A powerful Windows video downloader application that allows you to download videos and audio from various online platforms with customizable quality options.

## Features

- **Multiple Download Types**:
  - Video + Audio (MP4)
  - Video Only (MP4)
  - Audio Only (MP3)
- **Quality Selection**: Choose from various resolution and bitrate options
- **Custom Titles**: Edit video titles before downloading
- **User-Friendly Interface**: Clean, themed UI with progress tracking
- **Persistent Settings**: Remembers your download folder location
- **Built-in FFmpeg**: Bundled with FFmpeg for media conversion

## System Requirements

- Windows 7, 8, 8.1, 10, or 11
- No installation required (portable application)

## Installation

### Option 1: Download Binary (For common users)

1. Go to the [Releases](https://github.com/aymandeepmind/video-downloader/releases) page
2. Download the latest version
3. Extract the downloaded file
4. Run `ADM Video Downloader.exe`

### Option 2: Run from Source (Mainly for developers)

1. Clone this repository:
   ```
   git clone https://github.com/aymandeepmind/video-downloader.git
   cd video-downloader
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python src/main.py
   ```

## Usage

1. **Paste URL**: Copy the video URL and click "Paste"
2. **Select Download Type**: Choose between Video+Audio, Video Only, or Audio Only
3. **Fetch Formats**: Click "Fetch Formats" to retrieve available quality options
4. **Edit Title** (Optional): Click "Edit title" to customize the filename
5. **Select Format**: Choose your preferred quality/resolution
6. **Choose Download Location**: Select a folder to save the download
7. **Download**: Click "Download" to start the download process

## Dependencies

- Python 3.6+ (for development)
- yt-dlp
- tkinter
- PyQt5
- FFmpeg (bundled)
- PhantomJS

## Building from Source

To create a standalone executable:

```
pip install pyinstaller
```
In the src directory, run this in the terminal:
```
pyinstaller main.spec
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Contact

GitHub: [aymandeepmind](https://github.com/aymandeepmind)

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - The core downloading engine
- [FFmpeg](https://ffmpeg.org/) - For media processing
- [PyQt5](https://github.com/PyQt/PyQt5) - For the UI theme
- [PhantomJS](https://github.com/ariya/phantomjs) - For headless browser automation