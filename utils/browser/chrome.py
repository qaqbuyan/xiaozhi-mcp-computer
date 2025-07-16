import os
import json
import logging
from pathlib import Path
from utils.browser.extract import extract_bookmarks

logger = logging.getLogger('chrome书签')

def get_chrome_bookmarks():
    """获取Chrome浏览器书签"""
    try:
        logger.info("开始获取Chrome书签")
        # Chrome书签路径检测逻辑
        possible_paths = []
        if os.name == 'nt':  # Windows
            default_path = Path(os.environ['USERPROFILE']) / 'AppData/Local/Google/Chrome/User Data/Default/Bookmarks'
            possible_paths.append(default_path)
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\chrome.exe') as key:
                    chrome_path = Path(winreg.QueryValue(key, None)).parent.parent
                    possible_paths.append(chrome_path / 'User Data/Default/Bookmarks')
            except:
                pass
            user_data_dir = Path(os.environ['USERPROFILE']) / 'AppData/Local/Google/Chrome'
            for profile_dir in user_data_dir.glob('User Data/*'):
                possible_paths.append(profile_dir / 'Bookmarks')
        # 检查所有可能的路径
        path = None
        for p in possible_paths:
            if p.exists():
                path = p
                break
        if not path:
            return []
        # 读取并解析书签文件
        with open(path, 'r', encoding='utf-8') as f:
            bookmarks = json.load(f)
        # 递归提取书签信息
        result = []
        for root_node in bookmarks['roots'].values():
            folder = extract_bookmarks(root_node)
            if folder:
                result.append(folder)
        logger.info(f"成功获取Chrome书签")
        return result
    # 修改错误处理部分
    except Exception as e:
        logger.error(f"获取Chrome书签出错: {e}")
        return []