# Video Edit MCP Server 🎬

A powerful **Model Context Protocol (MCP)** server designed for advanced video and audio editing operations. This server enables MCP clients—such as Claude Desktop, Cursor, and others—to perform comprehensive multimedia editing tasks through a standardized and unified interface.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![MCP](https://img.shields.io/badge/MCP-Compatible-purple.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)


https://github.com/user-attachments/assets/134b8b82-80b1-4678-8930-ab53121b121f





## ✨ Key Features

### 🎥 Video Operations
- **Basic Editing**: Trim, merge, resize, crop, rotate videos
- **Effects**: Speed control, fade in/out, grayscale, mirror
- **Overlays**: Add text, images, or video overlays with transparency
- **Format Conversion**: Convert between formats with codec control
- **Frame Operations**: Extract frames, create videos from images

### 🎵 Audio Operations  
- **Audio Processing**: Extract, trim, loop, concatenate audio
- **Volume Control**: Adjust levels, fade in/out effects
- **Audio Mixing**: Mix multiple tracks together
- **Integration**: Add audio to videos, replace soundtracks

### 📥 Download & Utilities
- **Video Download**: Download from YouTube and other platforms
- **File Management**: Directory operations, file listing
- **Path Suggestions**: Get recommended download locations

### 🧹 Memory & Cleanup
- **Smart Memory**: Chain operations without saving intermediate files
- **Resource Management**: Clear memory, check stored objects
- **Efficient Processing**: Keep objects in memory for complex workflows

### 🔗 Operation Chaining
Seamlessly chain multiple operations together without creating intermediate files. Process your video through multiple steps (trim → add audio → apply effects → add text) while keeping everything in memory for optimal performance.

## 📋 Requirements

- **Python 3.10 or higher**
- **moviepy==1.0.3**
- **yt-dlp>=2023.1.6**
- **mcp>=1.12.2**
- **typing-extensions>=4.0.0**

## ⚙️ Installation & Setup



### For Claude Desktop / Cursor MCP Integration

**Ensure that `uv` is installed.**  
If not, install it using the following PowerShell command:

```powershell
powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
```

Add this configuration to your MCP configuration file:

```json
{
  "mcpServers": {
    "video_editing": {
      "command": "uvx",
      "args": [
        "--python",
        "3.11",
        "video-edit-mcp"
      ]
    }
  }
}
```

**Configuration file locations:**
- **Claude Desktop (Windows)**: `%APPDATA%/Claude/claude_desktop_config.json`
- **Claude Desktop (macOS)**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Cursor**: `.cursor/mcp.json` in your project root

### Manual Installation

```bash
git clone https://github.com/Aditya2755/video-edit-mcp.git
cd video-edit-mcp
pip install -r requirements.txt
pip install -e .
```

## 🏗️ Project Structure

```
video_edit_mcp/
├── src/
│   └── video_edit_mcp/
│       ├── __init__.py
│       ├── main.py                 # MCP server implementation  
│       ├── video_operations.py     # Video editing tools
│       ├── audio_operations.py     # Audio processing tools
│       ├── download_utils.py       # Download functionality
│       ├── util_tools.py          # Memory & utility tools
│       ├── utils.py               # Utility functions
│     
├── pyproject.toml                 # Project configuration
├── requirements.txt               # Dependencies
├── uv.lock                        # Lock file
├── LICENSE                        # MIT License
├── MANIFEST.in                    # Manifest file
└── README.md
```

## 🎯 Example Usage

```python
# Chain operations without intermediate files
video_info = get_video_info("input.mp4")
trimmed = trim_video("input.mp4", 10, 60, return_path=False)  # Keep in memory
with_audio = add_audio(trimmed, "background.mp3", return_path=False)  
final = add_text_overlay(with_audio, "Hello World", x=100, y=50, return_path=True)
```

## 🚀 Future Enhancements & Contributions

We welcome contributions in these exciting areas:

### 🤖 AI-Powered Features
- **Speech-to-Text (STT)**: Automatic subtitle generation and transcription
- **Text-to-Speech (TTS)**: AI voice synthesis for narration
- **Audio Enhancement**: AI-based noise reduction and audio quality improvement
- **Smart Timestamps**: Automatic scene detection and chapter generation
- **Face Tracking**: Advanced face detection and tracking for automatic editing
- **Object Recognition**: Track and edit based on detected objects
- **Content Analysis**: AI-powered content categorization and tagging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Made with ❤️ for the AI and multimedia editing community**

[⭐ Star this project](https://github.com/Aditya2755/video-edit-mcp) | [🤝 Contribute](https://github.com/Aditya2755/video-edit-mcp/contribute) | [📖 Documentation](https://github.com/Aditya2755/video-edit-mcp#readme)

</div>