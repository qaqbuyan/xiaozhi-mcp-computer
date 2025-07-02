import logging
from mcp.server.fastmcp import FastMCP
from pycaw.pycaw import AudioUtilities

logger = logging.getLogger('获取音频会话')

def get_audio_sessions(mcp: FastMCP):
    @mcp.tool()
    def get_audio_sessions() -> dict:
        """获取所有正在运行的音频会话（应用程序）"""
        try:
            logger.info("开始获取所有正在运行的音频会话...")
            sessions = []
            sessions_manager = AudioUtilities.GetAllSessions()
            for session in sessions_manager:
                if session.Process:
                    app_name = session.Process.name()
                    # 去除 .exe 扩展名
                    if app_name.lower().endswith('.exe'):
                        app_name = app_name[:-4]
                    volume = session.SimpleAudioVolume.GetMasterVolume()
                    sessions.append({
                        "app_name": app_name,
                        "volume": volume
                    })
            if not sessions:
                error_msg = "未找到任何正在运行的音频会话"
                logger.warning(error_msg)
                return {"success": False, "result": error_msg}
            logger.info("获取音频会话完成")
            logger.info(f"成功获取到 {len(sessions)} 个音频会话")
            msg = f"获取到的音频会话: {sessions}"
            logger.info(msg)
            return {"success": True, "result": sessions}
        except Exception as e:
            error_msg = f"获取音频会话时出错: {e}"
            logger.error(error_msg)
            return {"success": False, "result": error_msg}