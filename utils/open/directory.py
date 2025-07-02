import os
import logging
import platform
import subprocess
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('打开目录')

def open_directory(mcp: FastMCP) -> dict:
    @mcp.tool()
    def open_directory(directory_path: str) -> dict:
        """用于打开指定目录。当需要打开桌面或者菜单目录时，立刻使用该工具。"""
        logger.info(f"尝试打开目录: {directory_path}")
        # 确保目录存在且是有效路径
        if not directory_path or not isinstance(directory_path, str):
            msg = f"错误：目录路径不能为空且必须是字符串"
            logger.error(msg)
            return {"success": False, "result": msg}
        try:
            directory_path = os.path.abspath(directory_path)
            if not os.path.isdir(directory_path):
                msg = f"错误：指定的路径不是有效的目录 - {directory_path}"
                logger.error(msg)
                return {"success": False, "result": msg}
            # 根据操作系统选择不同的打开方式
            system = platform.system()
            if system == 'Windows':
                # Windows 系统
                os.startfile(directory_path)
            elif system == 'Darwin':  # macOS
                # macOS 系统
                subprocess.run(['open', directory_path], check=True)
            elif system == 'Linux':
                # Linux 系统，尝试几种常见的文件管理器
                managers = ['xdg-open', 'nautilus', 'dolphin', 'thunar', 'caja', 'pcmanfm']
                opened = False
                for manager in managers:
                    try:
                        subprocess.run([manager, directory_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        opened = True
                        break
                    except (subprocess.SubprocessError, FileNotFoundError):
                        continue
                if not opened:
                    msg = f"无法找到合适的文件管理器来打开目录"
                    logger.error(msg)
                    return {"success": False, "result": msg}
            else:
                msg = f"不支持的操作系统: {system}"
                logger.error(msg)
                return {"success": False, "result": msg}
            msg = f"成功打开目录: {directory_path}"
            logger.info(msg)
            return {"success": True, "result": msg}
        except Exception as e:
            msg = f"打开目录时出错: {e}"
            logger.error(msg)
            return {"success": False, "result": msg}