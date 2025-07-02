import logging
from mcp.server.fastmcp import FastMCP
from utils.speaker.speaker import get_speaker

logger = logging.getLogger('获取音量')

def get_volume(mcp: FastMCP):
    @mcp.tool()
    def get_volume() -> float:
        """获取电脑当前音量（0.0到1.0之间）"""
        logger.info("获取当前音量...")
        speaker = get_speaker()
        volume = speaker.GetMasterVolumeLevelScalar()
        rounded_volume = round(volume, 2)
        logger.info(f"当前音量为：{rounded_volume}")
        return rounded_volume