import os
import sys
import subprocess
import json
import tempfile
import logging
from urllib.parse import urlparse

# Configure logging
logger = logging.getLogger("phantom")

class PhantomJSHandler:
    """
    Class to handle websites that need PhantomJS to scrape content.
    """
    def __init__(self):
        # Get PhantomJS executable path
        if getattr(sys, 'frozen', False):
            # Running as compiled .exe
            self.phantomjs_path = os.path.join(os.path.dirname(sys.executable), 'assets', 'phantomjs.exe')
        else:
            # Running as script
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.phantomjs_path = os.path.join(current_dir, 'assets', 'phantomjs.exe')
        
        # Sites that are known to require PhantomJS
        self.phantom_required_domains = [
            'vimeo.com',
            'dailymotion.com',
            'twitch.tv',
            # Add more sites that typically need JS execution
        ]
        
        # JS script for extracting video info using PhantomJS
        self.extract_js = """
var page = require('webpage').create();
var system = require('system');
var url = system.args[1];

page.onConsoleMessage = function(msg) {
    console.log('PAGE LOG: ' + msg);
};

page.onError = function(msg, trace) {
    // Silence JS errors
};

page.open(url, function(status) {
    if (status !== 'success') {
        console.log(JSON.stringify({error: 'Failed to load page'}));
        phantom.exit(1);
    } else {
        // Wait for dynamic content to load
        setTimeout(function() {
            var result = page.evaluate(function() {
                var videoData = {
                    title: document.title,
                    videoUrls: [],
                    audioUrls: []
                };
                
                // Find video sources
                var videoElements = document.querySelectorAll('video');
                var videoSources = document.querySelectorAll('video source');
                
                // Extract from video elements
                Array.prototype.forEach.call(videoElements, function(video) {
                    if (video.src) videoData.videoUrls.push(video.src);
                });
                
                // Extract from source elements
                Array.prototype.forEach.call(videoSources, function(source) {
                    if (source.src) videoData.videoUrls.push(source.src);
                });
                
                // Look for JSON data containing media URLs
                var scripts = document.querySelectorAll('script');
                Array.prototype.forEach.call(scripts, function(script) {
                    if (script.text) {
                        // Search for media URLs in script content
                        var urlMatches = script.text.match(/(https?:\\/\\/[^"'\\s]+\\.(mp4|webm|m3u8|mp3|m4a)[^"'\\s]*)/g);
                        if (urlMatches) {
                            urlMatches.forEach(function(url) {
                                if (url.match(/\\.(mp4|webm|m3u8)$/)) {
                                    videoData.videoUrls.push(url);
                                } else if (url.match(/\\.(mp3|m4a)$/)) {
                                    videoData.audioUrls.push(url);
                                }
                            });
                        }
                        
                        // Look for HLS and DASH streams
                        if (script.text.includes('m3u8') || script.text.includes('mpd')) {
                            try {
                                var jsonData = script.text.match(/({[^;]*})/g);
                                if (jsonData) {
                                    jsonData.forEach(function(potential) {
                                        try {
                                            var obj = JSON.parse(potential);
                                            if (obj && typeof obj === 'object') {
                                                var jsonStr = JSON.stringify(obj);
                                                if (jsonStr.includes('m3u8')) {
                                                    var m3u8Matches = jsonStr.match(/(https?:\\/\\/[^"'\\s]+\\.m3u8[^"'\\s]*)/g);
                                                    if (m3u8Matches) {
                                                        m3u8Matches.forEach(function(url) {
                                                            videoData.videoUrls.push(url);
                                                        });
                                                    }
                                                }
                                            }
                                        } catch (e) {
                                            // Not valid JSON, ignore
                                        }
                                    });
                                }
                            } catch (e) {
                                // JSON parsing error, ignore
                            }
                        }
                    }
                });
                
                // Remove duplicates
                videoData.videoUrls = videoData.videoUrls.filter(function(item, pos, self) {
                    return self.indexOf(item) === pos;
                });
                videoData.audioUrls = videoData.audioUrls.filter(function(item, pos, self) {
                    return self.indexOf(item) === pos;
                });
                
                return videoData;
            });
            
            console.log(JSON.stringify(result));
            phantom.exit(0);
        }, 5000); // Wait 5 seconds for content to load
    }
});
"""
    
    def is_phantom_required(self, url):
        """
        Determine if a URL requires PhantomJS for content extraction.
        
        Args:
            url (str): The URL to check
            
        Returns:
            bool: True if PhantomJS should be used, False otherwise
        """
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # Check against known domains that require PhantomJS
            for phantom_domain in self.phantom_required_domains:
                if phantom_domain in domain:
                    logger.info(f"PhantomJS will be used for domain: {domain}")
                    return True
            
            # Additional heuristics could be added here
            
            return False
        except Exception as e:
            logger.error(f"Error in is_phantom_required: {str(e)}")
            return False
    
    def extract_media_urls(self, url):
        """
        Use PhantomJS to extract media URLs from a page.
        
        Args:
            url (str): The URL to extract media from
            
        Returns:
            dict: A dictionary with video and audio URLs extracted
        """
        if not os.path.exists(self.phantomjs_path):
            logger.error(f"PhantomJS executable not found at {self.phantomjs_path}")
            return {"error": "PhantomJS executable not found"}
        
        try:
            # Create temporary script file
            with tempfile.NamedTemporaryFile(suffix='.js', delete=False, mode='w') as temp:
                temp.write(self.extract_js)
                script_path = temp.name
            
            # Run PhantomJS
            logger.info(f"Running PhantomJS for URL: {url}")
            process = subprocess.Popen(
                [self.phantomjs_path, script_path, url],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(timeout=30)
            
            # Clean up temporary file
            try:
                os.unlink(script_path)
            except Exception as e:
                logger.warning(f"Failed to delete temporary script: {str(e)}")
            
            # Parse the output
            if process.returncode == 0 and stdout:
                try:
                    result = json.loads(stdout.strip())
                    return result
                except json.JSONDecodeError:
                    logger.error("Failed to parse PhantomJS output as JSON")
                    return {"error": "Invalid JSON output from PhantomJS"}
            else:
                logger.error(f"PhantomJS failed: {stderr}")
                return {"error": f"PhantomJS error: {stderr}"}
                
        except subprocess.TimeoutExpired:
            logger.error("PhantomJS process timed out")
            return {"error": "PhantomJS process timed out"}
        except Exception as e:
            logger.error(f"PhantomJS extraction error: {str(e)}")
            return {"error": f"PhantomJS extraction error: {str(e)}"}

    def get_ytdlp_compatible_urls(self, phantom_result):
        """
        Convert PhantomJS results into a format compatible with yt-dlp.
        
        Args:
            phantom_result (dict): The result from extract_media_urls
            
        Returns:
            list: A list of URLs that can be passed to yt-dlp
        """
        urls = []
        
        if "error" in phantom_result:
            return urls
            
        # Add video URLs
        if "videoUrls" in phantom_result and phantom_result["videoUrls"]:
            urls.extend(phantom_result["videoUrls"])
            
        # Add audio URLs
        if "audioUrls" in phantom_result and phantom_result["audioUrls"]:
            urls.extend(phantom_result["audioUrls"])
            
        return urls 