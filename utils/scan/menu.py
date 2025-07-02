import os
import sys
import json
import winreg
import ctypes
import logging

logger = logging.getLogger('扫描开始菜单')

def scan_menu():
    """
    获取开始菜单固定项信息
    返回: (程序列表, 目录列表, 错误信息列表), 当说获取开始菜单时，立刻使用该工具。
    """
    logger.info("开始扫描开始菜单...")
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False
    errors = []
    if sys.platform != 'win32':
        error_msg = "错误：此脚本仅适用于 Windows 系统"
        logger.error(error_msg)
        errors.append(error_msg)
        return [], [], errors
    if not is_admin:
        error_msg = "警告：建议以管理员权限运行此脚本以获取完整结果"
        logger.error(error_msg)
        errors.append(error_msg)
    programs = []
    directories = []
    # 方法1：通过注册表获取
    try:
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\StartPage"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            i = 0
            while True:
                try:
                    value_name, value_data, _ = winreg.EnumValue(key, i)
                    if value_name.startswith("App") and value_data:
                        try:
                            app_info = json.loads(value_data)
                            if "Path" in app_info:
                                path = app_info["Path"]
                                if os.path.exists(path):
                                    if os.path.isdir(path):
                                        directories.append(path)
                                    else:
                                        programs.append(path)
                        except json.JSONDecodeError:
                            if os.path.exists(value_data):
                                if os.path.isdir(value_data):
                                    directories.append(value_data)
                                else:
                                    programs.append(value_data)
                    i += 1
                except WindowsError:
                    break
    except Exception as e:
        error_msg = f"访问注册表时出错: {e}"
        logger.error(error_msg)
        errors.append(error_msg)
    # 方法2：检查开始菜单文件夹中的链接
    try:
        start_menu_path = os.path.join(
            os.environ['APPDATA'], 
            r'Microsoft\Windows\Start Menu\Programs'
        )
        # 检查用户特定的开始菜单
        if os.path.exists(start_menu_path):
            for item in os.listdir(start_menu_path):
                item_path = os.path.join(start_menu_path, item)
                if item.lower().endswith('.lnk'):
                    programs.append(item_path)
        # 检查所有用户的开始菜单
        all_users_start_menu = os.path.join(
            os.environ['ALLUSERSPROFILE'], 
            r'Microsoft\Windows\Start Menu\Programs'
        )
        if os.path.exists(all_users_start_menu):
            for item in os.listdir(all_users_start_menu):
                item_path = os.path.join(all_users_start_menu, item)
                if item.lower().endswith('.lnk'):
                    try:
                        from win32com.client import Dispatch
                        shell = Dispatch('WScript.Shell')
                        shortcut = shell.CreateShortCut(item_path)
                        programs.append(shortcut.Targetpath)
                    except Exception as e:
                        logger.warning(f"无法解析快捷方式 {item_path}: {str(e)}")
                        programs.append(item_path)  # 解析失败时保留原路径
    except Exception as e:
        error_msg = f"检查开始菜单文件夹时出错: {e}"
        logger.error(error_msg)
        errors.append(error_msg)
    # 方法3：检查 Windows 11 中的固定项（通过 XML 或 JSON 配置）
    try:
        # Windows 11 可能使用不同的位置存储固定项
        possible_locations = [
            os.path.join(os.environ['LOCALAPPDATA'], r'Packages\Microsoft.Windows.StartMenuExperienceHost_cw5n1h2txyewy\LocalState'),
            os.path.join(os.environ['LOCALAPPDATA'], r'Microsoft\Windows\Shell')
        ]
        for location in possible_locations:
            if os.path.exists(location):
                for item in os.listdir(location):
                    if item.endswith(('.json', '.xml')):
                        file_path = os.path.join(location, item)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                pass  # 不再处理配置文件
                        except Exception as e:
                            pass
    except Exception as e:
        error_msg = f"检查 Windows 11 配置时出错: {e}"
        logger.error(error_msg)
        errors.append(error_msg)
    # 构建返回结果字符串
    programs_str = "固定到开始屏幕的程序，目录为：" + (os.path.dirname(programs[0]) + "：" + ",".join([os.path.basename(p) for p in programs]) if programs else "无")
    directories_str = "固定到开始屏幕的目录，目录为：" + (os.path.dirname(directories[0]) + "：" + ",".join([os.path.basename(d) for d in directories]) if directories else "无")
    # 将错误信息转换为字符串
    errors_str = "错误信息：" + ",".join(errors) if errors else ""
    # 组合所有结果
    result = f"扫描菜单结果:\n\n路径: {os.path.join(os.environ['APPDATA'], 'Microsoft\\Windows\\Start Menu\\Programs')}\n\n程序: {','.join([os.path.basename(p) for p in programs]) if programs else '无'}\n\n目录: 无"
    if errors_str:
        result += f"\n{errors_str}"
    return result