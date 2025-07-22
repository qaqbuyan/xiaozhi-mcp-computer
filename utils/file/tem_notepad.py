import os
import logging
import platform
import tempfile
import subprocess
from mcp.server.fastmcp import FastMCP
from utils.application.check_activity import get_window_active

logger = logging.getLogger('临时写入')

def temporary_write_to_notepad(mcp: FastMCP):
    @mcp.tool()
    def temporary_write_to_notepad(content: str) -> dict:
        """用于使用记事本打开文件并写入指定内容。
        当需要临时存储内容，或者将内容保存到文件，或者通过记事本展示给用户时，立刻使用此工具。
        Args:
            content (str): 要写入记事本文件的具体内容。
        Returns:
            dict: 包含操作结果的字典，格式如下：
                {
                    "success": bool,
                        # 操作是否成功的标志
                    "result": str,
                        # 操作结果的描述信息
                    "state": bool
                        # 窗口是否为活动状态，仅在成功打开时可能包含
                        # 如果为False，则表示窗口未激活或未处于前台
                }
        """
        logger.info(f"收到请求，准备写入内容到记事本: {content}")
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
        file_path = temp_file.name
        temp_file.close()
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            logger.info(f"成功写入内容到文件: {file_path}")
        except Exception as e:
            msg = f"写入文件时出错: {e}"
            logger.error(msg)
            return {"success": False, "result": msg}
        try:
            system = platform.system()
            if system == 'Windows':
                subprocess.Popen(['notepad.exe', file_path])
                msg = f"已创建文件并启动记事本: {file_path}"
                logger.info(msg)
                result = {"success": True, "result": msg}
                file_name = os.path.basename(file_path)
                if not get_window_active(file_name):
                    result["state"] = False
                return result
            elif system == 'Darwin':
                subprocess.run(['open', '-a', 'TextEdit', file_path], check=True)
                msg = f"已打开文件:{os.path.basename(file_path)}"
                result = {"success": True, "result": msg}
                file_name = os.path.basename(file_path)
                if not get_window_active(file_name):
                    result["state"] = False
                return result
            elif system == 'Linux':
                editors = ['gedit', 'kate', 'mousepad', 'leafpad', 'nano', 'vim']
                for editor in editors:
                    try:
                        subprocess.Popen([editor, file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        msg = f"已打开文件:{os.path.basename(file_path)}"
                        result = {"success": True, "result": msg}
                        # 检查编辑器窗口是否为活动窗口
                        file_name = os.path.basename(file_path)
                        if not get_window_active(file_name):
                            result["state"] = False
                        return result
                    except (subprocess.SubprocessError, FileNotFoundError):
                        continue
                msg = "无法找到合适的文本编辑器"
                return {"success": False, "result": msg}
            else:
                msg = f"不支持的操作系统: {system}"
                return {"success": False, "result": msg}
        except Exception as e:
            msg = f"打开记事本时出错: {e}"
            logger.error(msg)
            return {"success": False, "result": msg}