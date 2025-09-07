from mcp.server.fastmcp import FastMCP
import logging
from .image_operations import register_image_tools
from .video_operations import register_video_tools
from .audio_operations import register_audio_tools
from .download_utils import register_download_and_utility_tools
from .util_tools import register_util_tools
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("VideoEdit", host="0.0.0.0", port=9000)

# Register all tools from different modules
register_image_tools(mcp)
register_video_tools(mcp)
register_audio_tools(mcp)
#register_download_and_utility_tools(mcp)
register_util_tools(mcp)

def main():
    """Entry point for the MCP server"""
    mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main()



