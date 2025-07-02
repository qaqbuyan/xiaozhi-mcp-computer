import os
import sys
import logging
import subprocess
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('桌面目录')

def open_desktop(mcp: FastMCP):
    @mcp.tool()
    def open_desktop() -> str:
        """打开桌面目录, 当说打开桌面时，立刻使用该工具。"""
        logger.info("打开桌面目录...")
        try:
            if sys.platform == 'win32':
                # Windows 系统获取桌面路径
                import ctypes
                CSIDL_DESKTOP = 0
                buf = ctypes.create_unicode_buffer(1024)
                ctypes.windll.shell32.SHGetSpecialFolderPathW(None, buf, CSIDL_DESKTOP, False)
                desktop_path = buf.value
            else:
                # macOS 和 Linux 系统获取桌面路径
                desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
            # 直接打开桌面目录
            if sys.platform == 'win32':
                os.startfile(desktop_path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', desktop_path], check=True)
            elif sys.platform == 'linux':
                subprocess.run(['xdg-open', desktop_path], check=True)
            msg = f"已打开桌面目录: {desktop_path}"
            logger.info(msg)
            return {"success": True, "result": msg}
        except Exception as e:
            msg = f"打开桌面目录失败: {str(e)}"
            logger.error(msg)
            return {"success": False, "result": msg}