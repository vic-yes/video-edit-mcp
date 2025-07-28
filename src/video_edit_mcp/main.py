from mcp.server.fastmcp import FastMCP
import logging
from .video_operations import register_video_tools
from .audio_operations import register_audio_tools
from .download_utils import register_download_and_utility_tools
from .util_tools import register_util_tools
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP()

# Register all tools from different modules
register_video_tools(mcp)
register_audio_tools(mcp)
register_download_and_utility_tools(mcp)
register_util_tools(mcp)

def main():
    """Entry point for the MCP server"""
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()



