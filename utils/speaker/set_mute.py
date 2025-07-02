import logging
from mcp.server.fastmcp import FastMCP
from utils.speaker.speaker import get_speaker

logger = logging.getLogger('切换静音')

def toggle_mute(mcp: FastMCP):
    @mcp.tool()
    def toggle_mute() -> str:
        """切换电脑扬声器静音状态。如果当前状态未知，您必须先调用 `get_mute` 工具，然后再调用此工具。"""
        logger.info("切换扬声器静音状态...")
        speaker = get_speaker()
        is_muted = speaker.GetMute()
        speaker.SetMute(not is_muted, None)
        status = "静音" if not is_muted else "取消静音"
        logger.info(f"已{status}扬声器")
        return f"已{status}扬声器"