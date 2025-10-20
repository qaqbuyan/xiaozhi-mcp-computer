import logging
from mcp.server.fastmcp import FastMCP
from utils.speaker.get_all_audio import get_all_audio_sessions

logger = logging.getLogger('获取音频会话')

def get_audio_sessions(mcp: FastMCP):
    @mcp.tool()
    def get_audio_sessions() -> dict:
        """获取所有正在运行的音频会话（应用程序）
        
        Returns:
            dict: 包含success和result两个键的字典
                success: bool - 获取是否成功
                result: list/dict - 如果成功，返回音频会话列表；如果失败，返回错误信息
        """
        sessions = get_all_audio_sessions()
        return {"success": True, "result": sessions}