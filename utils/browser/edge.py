import os
import json
import logging
from pathlib import Path
from utils.browser.extract import extract_bookmarks

logger = logging.getLogger('Edge书签')

def get_edge_bookmarks():
    """获取Microsoft Edge浏览器书签"""
    try:
        logger.info("开始获取Edge书签")
        # Edge书签路径检测逻辑
        possible_paths = []
        if os.name == 'nt':  # Windows
            default_path = Path(os.environ['USERPROFILE']) / 'AppData/Local/Microsoft/Edge/User Data/Default/Bookmarks'
            possible_paths.append(default_path)
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\msedge.exe') as key:
                    edge_path = Path(winreg.QueryValue(key, None)).parent.parent
                    possible_paths.append(edge_path / 'User Data/Default/Bookmarks')
            except:
                pass
            user_data_dir = Path(os.environ['USERPROFILE']) / 'AppData/Local/Microsoft/Edge'
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
        logger.info(f"成功获取Edge书签")
        return result
    except Exception as e:
        logger.error(f"获取Edge书签出错: {str(e)}")
        return []