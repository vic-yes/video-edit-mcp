import cv2
import numpy as np
import os
import logging
import exifread
from .editorpy.editor import *
from moviepy.editor import *
from moviepy.video.fx import *
from PIL import Image
from .utils import get_output_path, VideoStore, AudioStore
from typing import Dict, Any, Optional, List, Tuple
from moviepy.editor import ImageClip, ImageSequenceClip

logger = logging.getLogger(__name__)

def register_image_tools(mcp):
    """Register all image processing tools with the MCP server"""

    @mcp.tool()
    def get_image_info(image_path: str) -> Dict[str, Any]:
        """Get comprehensive information about an image file including dimensions, format, EXIF data, and file information."""
        try:
            # Load image file
            with Image.open(image_path) as img:
                # Basic image information
                info = {
                    "file_path": image_path,
                    "filename": os.path.basename(image_path),
                    "format": img.format,
                    "mode": img.mode,
                    "width": img.width,
                    "height": img.height,
                    "size": img.size,  # (width, height)
                    "aspect_ratio": round(img.width / img.height, 2) if img.height > 0 else None,
                    "is_animated": getattr(img, "is_animated", False),
                    "n_frames": getattr(img, "n_frames", 1),
                }
                
                # Get EXIF data if available - 修复编码问题
                exif_data = {}
                try:
                    with open(image_path, 'rb') as f:
                        tags = exifread.process_file(f, details=False)
                        for tag, value in tags.items():
                            if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
                                # 安全地处理可能包含二进制数据的EXIF值
                                try:
                                    # 尝试直接转换为字符串
                                    exif_data[tag] = str(value)
                                except UnicodeDecodeError:
                                    # 如果是二进制数据，进行base64编码
                                    try:
                                        exif_data[tag] = f"base64:{base64.b64encode(value).decode('utf-8')}"
                                    except:
                                        # 如果还是失败，跳过这个标签
                                        continue
                    
                    if exif_data:
                        info["has_exif"] = True
                        info["exif_tags_count"] = len(exif_data)
                        
                        # Extract common EXIF metadata with safe handling
                        common_exif = {}
                        exif_mapping = {
                            'EXIF DateTimeOriginal': 'date_time_original',
                            'Image DateTime': 'date_time',
                            'Image Make': 'camera_make',
                            'Image Model': 'camera_model',
                            'EXIF ExposureTime': 'exposure_time',
                            'EXIF FNumber': 'f_number',
                            'EXIF FocalLength': 'focal_length',
                            'EXIF ISOSpeedRatings': 'iso',
                            'EXIF Flash': 'flash',
                        }
                        
                        for exif_tag, friendly_name in exif_mapping.items():
                            if exif_tag in exif_data:
                                try:
                                    common_exif[friendly_name] = str(exif_data[exif_tag])
                                except:
                                    pass
                        
                        # Check for GPS data
                        has_gps = any(tag.startswith('GPS') for tag in exif_data.keys())
                        common_exif['has_gps'] = has_gps
                        
                        info["common_exif"] = common_exif
                    else:
                        info["has_exif"] = False
                        
                except Exception as e:
                    info["has_exif"] = False
                    info["exif_error"] = str(e)
                
                # Get ICC profile if available
                if hasattr(img, 'icc_profile') and img.icc_profile:
                    info["has_icc_profile"] = True
                    info["icc_profile_size"] = len(img.icc_profile)
                else:
                    info["has_icc_profile"] = False
                
                # Get image metadata safely
                if hasattr(img, 'info') and img.info:
                    safe_info = {}
                    for key, value in img.info.items():
                        try:
                            # 确保所有值都可以序列化为JSON
                            if isinstance(value, (str, int, float, bool, type(None))):
                                safe_info[key] = value
                            else:
                                safe_info[key] = str(value)
                        except:
                            safe_info[key] = "unserializable_value"
                    info["image_info"] = safe_info
                
            # File size information
            try:
                file_size = os.path.getsize(image_path)
                info["file_size_bytes"] = file_size
                info["file_size_kb"] = round(file_size / 1024, 2)
                info["file_size_mb"] = round(file_size / (1024 * 1024), 2)
            except OSError:
                info["file_size_bytes"] = None
                info["file_size_kb"] = None
                info["file_size_mb"] = None
            
            # Calculate compression ratio estimate
            if info.get("file_size_bytes") and img.width and img.height:
                # Estimate uncompressed size (rough approximation)
                bytes_per_pixel_mapping = {
                    'RGB': 3,
                    'RGBA': 4,
                    'L': 1,
                    'LA': 2,
                    'CMYK': 4,
                    'YCbCr': 3
                }
                
                bytes_per_pixel = bytes_per_pixel_mapping.get(img.mode, 3)
                uncompressed_size = img.width * img.height * bytes_per_pixel
                
                if uncompressed_size > 0:
                    info["compression_ratio"] = round(info["file_size_bytes"] / uncompressed_size, 4)
                    info["estimated_bpp"] = round((info["file_size_bytes"] * 8) / (img.width * img.height), 2)
            
            return {
                "success": True,
                "image_info": info
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "image_path": image_path
            }

    @mcp.tool(description="Use this tool for resizing the image")
    def resize_image(image_path: str, size: Tuple[int, int], output_path: str) -> Dict[str, Any]:
        try:
            # Input validation
            if not size or len(size) != 2 or size[0] <= 0 or size[1] <= 0:
                return {
                    "success": False,
                    "error": "Size must be a tuple of two positive integers (width, height)",
                    "message": "Invalid size parameters"
                }
            
            # Load the image
            image = cv2.imread(image_path)
            if image is None:
                return {
                    "success": False,
                    "error": f"Failed to load image: {image_path}",
                    "message": "Invalid image file"
                }
            
            target_width, target_height = size
            original_height, original_width = image.shape[:2]
            
            # Calculate scaling ratio
            scale = min(target_width / original_width, target_height / original_height)
            
            # Calculate new dimensions
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)
            
            # Resize image
            resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
            
            # Create black background
            result = np.zeros((target_height, target_width, 3), dtype=np.uint8)
            
            # Calculate position to center the image
            x_offset = (target_width - new_width) // 2
            y_offset = (target_height - new_height) // 2
            
            # Place resized image on black background
            result[y_offset:y_offset+new_height, x_offset:x_offset+new_width] = resized
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save the result
            cv2.imwrite(output_path, result)

            return {
                "success": True,
                "output_path": output_path,
                "message": "Image resized successfully"
            }
        except Exception as e:
            logger.error(f"Error resizing image {image_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Error resizing image"
            }

    @mcp.tool()
    def image_to_video(
        image_path: str,
        output_path: str,
        duration: float = 5.0,
        fps: int = 24,
        return_path: bool = True,
        # 滤镜特效参数
        effect: Optional[str] = None,
        # 缩放移动参数
        zoom_factor: Optional[float] = None,
        zoom_direction: str = "center",  # center, top, bottom, left, right
        pan_start: Optional[Tuple[int, int]] = None,
        pan_end: Optional[Tuple[int, int]] = None,
        # 旋转参数
        rotation_angle: Optional[float] = None,
        # 颜色调整
        brightness: Optional[float] = None,
        contrast: Optional[float] = None,
        saturation: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Convert an image to video with various effects and transformations.
        
        Args:
            image_path: Path to the input image
            output_path: Path to the output video filename
            duration: Duration of the output video in seconds
            fps: Frames per second for the output video
            return_path: Whether to return file path or object reference
            effect: Special effect to apply ('blackwhite', 'sepia', 'blur', 'edge_detect', 'invert', 'sharpen', 'emboss', 'sketch')
            zoom_factor: Zoom factor (e.g., 1.5 for 1.5x zoom)
            zoom_direction: Direction for zoom effect ('center', 'top', 'left', 'right', 'bottom')
            pan_start: Starting position for pan effect (x, y)
            pan_end: Ending position for pan effect (x, y)
            rotation_angle: Rotation angle in degrees
            brightness: Brightness adjustment (-1.0 to 1.0)
            contrast: Contrast adjustment (0.0 to 2.0+)
            saturation: Saturation adjustment (0.0 to 2.0+)
        
        Returns:
            Dictionary with success status and output path or object reference
        """
        try:
            # Input validation
            if duration <= 0:
                return {
                    "success": False,
                    "error": "Duration must be positive",
                    "message": "Invalid duration parameter"
                }
            
            if fps <= 0:
                return {
                    "success": False,
                    "error": "FPS must be positive",
                    "message": "Invalid FPS parameter"
                }
            
            # Load the image
            image_clip = ImageClip(image_path).set_duration(duration)
            
            # Apply color adjustments
            if brightness is not None:
                # 亮度调整 (-1.0 到 1.0)
                brightness_factor = 1.0 + max(-1.0, min(1.0, brightness))
                image_clip = image_clip.fx(vfx.colorx, factor=brightness_factor)
            
            if contrast is not None:
                # 对比度调整 (0.0 到 2.0+)
                contrast_factor = max(0.0, contrast)
                image_clip = image_clip.fx(ifx.contrast, factor=contrast_factor)
            
            if saturation is not None:
                # 饱和度调整 (0.0 到 2.0+)
                saturation_factor = max(0.0, saturation)
                image_clip = image_clip.fx(ifx.saturation, factor=saturation_factor)
            
            # Apply special effects
            if effect:
                effect = effect.lower()
                if effect == 'blackwhite':
                    image_clip = image_clip.fx(vfx.blackwhite)
                
                elif effect == 'sepia':
                    image_clip = image_clip.fl_image(ifx.sepia)
                
                elif effect == 'blur':
                    # 模糊效果
                    image_clip = image_clip.fl_image(ifx.blur)
                
                elif effect == 'edge_detect':
                    # 边缘检测效果
                    image_clip = image_clip.fl_image(ifx.edge_detect)
                
                elif effect == 'invert':
                    # 颜色反转效果
                    image_clip = image_clip.fx(vfx.invert_colors)

                elif effect == 'sharpen':
                    # 锐化效果
                    image_clip = image_clip.fl_image(ifx.sharpen)
                
                elif effect == 'emboss':
                    # 浮雕效果
                    image_clip = image_clip.fl_image(ifx.emboss)
                
                elif effect == 'sketch':
                    # 素描效果
                    image_clip = image_clip.fl_image(ifx.sketch)
            
            # Apply zoom and pan effects using a simpler approach
            if zoom_factor is not None or pan_start is not None or pan_end is not None:
                final_clip = apply_zoom_pan_effect_simple(image_clip, zoom_factor, zoom_direction, pan_start, pan_end, duration)
            else:
                final_clip = image_clip
            
            # Apply rotation
            if rotation_angle is not None:
                final_clip = final_clip.fx(vfx.rotate, angle=rotation_angle)
            
            # Set FPS
            final_clip = final_clip.set_fps(fps)
            
            # Output handling
            if return_path:
                final_clip.write_videofile(output_path, fps=fps)
                result = {
                    "success": True,
                    "output_path": output_path,
                    "message": "Image converted to video successfully"
                }
            else:
                ref = VideoStore.store(final_clip)
                result = {
                    "success": True,
                    "output_object": ref,
                    "message": "Image converted to video successfully"
                }
            
            # Clean up
            final_clip.close()
            
            return result
            
        except Exception as e:
            logger.error(f"Error converting image {image_path} to video: {e}")
            # Ensure resources are cleaned up
            try:
                if 'final_clip' in locals():
                    final_clip.close()
            except:
                pass
            
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Error converting image to video"
            }
    
    def apply_zoom_pan_effect_simple(clip, zoom_factor, zoom_direction, pan_start, pan_end, duration):
        """
        Apply zoom and pan effects using a proper approach with resize and crop.
        """

        # If no zoom or pan specified, return original clip
        if zoom_factor is None and pan_start is None and pan_end is None:
            return clip
        
        # Default values
        zoom_factor = zoom_factor or 1.0
        zoom_direction = zoom_direction or "center"
        
        # Store original dimensions
        orig_w, orig_h = clip.size
        
        # Create a function that applies transformations at each time point
        def transform(get_frame, t):
            # Calculate progress (0 to 1)
            progress = min(1.0, max(0.0, t / duration))
            
            # Calculate current zoom factor
            current_zoom = 1.0 + (zoom_factor - 1.0) * progress
            
            # Calculate current pan position
            current_x, current_y = 0, 0
            is_manual_pan = False
            
            if pan_start and pan_end:
                # Manual panning between specified points
                is_manual_pan = True
                start_x, start_y = pan_start
                end_x, end_y = pan_end
                current_x = start_x + (end_x - start_x) * progress
                current_y = start_y + (end_y - start_y) * progress
            elif zoom_direction != "center":
                # Automatic pan based on zoom direction
                zoom_effect = (current_zoom - 1.0) * 0.5
                
                if zoom_direction == "top":
                    current_y = -orig_h * zoom_effect
                elif zoom_direction == "bottom":
                    current_y = orig_h * zoom_effect
                elif zoom_direction == "left":
                    current_x = -orig_w * zoom_effect
                elif zoom_direction == "right":
                    current_x = orig_w * zoom_effect
            
            # Get the original frame
            frame = get_frame(t)
            
            # Apply zoom first
            if current_zoom != 1.0:
                from PIL import Image
                pil_image = Image.fromarray(frame)
                
                # Calculate new dimensions
                new_width = int(orig_w * current_zoom)
                new_height = int(orig_h * current_zoom)
                
                # Resize with high quality interpolation
                resized = pil_image.resize((new_width, new_height), Image.LANCZOS)
                frame = np.array(resized)
            
            # Apply pan by cropping
            h, w, _ = frame.shape
            
            if is_manual_pan:
                # MANUAL PANNING: Allow going beyond original image boundaries
                # Calculate crop coordinates based on pan position
                crop_x = int(current_x)
                crop_y = int(current_y)
                
                # Calculate crop boundaries
                x1 = crop_x
                y1 = crop_y
                x2 = x1 + orig_w
                y2 = y1 + orig_h
                
                # Create a blank canvas of the original size
                result_frame = np.zeros((orig_h, orig_w, 3), dtype=np.uint8)
                
                # Calculate the visible portion of the zoomed frame
                visible_x1 = max(0, -x1)
                visible_y1 = max(0, -y1)
                visible_x2 = min(orig_w, w - x1)
                visible_y2 = min(orig_h, h - y1)
                
                # Calculate corresponding source coordinates
                source_x1 = max(0, x1)
                source_y1 = max(0, y1)
                source_x2 = min(w, x2)
                source_y2 = min(h, y2)
                
                # Copy the visible portion to the result frame
                if source_x2 > source_x1 and source_y2 > source_y1:
                    visible_width = source_x2 - source_x1
                    visible_height = source_y2 - source_y1
                    
                    result_frame[visible_y1:visible_y1+visible_height, 
                               visible_x1:visible_x1+visible_width] = \
                        frame[source_y1:source_y2, source_x1:source_x2]
                
                frame = result_frame
                
            else:
                # ZOOM-BASED PANNING: Apply boundary checks
                crop_x = max(0, (w - orig_w) // 2)
                crop_y = max(0, (h - orig_h) // 2)
                
                # Add zoom direction offset
                crop_x += int(current_x)
                crop_y += int(current_y)
                
                # Ensure crop coordinates are within bounds for zoom
                crop_x = max(0, min(w - orig_w, crop_x))
                crop_y = max(0, min(h - orig_h, crop_y))
                
                # Calculate crop boundaries
                x1 = crop_x
                y1 = crop_y
                x2 = x1 + orig_w
                y2 = y1 + orig_h
                
                # Perform the crop
                if x2 > x1 and y2 > y1:
                    frame = frame[y1:y2, x1:x2]
                
                # If the cropped frame is smaller than original, pad it
                crop_h, crop_w, _ = frame.shape
                if crop_h < orig_h or crop_w < orig_w:
                    padded_frame = np.zeros((orig_h, orig_w, 3), dtype=np.uint8)
                    y_offset = (orig_h - crop_h) // 2
                    x_offset = (orig_w - crop_w) // 2
                    padded_frame[y_offset:y_offset+crop_h, x_offset:x_offset+crop_w] = frame
                    frame = padded_frame
            
            return frame
        
        # Apply the transformation
        return clip.fl(transform, apply_to=['mask', 'audio'] if clip.audio else None)

    @mcp.tool(description="Use this tool for creating video from image sequence, provide folder path with images, fps, and output name, if there are multiple steps to be done after creating video from images then make sure to return object and return path should be false else return path should be true")
    def images_to_video(images_folder_path:str, fps:int, output_name:str, return_path:bool) -> Dict[str,Any]:
        try:
            output_path = get_output_path(output_name)
            clip = ImageSequenceClip(images_folder_path, fps=fps)
            if return_path:
                clip.write_videofile(output_path)
                return {
                    "success": True,
                    "output_path": output_path,
                    "message": "Video created from images successfully"
                }
            else:
                ref = VideoStore.store(clip)
                return {
                    "success": True,
                    "output_object": ref
                }
        except Exception as e:
            logger.error(f"Error creating video from images {images_folder_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Error creating video from images"
            }