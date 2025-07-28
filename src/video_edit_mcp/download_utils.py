import yt_dlp
import os
import logging
from typing import Dict, Any, Optional, List
from .utils import VideoStore, AudioStore

logger = logging.getLogger(__name__)

def get_default_download_paths():
    """Get common download directory paths"""
    user_home = os.path.expanduser("~")
    return {
        "user_downloads": os.path.join(user_home, "Downloads"),
        "desktop": os.path.join(user_home, "Desktop"), 
        "documents": os.path.join(user_home, "Documents"),
        "project_root": os.path.abspath(".") if "video_edit_mcp" in os.path.abspath(".") else None
    }

def register_download_and_utility_tools(mcp):
    """Register all download and utility tools with the MCP server"""
    @mcp.tool(description= "use this tool to download videos make sure to give proper path for saving video not just name, if there are multiple steps to be done after downloading then make sure to return object and return path should be false else return path should be true")
    def download_video(
        url: str,
        save_path: Optional[str] = None,
        audio_only: bool = False,
        **yt_dlp_options: Any
    ) -> Dict[str, Any]:
        """
        Download video or audio from URL using yt-dlp
        
        Args:
            url: URL to download from
            save_path: Directory path or full file path template where to save
            audio_only: If True, download and extract audio only
            **yt_dlp_options: Additional yt-dlp options
            
        Returns:
            Dict with success status, file path, and other info
        """
        try:
            # Start with user-provided yt-dlp options
            ydl_opts = yt_dlp_options.copy()
            
            # --- Handle Core Parameters ---
            
            # 1. Set output path template if not already specified by user
            if 'outtmpl' not in ydl_opts:
                if save_path:
                    # Check if user provided a relative path that might cause confusion
                    if not os.path.isabs(save_path) and not save_path.startswith('.'):
                        logger.warning(f"Relative path detected: '{save_path}'. This will save relative to current directory: {os.getcwd()}")
                        
                    # Convert save_path to absolute path first
                    save_path = os.path.abspath(save_path)
                    
                    if os.path.isdir(save_path):
                        # save_path is a directory
                        ydl_opts['outtmpl'] = os.path.join(save_path, '%(title)s [%(id)s].%(ext)s')
                    else:
                        # save_path could be a full path or template
                        # Check if it contains yt-dlp template variables
                        if '%(' in save_path:
                            ydl_opts['outtmpl'] = save_path
                        else:
                            # Treat as full file path, ensure directory exists
                            directory = os.path.dirname(save_path)
                            if directory and not os.path.exists(directory):
                                os.makedirs(directory, exist_ok=True)
                            ydl_opts['outtmpl'] = save_path
                else:
                    # Default to user's Downloads folder instead of current directory
                    default_paths = get_default_download_paths()
                    downloads_dir = default_paths["user_downloads"]
                    
                    # Create Downloads directory if it doesn't exist
                    os.makedirs(downloads_dir, exist_ok=True)
                    ydl_opts['outtmpl'] = os.path.join(downloads_dir, '%(title)s [%(id)s].%(ext)s')

            # 2. Configure for audio-only downloads
            if audio_only:
                # Set format to best audio
                ydl_opts['format'] = 'bestaudio/best'
                # Ensure post-processor is set to extract audio (defaults to mp3)
                if 'postprocessors' not in ydl_opts:
                    ydl_opts['postprocessors'] = []
                
                # Add audio extraction post-processor
                audio_postprocessor = {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': ydl_opts.get('audio_format', 'mp3'),
                    'preferredquality': ydl_opts.get('audio_quality', '192'),
                }
                ydl_opts['postprocessors'].append(audio_postprocessor)

            # Add logger
            ydl_opts['logger'] = logger

            # --- Execute Download ---
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info and download
                info = ydl.extract_info(url, download=not ydl_opts.get('simulate', False))
                
                # Prepare response
                response = {
                    "success": True,
                    "message": "Operation successful!",
                    "title": info.get('title', 'Unknown'),
                    "id": info.get('id', 'Unknown'),
                    "duration": info.get('duration'),
                    "uploader": info.get('uploader')
                }
                
                # If not simulating, get the actual file path
                if not ydl_opts.get('simulate', False):
                    # Get the base filename that yt-dlp would use
                    base_filepath = ydl.prepare_filename(info)
                    
                    # Convert to absolute path
                    base_filepath = os.path.abspath(base_filepath)
                    
                    # For audio-only downloads, the file extension will change
                    if audio_only:
                        # Find the audio codec used
                        audio_codec = ydl_opts.get('audio_format', 'mp3')
                        # Change extension to match the extracted audio format
                        base_name = os.path.splitext(base_filepath)[0]
                        actual_filepath = f"{base_name}.{audio_codec}"
                    else:
                        actual_filepath = base_filepath
                    
                    # Ensure we have absolute path
                    actual_filepath = os.path.abspath(actual_filepath)
                    
                    # Verify the file exists
                    if os.path.exists(actual_filepath):
                        response.update({
                            "filepath": actual_filepath,
                            "filename": os.path.basename(actual_filepath),
                            "directory": os.path.dirname(actual_filepath),
                            "file_size": os.path.getsize(actual_filepath)
                        })
                    else:
                        # If exact path doesn't exist, try to find the actual file
                        # This handles cases where yt-dlp might have modified the filename
                        directory = os.path.dirname(actual_filepath)
                        base_name = os.path.splitext(os.path.basename(actual_filepath))[0]
                        
                        # Look for files with similar names in the directory
                        if os.path.exists(directory):
                            found_file = None
                            for file in os.listdir(directory):
                                if base_name in file or info.get('id', '') in file:
                                    found_file = file
                                    break
                            
                            if found_file:
                                found_filepath = os.path.abspath(os.path.join(directory, found_file))
                                response.update({
                                    "filepath": found_filepath,
                                    "filename": found_file,
                                    "directory": os.path.dirname(found_filepath),
                                    "file_size": os.path.getsize(found_filepath),
                                    "note": "Filename was modified during download"
                                })
                            else:
                                response.update({
                                    "filepath": actual_filepath,
                                    "filename": os.path.basename(actual_filepath),
                                    "directory": os.path.dirname(actual_filepath),
                                    "warning": "File path expected but not found at exact location",
                                    "expected_path": actual_filepath
                                })
                        else:
                            response.update({
                                "filepath": actual_filepath,
                                "filename": os.path.basename(actual_filepath),
                                "directory": os.path.dirname(actual_filepath),
                                "warning": "Directory not found",
                                "expected_path": actual_filepath
                            })
                else:
                    # Simulation mode
                    simulated_path = ydl.prepare_filename(info)
                    response["simulated_filepath"] = os.path.abspath(simulated_path)
                    response["message"] = "Simulation successful - no file downloaded"

                return response
                
        except Exception as e:
            logger.error(f"Error during video download from {url}: {e}", exc_info=True)
            return {
                "success": False, 
                "error": str(e), 
                "error_type": type(e).__name__,
                "url": url,
                "message": "Download failed"
            }

    @mcp.tool(description="Get suggested download directory paths for saving videos/audio files")
    def get_download_paths() -> Dict[str, Any]:
        """
        Get suggested common download directory paths
        
        Returns:
            Dict with suggested download paths
        """
        try:
            paths = get_default_download_paths()
            current_dir = os.getcwd()
            
            return {
                "success": True,
                "current_working_directory": current_dir,
                "suggested_paths": {
                    "user_downloads": paths["user_downloads"],
                    "desktop": paths["desktop"],
                    "documents": paths["documents"],
                    "project_root": paths["project_root"],
                    "current_directory": current_dir
                },
                "usage_examples": {
                    "save_to_downloads": paths["user_downloads"],
                    "save_to_custom_folder": os.path.join(paths["user_downloads"], "YouTube_Videos"),
                    "save_to_desktop": paths["desktop"]
                },
                "note": "Use full absolute paths to avoid saving in unexpected locations"
            }
        except Exception as e:
            logger.error(f"Error getting download paths: {e}")
            return {
                "success": False,
                "error": str(e),
                "current_directory": os.getcwd(),
                "message": "Error getting download paths"
            }

    