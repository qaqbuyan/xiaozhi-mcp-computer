import os
import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger('Firefox书签')

def get_firefox_bookmarks():
    """获取Firefox浏览器书签"""
    try:
        logger.info("开始获取Firefox书签")
        # 首先检查Firefox是否安装
        if os.name == 'nt':  # Windows
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE\\Mozilla\\Mozilla Firefox') as key:
                    pass
            except:
                logger.error("未安装Firefox浏览器")
                return []  # 未安装Firefox
        # Firefox书签路径检测逻辑
        if os.name == 'nt':  # Windows
            profiles_path = Path(os.environ['USERPROFILE']) / 'AppData/Roaming/Mozilla/Firefox/Profiles/'
        elif os.name == 'posix':  # macOS/Linux
            if os.path.exists(Path.home() / 'Library/Application Support/Firefox/Profiles/'):
                profiles_path = Path.home() / 'Library/Application Support/Firefox/Profiles/'
            else:
                profiles_path = Path.home() / '.mozilla/firefox/'
        else:
            return []
        if not profiles_path.exists():
            return []
        # 查找默认配置文件
        profile_dir = None
        for item in profiles_path.iterdir():
            if item.is_dir() and 'default' in item.name.lower():
                profile_dir = item
                break
        if not profile_dir:
            return []
        # 检查places.sqlite是否存在
        places_db = profile_dir / 'places.sqlite'
        if not places_db.exists():
            return []
        # 连接SQLite数据库并查询书签
        conn = sqlite3.connect(str(places_db))
        cursor = conn.cursor()
        cursor.execute('''
            SELECT b.title, p.url, f.title 
            FROM moz_bookmarks b
            JOIN moz_places p ON b.fk = p.id
            LEFT JOIN moz_bookmarks f ON b.parent = f.id
            WHERE b.type = 1
        ''')
        result = []
        current_folder = None
        folder_items = []
        for row in cursor.fetchall():
            title, url, folder = row
            if url and url.startswith(('http://', 'https://')):
                folder_items.append({
                    'title': title or '',
                    'url': url
                })
            if folder != current_folder:
                if current_folder is not None:
                    result.append({
                        'folder': current_folder or '未分类',
                        'list': folder_items
                    })
                current_folder = folder
                folder_items = []
        # 添加最后一个文件夹
        if current_folder is not None:
            result.append({
                'folder': current_folder or '未分类',
                'list': folder_items
            })
        conn.close()
        logger.info(f"成功获取Firefox书签")
        return result
    except Exception as e:
        logger.error(f"获取Firefox书签出错: {str(e)}")
        return []