import logging
from mcp.server.fastmcp import FastMCP
from utils.speaker.speaker import get_speaker

logger = logging.getLogger('获取扬声器状态')

def get_mute(mcp: FastMCP):
    @mcp.tool()
    def get_mute() -> str:
        """获取扬声器静音状态"""
        logger.info("开始获取扬声器静音状态...")
        speaker = get_speaker()
        is_muted = speaker.GetMute()
        if is_muted:
            msg = "扬声器当前已处于静音状态"
            logger.info(msg)
            return msg
        else:
            msg = "扬声器不为静音状态"
            logger.info(msg)
            return msg