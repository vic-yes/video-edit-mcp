from typing import Dict, Any
from moviepy.editor import VideoFileClip, AudioFileClip
import os
import logging
from .utils import VideoStore, AudioStore

logger = logging.getLogger(__name__)


def register_util_tools(mcp):
    @mcp.tool(description="Use this tool to check what is stored in memory, like objects and etc.")
    def check_memory(store_type: str = "both") -> Dict[str, Any]:
        """
        Check what objects are stored in memory.
        
        Args:
            store_type: Type of store to check ("video", "audio", or "both")
        """
        try:
            if store_type.lower() == "video":
                return {
                    "success": True,
                    "video_memory": VideoStore._store,
                    "video_count": len(VideoStore._store)
                }
            elif store_type.lower() == "audio":
                return {
                    "success": True,
                    "audio_memory": AudioStore._store,
                    "audio_count": len(AudioStore._store)
                }
            else:  # both or any other value
                return {
                    "success": True,
                    "video_memory": VideoStore._store,
                    "audio_memory": AudioStore._store,
                    "video_count": len(VideoStore._store),
                    "audio_count": len(AudioStore._store),
                    "total_objects": len(VideoStore._store) + len(AudioStore._store)
                }
        except Exception as e:
            logger.error(f"Error checking memory: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Error checking memory"
            }

    @mcp.tool(description="Use this tool for clearing all stored video and audio objects from memory to free up space")
    def clear_memory(clear_videos:bool, clear_audios:bool) -> Dict[str,Any]:
        try:
            if clear_videos:
                VideoStore.clear()
            if clear_audios:
                AudioStore.clear()
            return {
                "success": True,
                "message": f"Memory cleared - Videos: {clear_videos}, Audios: {clear_audios}"
            }
        except Exception as e:
            logger.error(f"Error clearing memory: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Error clearing memory"
            }

    @mcp.tool(description="Use this tool for listing files in a directory, provide directory path")
    def list_files(directory_path: str) -> Dict[str, Any]:
        try:
            if not os.path.exists(directory_path):
                return {
                    "success": False,
                    "error": "Directory does not exist",
                    "message": "Provide valid directory path"
                }
            files = os.listdir(directory_path)
            return {
                "success": True,
                "files": files
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error listing files"
            }
        
    @mcp.tool(description="Use this tool to create a directory to store output files, make sure to provide accurate path")
    def make_directory(directory_path: str) -> Dict[str, Any]:
        try:
            os.makedirs(directory_path, exist_ok=True)
            return {
                "success": True,
                "message": "Directory created successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error creating directory"
            } 