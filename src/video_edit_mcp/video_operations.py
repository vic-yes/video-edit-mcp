from moviepy.editor import *
from moviepy.video.fx import *
from moviepy.video.fx.speedx import speedx
from moviepy.video.fx.rotate import rotate
from moviepy.video.fx.crop import crop
from moviepy.video.fx.resize import resize
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
from moviepy.video.fx.blackwhite import blackwhite
from moviepy.video.fx.mirror_x import mirror_x
from moviepy.editor import ColorClip, ImageClip, CompositeVideoClip, VideoFileClip, TextClip
import cv2
import numpy as np
import random
from typing import Dict, Any, Optional, List, Tuple
import os
import logging
import imageio
from .utils import get_output_path, VideoStore, AudioStore
import moviepy.config as mpy_conf


logger = logging.getLogger(__name__)

def register_video_tools(mcp):
    """Register all video processing tools with the MCP server"""
    
    @mcp.tool()
    def get_video_info(video_path: str) -> Dict[str, Any]:
        """Get comprehensive information about a video file including duration, fps, resolution, codec details, and audio information."""
        try:
            # Load video file
            video = VideoFileClip(video_path)
            
            # Basic video information
            info = {
                "file_path": video_path,
                "filename": os.path.basename(video_path),
                "duration": video.duration,
                "fps": video.fps,
                "size": video.size,  # (width, height)
                "width": video.w,
                "height": video.h,
                "aspect_ratio": round(video.w / video.h, 2) if video.h > 0 else None,
            }
            
            # Add reader/codec information if available
            if hasattr(video, 'reader') and video.reader:
                reader_info = {
                    "nframes": getattr(video.reader, 'nframes', None),
                    "bitrate": getattr(video.reader, 'bitrate', None),
                    "codec": getattr(video.reader, 'codec', None),
                    "pix_fmt": getattr(video.reader, 'pix_fmt', None),
                }
                # Only add non-None values
                info.update({k: v for k, v in reader_info.items() if v is not None})
            
            # Audio information
            if video.audio is not None:
                audio_info = {
                    "has_audio": True,
                    "audio_duration": video.audio.duration,
                    "audio_fps": video.audio.fps,
                    "audio_channels": getattr(video.audio, 'nchannels', None),
                }
                
                # Add audio reader info if available
                if hasattr(video.audio, 'reader') and video.audio.reader:
                    audio_reader_info = {
                        "audio_bitrate": getattr(video.audio.reader, 'bitrate', None),
                        "audio_codec": getattr(video.audio.reader, 'codec', None),
                        "sample_rate": getattr(video.audio.reader, 'fps', None),
                    }
                    # Only add non-None values
                    audio_info.update({k: v for k, v in audio_reader_info.items() if v is not None})
            else:
                audio_info = {
                    "has_audio": False,
                    "audio_duration": None,
                    "audio_fps": None,
                    "audio_channels": None,
                }
            
            info.update(audio_info)
            
            # File size information
            try:
                file_size = os.path.getsize(video_path)
                info["file_size_bytes"] = file_size
                info["file_size_mb"] = round(file_size / (1024 * 1024), 2)
            except OSError:
                info["file_size_bytes"] = None
                info["file_size_mb"] = None
            
            # Calculate video quality metrics
            if info["duration"] and info["duration"] > 0:
                info["total_frames"] = int(info["fps"] * info["duration"]) if info["fps"] else None
                if info.get("file_size_bytes"):
                    info["average_bitrate_kbps"] = round((info["file_size_bytes"] * 8) / (info["duration"] * 1000), 2)
            
            # Clean up video object to prevent memory leaks
            video.close()
            
            return {
                "success": True,
                "video_info": info
            }
            
        except Exception as e:
            logger.error(f"Error getting video info for {video_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
        finally:
            # Ensure video object is cleaned up even if an exception occurs
            try:
                if 'video' in locals():
                    video.close()
            except:
                pass

    @mcp.tool(description="Use this tool for trimming the video, provide start and end time in seconds, and output name like trimmed_video.mp4 , if there are multiple steps to be done after trimming then make sure to return object and return path should be false else return path should be true")
    def trim_video(video_path: str, start_time: float, end_time: float, output_name: str, return_path: bool) -> Dict[str, Any]:
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
            video = VideoStore.load(video_path)
            trimmed_video = video.subclip(start_time, end_time)

            if return_path:
                trimmed_video.write_videofile(output_path)
                return {
                    "success": True,
                    "output_path": output_path,
                    "message": "Video trimmed successfully"
                }
            else:
                ref = VideoStore.store(trimmed_video)
                return {
                    "success": True,
                    "output_object": ref
                }
        except Exception as e:
            logger.error(f"Error trimming video {video_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Error trimming video"
            }
 
    @mcp.tool(description="Use this tool for resizing the video make sure first whether video needs to be saved directly or just object has to be returned for further processing, if there are multiple steps to be done after resizing then make sure to return object and return path should be false else return path should be true")
    def resize_video(video_path: str, size: Tuple[int, int], output_name: str, return_path: bool) -> Dict[str, Any]:
        cap = cv2.VideoCapture(video_path)
    
        if not cap.isOpened():
            raise Exception(f"Can't open the video: {video_path}")
        
        try:
            # Input validation
            if not size or len(size) != 2 or size[0] <= 0 or size[1] <= 0:
                return {
                    "success": False,
                    "error": "Size must be a tuple of two positive integers (width, height)",
                    "message": "Invalid size parameters"
                }
            
            output_path = get_output_path(output_name)

            original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            target_width, target_height = size
            
            # 计算保持原始比例的新尺寸
            original_aspect = original_width / original_height
            target_aspect = target_width / target_height
            
            # 计算缩放后的尺寸（不拉伸）
            if original_aspect > target_aspect:
                # 原始视频更宽，以宽度为基准缩放
                scale_factor = target_width / original_width
                new_width = target_width
                new_height = int(original_height * scale_factor)
            else:
                # 原始视频更高，以高度为基准缩放
                scale_factor = target_height / original_height
                new_width = int(original_width * scale_factor)
                new_height = target_height
            
            # even size
            new_width = new_width - (new_width % 2)
            new_height = new_height - (new_height % 2)

            logger.info(f"cv_original_width: {original_width}, cv_original_height: {original_height}")
            logger.info(f"new_width: {new_width}, new_height: {new_height}")
            # 首先调整视频大小（不拉伸）
            resized_clip = VideoFileClip(video_path, target_resolution=(new_height,new_width))
            logger.info(f"resized video size: {resized_clip.size}")

            # 创建黑色背景
            background = ColorClip(
                size=(target_width, target_height),
                color=(0, 0, 0),
                duration=resized_clip.duration
            )
            
            # 计算居中位置
            x_pos = (target_width - new_width) // 2
            y_pos = (target_height - new_height) // 2
            
            # 将调整后的视频叠加到黑色背景上
            final_video = CompositeVideoClip(
                [background, resized_clip.set_position((x_pos, y_pos))],
                size=(target_width, target_height)
            )
            
            if return_path:
                final_video.write_videofile(output_path, codec='libx264', audio_codec='aac')
                return {
                    "success": True,
                    "output_path": output_path,
                    "message": "Video resized successfully"
                }
            else:
                ref = VideoStore.store(final_video)
                return {
                    "success": True,
                    "output_object": ref
                }
        except Exception as e:
            logger.error(f"Error resizing video {video_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Error resizing video"
            }
        finally:
            # 释放视频捕获对象
            cap.release()

    @mcp.tool(description="Use this tool for cropping the video, provide x1, y1, x2, y2 coordinates, and output name like cropped_video.mp4 , if there are multiple steps to be done after cropping then make sure to return object and return path should be false else return path should be true")
    def crop_video(video_path: str, x1: int, y1: int, x2: int, y2: int, output_name: str, return_path: bool) -> Dict[str, Any]:
        try:
            # Input validation
            if x1 < 0 or y1 < 0 or x2 <= x1 or y2 <= y1:
                return {
                    "success": False,
                    "error": "Invalid crop coordinates. x2 > x1 and y2 > y1, all values must be non-negative",
                    "message": "Invalid crop parameters"
                }
            
            output_path = get_output_path(output_name)
            video = VideoStore.load(video_path)
            cropped_video = crop(video, x1, y1, x2, y2)
            
            if return_path:
                cropped_video.write_videofile(output_path)
                return {
                    "success": True,
                    "output_path": output_path,
                    "message": "Video cropped successfully"
                }
            else:
                ref = VideoStore.store(cropped_video)
                return {
                    "success": True,
                    "output_object": ref
                }
        except Exception as e:
            logger.error(f"Error cropping video {video_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Error cropping video"
            }

    @mcp.tool(description="Use this tool for rotating the video, and make sure to provide output name like rotated_video.mp4 , some_hello.mp4 etc. don't pass path just give meaningful names based on video info, if there are multiple steps to be done after rotating then make sure to return object and return path should be false else return path should be true")
    def rotate_video(video_path: str, angle: int, output_name: str, return_path: bool) -> Dict[str, Any]:
        try:
            # Input validation
            if not isinstance(angle, (int, float)):
                return {
                    "success": False,
                    "error": "Angle must be a number",
                    "message": "Invalid angle parameter"
                }
            
            output_path = get_output_path(output_name)
            video = VideoStore.load(video_path)
            rotated_video = rotate(video, angle)
            
            if return_path:
                rotated_video.write_videofile(output_path)
                return {
                    "success": True,
                    "output_path": output_path,
                    "message": "Video rotated successfully"
                }
            else:
                ref = VideoStore.store(rotated_video)
                return {
                    "success": True,
                    "output_object": ref
                }
        except Exception as e:
            logger.error(f"Error rotating video {video_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Error rotating video"
            }

    @mcp.tool(description="Use this tool for speed up the video, and make sure to provide output name like speed_up_video.mp4 , some_hello.mp4 etc. don't pass path just give meaningful names based on video info, if there are multiple steps to be done after speed up then make sure to return object and return path should be false else return path should be true")
    def speed_up_video(video_path: str, speed: float, output_name: str, return_path: bool) -> Dict[str, Any]:
        try:
            # Input validation
            if speed <= 0:
                return {
                    "success": False,
                    "error": "Speed must be positive (e.g., 2.0 for 2x speed)",
                    "message": "Invalid speed parameter"
                }
            
            output_path = get_output_path(output_name)
            video = VideoStore.load(video_path)
            sped_up_video = speedx(video, speed)

            if return_path:
                sped_up_video.write_videofile(output_path)
                return {
                    "success": True,
                    "output_path": output_path,
                    "message": "Video speed changed successfully"
                }
            else:
                ref = VideoStore.store(sped_up_video)
                return {
                    "success": True,
                    "output_object": ref
                }
        except Exception as e:
            logger.error(f"Error changing video speed {video_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Error changing video speed"
            }

    @mcp.tool(description="Use this tool for adding audio to the video , and make sure to provide output file name like added_audio.mp4 etc. make sure mp4 extension is provided and name should be meaningful, if there are multiple steps to be done after adding audio then make sure to return object and return path should be false else return path should be true")
    def add_audio(video_path: str, audio_path: str, output_name: str, return_path: bool) -> Dict[str, Any]:
        try:
            output_path = get_output_path(output_name)
            video = VideoStore.load(video_path)
            audio = AudioStore.load(audio_path)
            new_video = video.set_audio(audio)
            
            if return_path:
                new_video.write_videofile(output_path)
                return {
                    "success": True,
                    "output_path": output_path,
                    "message": "Audio added successfully"
                }
            else:
                ref = VideoStore.store(new_video)
                return {
                    "success": True,
                    "output_object": ref
                }
        except Exception as e:
            logger.error(f"Error adding audio to video {video_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Error adding audio to video"
            }

    @mcp.tool(description="Use this tool for adding fade in effect to video, provide fade_duration in seconds, and output name like fadein_video.mp4, if there are multiple steps to be done after adding fade in then make sure to return object and return path should be false else return path should be true")
    def fadein_video(video_path: str, fade_duration: float, output_name: str, return_path: bool) -> Dict[str, Any]:
        try:
            # Input validation
            if fade_duration <= 0:
                return {
                    "success": False,
                    "error": "Fade duration must be positive",
                    "message": "Invalid fade duration parameter"
                }
            
            output_path = get_output_path(output_name)
            video = VideoStore.load(video_path)
            faded_video = fadein(video, fade_duration)
            
            if return_path:
                faded_video.write_videofile(output_path)
                return {
                    "success": True,
                    "output_path": output_path,
                    "message": "Fade in effect added successfully"
                }
            else:
                ref = VideoStore.store(faded_video)
                return {
                    "success": True,
                    "output_object": ref
                }
        except Exception as e:
            logger.error(f"Error adding fade in effect to video {video_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Error adding fade in effect"
            }

    @mcp.tool(description="Use this tool for adding fade out effect to video, provide fade_duration in seconds, and output name like fadeout_video.mp4, if there are multiple steps to be done after adding fade out then make sure to return object and return path should be false else return path should be true")
    def fadeout_video(video_path: str, fade_duration: float, output_name: str, return_path: bool) -> Dict[str, Any]:
        try:
            # Input validation
            if fade_duration <= 0:
                return {
                    "success": False,
                    "error": "Fade duration must be positive",
                    "message": "Invalid fade duration parameter"
                }
            
            output_path = get_output_path(output_name)
            video = VideoStore.load(video_path)
            faded_video = fadeout(video, fade_duration)
            
            if return_path:
                faded_video.write_videofile(output_path)
                return {
                    "success": True,
                    "output_path": output_path,
                    "message": "Fade out effect added successfully"
                }
            else:
                ref = VideoStore.store(faded_video)
                return {
                    "success": True,
                    "output_object": ref
                }
        except Exception as e:
            logger.error(f"Error adding fade out effect to video {video_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Error adding fade out effect"
            }

    @mcp.tool(description="Use this tool for adding text overlay to video, provide text, position coordinates (x,y), font_size, color, and output name, if there are multiple steps to be done after adding text overlay then make sure to return object and return path should be false else return path should be true")
    def add_text_overlay(video_path: str, text: str, x: int, y: int, font_size: int, color: str, duration: float, output_name: str, return_path: bool, path_of_imagemagick: str) -> Dict[str, Any]:
        try:
            # Input validation
            if not text or not text.strip():
                return {
                    "success": False,
                    "error": "Text cannot be empty",
                    "message": "Invalid text parameter"
                }
            if font_size <= 0:
                return {
                    "success": False,
                    "error": "Font size must be positive",
                    "message": "Invalid font size parameter"
                }
            if duration <= 0:
                return {
                    "success": False,
                    "error": "Duration must be positive",
                    "message": "Invalid duration parameter"
                }
            
            output_path = get_output_path(output_name)
            video = VideoStore.load(video_path)
            
            # Configure ImageMagick
            mpy_conf.change_settings({"IMAGEMAGICK_BINARY": path_of_imagemagick})
            
            # Create a TextClip with specified parameters
            text_clip = TextClip(text, fontsize=font_size, color=color)
            
            # Set position using the provided x, y coordinates and duration
            text_clip = text_clip.set_position((x, y)).set_duration(duration)
            
            # Overlay text on video
            final_video = CompositeVideoClip([video, text_clip])
            
            if return_path:
                final_video.write_videofile(output_path, fps=final_video.fps)
                return {
                    "success": True,
                    "output_path": output_path,
                    "message": "Text overlay added successfully"
                }
            else:
                ref = VideoStore.store(final_video)
                return {
                    "success": True,
                    "output_object": ref,
                    "message": "Text overlay added successfully"
                }

        except Exception as e:
            logger.error(f"Error adding text overlay to video {video_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Error adding text overlay. Make sure ImageMagick is installed and path is correct."
            }

    @mcp.tool(description="Use this tool for adding image watermark/overlay to video, provide image_path, position coordinates (x,y), and output name, if there are multiple steps to be done after adding image overlay then make sure to return object and return path should be false else return path should be true")
    def add_image_overlay(video_path: str, image_path: str, x: int, y: int, duration: float, output_name: str, return_path: bool) -> Dict[str, Any]:
        try:
            # Input validation
            if duration <= 0:
                return {
                    "success": False,
                    "error": "Duration must be positive",
                    "message": "Invalid duration parameter"
                }
            
            output_path = get_output_path(output_name)
            video = VideoStore.load(video_path)
            logo = ImageClip(image_path).set_duration(duration).set_position((x, y))
            final_video = CompositeVideoClip([video, logo])
            
            if return_path:
                final_video.write_videofile(output_path)
                return {
                    "success": True,
                    "output_path": output_path,
                    "message": "Image overlay added successfully"
                }
            else:
                ref = VideoStore.store(final_video)
                return {
                    "success": True,
                    "output_object": ref
                }
        except Exception as e:
            logger.error(f"Error adding image overlay to video {video_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Error adding image overlay"
            }

    @mcp.tool(description="Use this tool for converting video to grayscale/black and white, provide output name like grayscale_video.mp4, if there are multiple steps to be done after converting to grayscale then make sure to return object and return path should be false else return path should be true")
    def grayscale_video(video_path: str, output_name: str, return_path: bool) -> Dict[str, Any]:
        try:
            output_path = get_output_path(output_name)
            video = VideoStore.load(video_path)
            gray_video = video.fx(blackwhite)
            
            if return_path:
                gray_video.write_videofile(output_path)
                return {
                    "success": True,
                    "output_path": output_path,
                    "message": "Video converted to grayscale successfully"
                }
            else:
                ref = VideoStore.store(gray_video)
                return {
                    "success": True,
                    "output_object": ref
                }
        except Exception as e:
            logger.error(f"Error converting video to grayscale {video_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Error converting video to grayscale"
            }

    @mcp.tool(description="Use this tool for extracting frames from video as images, provide start_time, end_time, and fps for extraction, if there are multiple steps to be done after extracting frames then make sure to return object and return path should be false else return path should be true")
    def extract_frames(video_path:str, start_time:float, end_time:float, fps:int, output_folder_name:str, return_path:bool) -> Dict[str,Any]:
        try:
            video = VideoStore.load(video_path)
            subclip = video.subclip(start_time, end_time)
            if return_path:
                os.makedirs(output_folder_name, exist_ok=True)
                for i, frame in enumerate(subclip.iter_frames(fps=fps)):
                    frame_path = os.path.join(output_folder_name, f"frame_{i:04d}.png")
                    imageio.imwrite(frame_path, frame)
                return {
                    "success": True,
                    "output_path": output_folder_name,
                    "message": "Frames extracted successfully"
                }
            else:
                frames = list(subclip.iter_frames(fps=fps))
                return {
                    "success": True,
                    "output_object": frames,
                    "message": "Frames extracted to memory"
                }
        except Exception as e:
            logger.error(f"Error extracting frames from video {video_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Error extracting frames from video"
            }

    @mcp.tool(description="Use this tool for mirroring video horizontally, provide output name like mirrored_video.mp4, if there are multiple steps to be done after mirroring then make sure to return object and return path should be false else return path should be true")
    def mirror_video(video_path:str, output_name:str, return_path:bool) -> Dict[str,Any]:
        try:
            output_path = get_output_path(output_name)
            video = VideoStore.load(video_path)
            mirrored_video = video.fx(mirror_x)
            if return_path:
                mirrored_video.write_videofile(output_path)
                return {
                    "success": True,
                    "output_path": output_path,
                    "message": "Video mirrored successfully"
                }
            else:
                ref = VideoStore.store(mirrored_video)
                return {
                    "success": True,
                    "output_object": ref
                }
        except Exception as e:
            logger.error(f"Error mirroring video {video_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Error mirroring video"
            }

    @mcp.tool(description="Use this tool for splitting video into multiple parts at specific timestamps, provide list of split times in seconds, if there are multiple steps to be done after splitting then make sure to return object and return path should be false else return path should be true")
    def split_video_at_times(video_path:str, split_times:List[float], output_name:str, return_path:bool) -> Dict[str,Any]:
        try:
            output_path = get_output_path(output_name)
            video = VideoStore.load(video_path)
            segments = []
            split_times = [0] + split_times + [video.duration]
            
            for i in range(len(split_times) - 1):
                start = split_times[i]
                end = split_times[i + 1]
                segment = video.subclip(start, end)
                segments.append(segment)
                
            if return_path:
                output_paths = []
                for i, segment in enumerate(segments):
                    segment_path = os.path.join(output_path, f"{output_name}_part_{i+1}.mp4")
                    segment.write_videofile(segment_path)
                    output_paths.append(segment_path)
                return {
                    "success": True,
                    "output_paths": output_paths,
                    "message": "Video split successfully"
                }
            else:
                refs = [VideoStore.store(segment) for segment in segments]
                return {
                    "success": True,
                    "output_objects": refs
                }
        except Exception as e:
            logger.error(f"Error splitting video at times {video_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Error splitting video at times"
            }

    @mcp.tool(description="Use this tool for converting video format with codec and quality control, provide codec, fps, bitrate, if there are multiple steps to be done after converting video format then make sure to return object and return path should be false else return path should be true")
    def convert_video_format(video_path:str, output_name:str, codec:str, fps:Optional[int], bitrate:Optional[str], return_path:bool) -> Dict[str,Any]:
        try:
            output_path = get_output_path(output_name)
            video = VideoStore.load(video_path)
            write_kwargs = {"codec": codec}
            if fps:
                write_kwargs["fps"] = fps
            if bitrate:
                write_kwargs["bitrate"] = bitrate
                
            if return_path:
                video.write_videofile(output_path, **write_kwargs)
                return {
                    "success": True,
                    "output_path": output_path,
                    "message": "Video format converted successfully"
                }
            else:
                ref = VideoStore.store(video)
                return {
                    "success": True,
                    "output_object": ref
                }
        except Exception as e:
            logger.error(f"Error converting video format {video_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Error converting video format"
            }

    @mcp.tool(description="Use this tool for adding video overlay with transparency, provide overlay video, position, and opacity (0-1), if there are multiple steps to be done after adding video overlay then make sure to return object and return path should be false else return path should be true")
    def add_video_overlay(base_video_path:str, overlay_video_path:str, x:int, y:int, opacity:float, output_name:str, return_path:bool,duration:float) -> Dict[str,Any]:
        try:
            output_path = get_output_path(output_name)
            base_video = VideoStore.load(base_video_path)
            overlay_video = VideoStore.load(overlay_video_path)
            
            overlay_positioned = overlay_video.set_position((x, y)).set_opacity(opacity).set_duration(duration)
            final_video = CompositeVideoClip([base_video, overlay_positioned])
            
            if return_path:
                final_video.write_videofile(output_path)
                return {
                    "success": True,
                    "output_path": output_path,
                    "message": "Video overlay added successfully"
                }
            else:
                ref = VideoStore.store(final_video)
                return {
                    "success": True,
                    "output_object": ref
                }
        except Exception as e:
            logger.error(f"Error adding video overlay {base_video_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Error adding video overlay"
            } 
        
    @mcp.tool()
    def merge_videos(
        video_paths: List[str],
        audios_folder: str,
        output_path: str, 
        transition_duration: float = 1.0,
        return_path: bool = True
    ) -> Dict[str, Any]:
        """
        Use this tool for merging multiple videos, provide multiple video paths, and output path like /path/merged_video.mp4 , if there are multiple steps to be done after merging then make sure to return object and return path should be false else return path should be true
        
        Args:
            video_paths: List of video file paths
            audios_folder: Folder containing audio files to choose from
            output_path: Output file path
            transition_duration: Transition duration in seconds
            return_path: Whether to return file path (True) or video object (False)
        
        Returns:
            Dictionary with success status and output path or object reference
        """
        try:
            # Validate input
            if not video_paths or len(video_paths) < 1:
                return {
                    "success": False,
                    "error": "At least one video file is required",
                    "message": "Invalid video paths list"
                }
            
            clips = [VideoFileClip(path) for path in video_paths]
            
            # Shuffle video order randomly
            #random.shuffle(clips)
            
            # Define available transition effects
            transitions = [
                ("crossfade", None),
                ("slide", "left"),
                ("slide", "right"),
                ("slide", "top"),
                ("slide", "bottom")
            ]
            
            # Apply transition effects between each video pair
            clips_with_transitions = []
            video_start = 0
            for i in range(len(clips)):
                if i == 0:
                    current_clip = clips[i].fx(vfx.fadein, transition_duration)
                else:
                    trans_type, side = random.choice(transitions)

                    if trans_type == "crossfade":
                        current_clip = clips[i].fx(transfx.crossfadein, transition_duration)
                    elif trans_type == "slide":
                        current_clip = clips[i].fx(transfx.slide_in, duration=transition_duration, side=side)

                    if i == len(clips) - 1:
                        current_clip = current_clip.fx(vfx.fadeout, transition_duration)
    
                current_clip = current_clip.set_start(video_start)
                video_start += current_clip.duration - transition_duration
                clips_with_transitions.append(current_clip)

            final_clip = CompositeVideoClip(clips_with_transitions)

            if audios_folder and os.path.exists(audios_folder):
                try:
                    audio_extensions = ['.mp3', '.wav', '.aac', '.m4a', '.ogg']
                    
                    # 获取文件夹中的所有音频文件
                    audio_files = []
                    if os.path.exists(audios_folder) and os.path.isdir(audios_folder):
                        for file in os.listdir(audios_folder):
                            if any(file.lower().endswith(ext) for ext in audio_extensions):
                                audio_files.append(os.path.join(audios_folder, file))
    
                    if audio_files:
                        # 随机选择一个音频文件
                        random_audio_path = random.choice(audio_files)
                        logger.info(f"Selected random audio: {random_audio_path}")
                        
                        audio_clip = AudioFileClip(random_audio_path)
                        if audio_clip.duration < final_clip.duration:
                            # Loop audio to match video duration
                            audio_clip = audio_clip.fx(afx.audio_loop, duration=final_clip.duration)
                        elif audio_clip.duration > final_clip.duration:
                            # Trim audio to video duration
                            audio_clip = audio_clip.subclip(0, final_clip.duration)
        
                        fadeout_duration = 2.0  # 淡出持续时间（秒）
                        audio_clip = audio_clip.fx(afx.audio_fadeout, duration=fadeout_duration)

                        final_clip = final_clip.set_audio(audio_clip)
                    else:
                        logger.warning(f"No audio files found in directory: {audios_folder}")
                except Exception as audio_error:
                    logger.warning(f"Could not add audio: {audio_error}")

            # Decide return method based on return_path parameter
            if return_path:
                final_clip.write_videofile(
                    output_path, 
                    codec='libx264', 
                    audio_codec='aac'
                )
                
                # Close all clips to release resources
                for clip in clips_with_transitions:
                    clip.close()
                final_clip.close()
                
                return {
                    "success": True,
                    "output_path": output_path,
                    "message": f"Video concatenation successful, processed {len(video_paths)} videos"
                }
            else:
                ref = VideoStore.store(final_clip)
                
                return {
                    "success": True,
                    "output_object": ref,
                    "message": f"Video concatenation successful, processed {len(video_paths)} videos"
                }
                
        except Exception as e:
            logger.error(f"Error during video concatenation: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Video concatenation failed"
            }