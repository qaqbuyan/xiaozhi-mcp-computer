import logging
from mcp.server.fastmcp import FastMCP
from utils.speaker.speaker import get_speaker

logger = logging.getLogger('设置音量')

def set_volume(mcp: FastMCP):
    @mcp.tool()
    def set_volume(level: float = 1.0) -> str:
        """
        设置电脑音量
        Args:
            level: 音量级别（0.0到1.0之间）
        """
        logger.info(f"开始设置音量...")
        if not isinstance(level, (int, float)):
            msg = f"传入的音量级别类型错误，期望 float 或 int，实际为 {type(level)}"
            logger.error(msg)
            return msg
        logger.info(f"设置音量为: {level * 100:.0f}%")
        level = max(0.0, min(1.0, level))
        speaker = get_speaker()
        speaker.SetMasterVolumeLevelScalar(level, None)
        msg = f"已将音量设置为: {level * 100:.0f}%"
        logger.info(msg)
        return msg