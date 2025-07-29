from moviepy.editor import *
from moviepy.audio.fx.all import audio_loop
from moviepy.editor import CompositeAudioClip
from typing import Dict, Any, List
import os
import logging
from .utils import get_output_path, AudioStore

logger = logging.getLogger(__name__)

def register_audio_tools(mcp):
    """Register all audio processing tools with the MCP server"""
    
    @mcp.tool(description="get audio info")
    def audio_info(audio_path:str) -> Dict[str,Any]:
        try:
            
            audio = AudioFileClip(audio_path)
            return{
                "success": True,
                "audio_info": {
                    "duration": audio.duration,
                    "fps": audio.fps,
                    "channels": audio.nchannels
                }
            }
        except Exception as e:
            logger.error(f"Error getting audio info for {audio_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }

    @mcp.tool(description="Use this tool for extracting audio from the video , and make sure only give output name like extracted_audio.mp3 , some_hello.mp3 etc.. don't pass path just give meaningful names based on audio info, if there are multiple steps to be done after extracting audio then make sure to return object and return path should be false else return path should be true")
    def extract_audio(video_path: str, output_name: str, return_path: bool) -> Dict[str, Any]:
        try:
            output_path = get_output_path(output_name)
            from .utils import VideoStore
            video = VideoStore.load(video_path)
            
            if video.audio is None:
                return {
                    "success": False,
                    "error": "Video has no audio track",
                    "message": "No audio to extract"
                }
            
            audio = video.audio
            if return_path:
                audio.write_audiofile(output_path)
                return {
                    "success": True,
                    "output_path": output_path,
                    "message": "Audio extracted successfully"
                }
            else:
                ref = AudioStore.store(audio)
                return {
                    "success": True,
                    "output_object": ref
                }
        except Exception as e:
            logger.error(f"Error extracting audio from {video_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Error extracting audio"
            }

    @mcp.tool(description="Trim audio file, make sure to provide proper start and end time, and make sure to provide output name like trimmed_audio.mp3, some_hello.mp3 etc. don't pass path just give meaningful names based on audio info, if there are multiple steps to be done after trimming then make sure to return object and return path should be false else return path should be true")
    def trim_audio(audio_path: str, start_time: float, end_time: float, output_name: str, return_path: bool) -> Dict[str, Any]:
        try:
            # Input validation
            if start_time < 0 or end_time < 0:
                return {
                    "success": False,
                    "error": "Start and end times must be positive",
                    "message": "Invalid time parameters"
                }
            if start_time >= end_time:
                return {
                    "success": False,
                    "error": "Start time must be less than end time",
                    "message": "Invalid time range"
                }
            
            output_path = get_output_path(output_name)
            audio = AudioStore.load(audio_path)
            trimmed_audio = audio.subclip(start_time, end_time)
            
            if return_path:
                trimmed_audio.write_audiofile(output_path)
                return {
                    "success": True,
                    "output_path": output_path,
                    "message": "Audio trimmed successfully"
                }
            else:
                ref = AudioStore.store(trimmed_audio)
                return {
                    "success": True,
                    "output_object": ref,
                    "message": "Audio trimmed successfully"
                }
        except Exception as e:
            logger.error(f"Error trimming audio {audio_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Error trimming audio"
            }

    @mcp.tool(description="Use this tool to concatenate two audios, if there are multiple steps to be done after concatenating then make sure to return object and return path should be false else return path should be true")
    def concatenate_audio(audio_path_1: str, audio_path_2: str, output_name: str, return_path: bool) -> Dict[str, Any]:
        try:
            output_path = get_output_path(output_name)
            audio_1 = AudioStore.load(audio_path_1)
            audio_2 = AudioStore.load(audio_path_2)
            concatenated_audio = concatenate_audioclips([audio_1, audio_2])
            
            if return_path:
                concatenated_audio.write_audiofile(output_path)
                return {
                    "success": True,
                    "output_path": output_path,
                    "message": "Audio concatenated successfully"
                }
            else:
                ref = AudioStore.store(concatenated_audio)
                return {
                    "success": True,
                    "output_object": ref,
                    "message": "Audio concatenated successfully"
                }
        except Exception as e:
            logger.error(f"Error concatenating audio files {audio_path_1} and {audio_path_2}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Error concatenating audio files"
            }

    @mcp.tool(description="Use this tool to loop the audio, after looping make sure to provide output name like looped_audio.mp3, some_hello.mp3 etc. don't pass path just give meaningful names based on audio info and also make sure to provide duration in seconds, if there are multiple steps to be done after looping then make sure to return object and return path should be false else return path should be true")
    def loop_audio(audio_path: str, duration: float, output_name: str, return_path: bool) -> Dict[str, Any]:
        try:
            # Input validation
            if duration <= 0:
                return {
                    "success": False,
                    "error": "Duration must be positive",
                    "message": "Invalid duration parameter"
                }
            
            output_path = get_output_path(output_name)
            audio = AudioStore.load(audio_path)
            looped_audio = audio_loop(audio, duration=duration)
            
            if return_path:
                looped_audio.write_audiofile(output_path)
                return {
                    "success": True,
                    "output_path": output_path,
                    "message": "Audio looped successfully"
                }
            else:
                ref = AudioStore.store(looped_audio)
                return {
                    "success": True,
                    "output_object": ref,
                    "message": "Audio looped successfully"
                }
        except Exception as e:
            logger.error(f"Error looping audio {audio_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Error looping audio"
            }

    @mcp.tool(description="Adjust volume of an audio, if there are multiple steps to be done after adjusting volume then make sure to return object and return path should be false else return path should be true")
    def adjust_vol(audio_path: str, volume_level: float, output_name: str, return_path: bool) -> Dict[str, Any]:
        try:
            # Input validation
            if volume_level <= 0:
                return {
                    "success": False,
                    "error": "Volume level must be positive (e.g., 1.0 for normal, 2.0 for double)",
                    "message": "Invalid volume level parameter"
                }
            
            output_path = get_output_path(output_name)
            audio = AudioStore.load(audio_path)
            audio_adjusted = audio.volumex(volume_level)
            
            if return_path:
                audio_adjusted.write_audiofile(output_path)
                return {
                    "success": True,
                    "output_path": output_path,
                    "message": "Audio volume adjusted successfully"
                }
            else:
                ref = AudioStore.store(audio_adjusted)
                return {
                    "success": True,
                    "output_object": ref,
                    "message": "Audio volume adjusted successfully"
                }
        except Exception as e:
            logger.error(f"Error adjusting audio volume {audio_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Error adjusting audio volume"
            }

    @mcp.tool(description="Use this tool for audio fade in effect, provide fade_duration in seconds, and output name like fadein_audio.mp3, if there are multiple steps to be done after adding fade in then make sure to return object and return path should be false else return path should be true")
    def fadein_audio(audio_path:str, fade_duration:float, output_name:str, return_path:bool) -> Dict[str,Any]:
        try:
            output_path = get_output_path(output_name)
            audio = AudioStore.load(audio_path)
            fadein_audio = audio.audio_fadein(fade_duration)
            if return_path:
                fadein_audio.write_audiofile(output_path)
                return {
                    "success": True,
                    "output_path": output_path,
                    "message": "Audio fade in effect added successfully"
                }
            else:
                ref = AudioStore.store(fadein_audio)
                return {
                    "success": True,
                    "output_object": ref
                }
        except Exception as e:
            logger.error(f"Error adding audio fade in effect {audio_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Error adding audio fade in effect"
            }

    @mcp.tool(description="Use this tool for audio fade out effect, provide fade_duration in seconds, and output name like fadeout_audio.mp3, if there are multiple steps to be done after adding fade out then make sure to return object and return path should be false else return path should be true")
    def fadeout_audio(audio_path:str, fade_duration:float, output_name:str, return_path:bool) -> Dict[str,Any]:
        try:
            output_path = get_output_path(output_name)
            audio = AudioStore.load(audio_path)
            fadeout_audio = audio.audio_fadeout(fade_duration)
            if return_path:
                fadeout_audio.write_audiofile(output_path)
                return {
                    "success": True,
                    "output_path": output_path,
                    "message": "Audio fade out effect added successfully"
                }
            else:
                ref = AudioStore.store(fadeout_audio)
                return {
                    "success": True,
                    "output_object": ref
                }
        except Exception as e:
            logger.error(f"Error adding audio fade out effect {audio_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Error adding audio fade out effect"
            }

    @mcp.tool(description="Use this tool for mixing multiple audio tracks together, provide list of audio paths and output name, if there are multiple steps to be done after mixing audio tracks then make sure to return object and return path should be false else return path should be true")
    def mix_audio_tracks(audio_paths:List[str], output_name:str, return_path:bool) -> Dict[str,Any]:
        try:
            output_path = get_output_path(output_name)
            audio_clips = [AudioStore.load(clips) for clips in audio_paths]
            mixed_audio = CompositeAudioClip(audio_clips)
            mixed_audio.fps = 44100
            if return_path:
                    try:
                        mixed_audio.write_audiofile(output_path)
                        return {
                        "success": True,
                        "output_path": output_path,
                        "message": "Audio tracks mixed successfully"
                    }
                    except Exception as write_error:
                        return {
                        "success": False,
                        "error": f"Failed to write file: {str(write_error)}",
                        "message": "File writing failed"
                        }
            else:
                    return {
                    "success": True,
                    "output_object": mixed_audio
                    }

        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "error_type": type(e).__name__,
                "message": "Unexpected error occurred"
            } 