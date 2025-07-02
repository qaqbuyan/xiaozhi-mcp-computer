import os
import ctypes
import logging
import platform
from pathlib import Path

logger = logging.getLogger('扫描桌面')

def scan_desktop() -> str:
    """获取并返回桌面信息，兼容Windows、macOS和Linux, 当说获取桌面内容时，立刻使用该工具。"""
    logger.info("开始扫描桌面...")
    system = platform.system()
    errors = []
    # 获取桌面路径
    if system == 'Windows':
        CSIDL_DESKTOP = 0
        buf = ctypes.create_unicode_buffer(1024)
        ctypes.windll.shell32.SHGetSpecialFolderPathW(None, buf, CSIDL_DESKTOP, False)
        desktop_path = buf.value
    else:
        desktop_path = os.path.join(Path.home(), "Desktop")
    # 确保桌面路径存在
    if not os.path.exists(desktop_path):
        error_msg = f"错误：桌面路径不存在 - {desktop_path}"
        return f"错误信息: {error_msg}"
    # 列出桌面项目
    items = os.listdir(desktop_path)
    # 区分程序和目录
    programs = []
    directories = []
    for item in items:
        item_path = os.path.join(desktop_path, item)
        if os.path.isdir(item_path):
            directories.append(item)
        elif os.path.isfile(item_path):
            # 检查是否为可执行文件
            if system == 'Windows' and item.lower().endswith('.lnk'):
                try:
                    from win32com.client import Dispatch
                    shell = Dispatch('WScript.Shell')
                    shortcut = shell.CreateShortCut(item_path)
                    target = shortcut.Targetpath
                    if os.path.isfile(target):
                        programs.append(item)
                    else:
                        logger.debug(f"快捷方式目标不存在: {target}")
                except ImportError:
                    logger.warning("未安装pywin32模块，无法解析快捷方式")
                    programs.append(item)  # 保留快捷方式名称
                except Exception as e:
                    logger.warning(f"解析快捷方式失败: {str(e)}")
                    programs.append(item)  # 修改这里，不再检查.exe后缀
            elif system == 'Windows' and item.lower().endswith('.exe'):
                programs.append(item)
            elif system in ('Darwin', 'Linux') and os.access(item_path, os.X_OK):
                programs.append(item)
    # 构建返回结果字符串
    desktop_str = f"桌面路径: {desktop_path}"
    programs_str = "桌面上的程序:" + ",".join(programs) if programs else ""
    directories_str = "桌面上的目录:" + ",".join(directories) if directories else ""
    errors_str = "错误信息:" + ",".join(errors) if errors else ""
    # 组合所有结果
    result = f"{desktop_str}\n{programs_str}\n{directories_str}"
    if errors_str:
        result += f"\n{errors_str}"
    return result