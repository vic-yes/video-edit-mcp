# Simple cross-platform output directory helper
import os
from pathlib import Path
import uuid
from moviepy.editor import VideoFileClip, AudioFileClip
from PIL import Image, ImageDraw, ImageFont
import tempfile
import logging

logger = logging.getLogger(__name__)

def get_output_path(filename: str) -> str:
    """Get cross-platform output path for files"""
    # Use environment variable if set, otherwise default to Downloads
    output_dir = os.environ.get("VIDEO_MCP_OUTPUT_DIR", str(Path.home() / "Downloads" / "video_mcp_output"))
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    return os.path.join(output_dir, filename)

class VideoStore:
    _store = {}

    @classmethod
    def store(cls, video_clip) -> str:
        ref = str(uuid.uuid4())
        cls._store[ref] = video_clip
        return ref

    @classmethod
    def load(cls, video_ref: str):
        if video_ref in cls._store:
            return cls._store[video_ref]
        return VideoFileClip(video_ref)
    
    @classmethod
    def clear(cls):
        cls._store.clear()
    
class AudioStore:
    _store = {}

    @classmethod
    def store(cls, audio_clip) -> str:
        ref = str(uuid.uuid4())
        cls._store[ref] = audio_clip
        return ref
    
    @classmethod
    def load(cls, audio_ref: str):
        if audio_ref in cls._store:
            return cls._store[audio_ref]
        return AudioFileClip(audio_ref)
    
    @classmethod
    def clear(cls):
        cls._store.clear()


