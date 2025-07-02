import logging
from mcp.server.fastmcp import FastMCP
from pycaw.pycaw import AudioUtilities

logger = logging.getLogger('设置应用音量')

def set_app_volume(mcp: FastMCP):
    @mcp.tool()
    def set_app_volume(app_name: str, level: float) -> str:
        """
        设置指定应用程序的音量
        Args:
            app_name: 应用程序的进程名，例如 "chrome"，无需传入 .exe 扩展名，不区分大小写
            level: 音量级别（0.0到1.0之间）
        """
        # 自动添加 .exe 扩展名
        if not app_name.lower().endswith('.exe'):
            app_name += '.exe'
        logger.info(f"尝试将 {app_name} 的音量设置为 {level * 100:.0f}%")
        level = max(0.0, min(1.0, level))
        try:
            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                if session.Process and session.Process.name().lower() == app_name.lower():
                    volume = session.SimpleAudioVolume
                    volume.SetMasterVolume(level, None)
                    msg = f"已将 {app_name} 的音量设置为 {level * 100:.0f}%"
                    logger.info(msg)
                    return msg
            msg = f"未找到名为 {app_name} 的正在运行的应用程序"
            logger.error(msg)
            return msg
        except Exception as e:
            msg = f"设置 {app_name} 音量时出错: {e}"
            logger.error(msg)
            return msg