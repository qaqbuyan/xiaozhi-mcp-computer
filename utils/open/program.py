import os
import logging
import platform
import subprocess
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('打开程序')

def open_program(mcp: FastMCP):
    @mcp.tool()
    def open_program(program_path: str) -> dict:
        """用于打开程序或快捷方式。当需要打开桌面或者菜单程序时，立刻使用该工具。
        args:
            program_path (str): 程序或快捷方式的路径,
            比如：
            C:/Users/Administrator/Desktop/Chrome.lnk
            C:/Users/Administrator/Desktop/Chrome.exe
        """
        logger.info(f"开始打开程序: {program_path}")
        # 确保路径存在
        if not os.path.exists(program_path):
            # 尝试查找可能的变体路径
            base_path = os.path.splitext(program_path)[0]
            possible_paths = [
                f"{base_path}.exe",
                f"{base_path}.EXE",
                f"{base_path}.lnk",
                f"{base_path}.LNK"
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    program_path = path
                    break
            else:
                msg = f"错误：指定的路径不存在 - {program_path}"
                logger.error(msg)
                return {"success": False, "result": msg}
        try:
            system = platform.system()
            if system == 'Windows':
                # Windows 系统
                if program_path.lower().endswith('.lnk'):
                    # 处理快捷方式文件
                    try:
                        # 尝试使用 pywin32 解析快捷方式
                        import win32com.client
                        shell = win32com.client.Dispatch("WScript.Shell")
                        shortcut = shell.CreateShortCut(program_path)
                        target_path = shortcut.Targetpath
                        if os.path.exists(target_path):
                            os.startfile(target_path)
                            msg = f"成功打开快捷方式指向的程序: {target_path}"
                            logger.info(msg)
                            return {"success": True, "result": msg}
                        else:
                            msg = f"快捷方式指向的程序不存在: {target_path}"
                            logger.error(msg)
                            return {"success": False, "result": msg}
                    except ImportError:
                        # 如果没有安装 pywin32，直接打开快捷方式
                        os.startfile(program_path)
                        msg = f"成功打开快捷方式: {program_path}"
                        logger.info(msg)
                        return {"success": True, "result": msg}
                else:
                    # 直接打开程序
                    os.startfile(program_path)
                    msg = f"成功打开程序: {program_path}"
                    logger.info(msg)
                    return {"success": True, "result": msg}
            elif system == 'Darwin':  # macOS
                # macOS 系统
                # 尝试使用 open 命令打开应用
                subprocess.run(['open', program_path], check=True)
                msg = f"成功打开程序: {program_path}"
                logger.info(msg)
                return {"success": True, "result": msg}
            elif system == 'Linux':
                # Linux 系统
                # 尝试直接执行程序
                if os.access(program_path, os.X_OK):
                    subprocess.Popen([program_path], start_new_session=True)
                else:
                    # 尝试使用 xdg-open 打开
                    subprocess.run(['xdg-open', program_path], check=True)
                msg = f"成功打开程序: {program_path}"
                logger.info(msg)
                return {"success": True, "result": msg}
            else:
                msg = f"不支持的操作系统: {system}"
                logger.error(msg)
                return {"success": False, "result": msg}
        except Exception as e:
            msg = f"打开程序时出错: {e}"
            logger.error(msg)
            return {"success": False, "result": msg}