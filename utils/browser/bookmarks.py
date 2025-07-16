import os
import json
import sqlite3
import logging
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from utils.browser.edge import get_edge_bookmarks
from utils.browser.chrome import get_chrome_bookmarks
from utils.browser.firefox import get_firefox_bookmarks

logger = logging.getLogger('书签工具')

def get_browser_bookmarks(mcp: FastMCP):
    @mcp.tool()
    def get_browser_bookmarks(browser_type: str = None) -> dict:
        """获取浏览器书签, 当得到获取浏览器书签的结果时，可以使用‘open_website’工具打开对应的书签。
        注意：
            1. 当浏览器书签获取成功时，使用‘open_website’工具要保证书签的URL跟传入‘open_website’工具的URL是一致的。
                以及书签的URL为标准，传入‘open_website’工具。
        Args:
            browser_type (str, optional): 'chrome', 'firefox', 'edge' 或 None(自动检测默认浏览器)
        Returns:
            dict: 包含操作结果的字典，格式如下：
                {
                    "success": bool,  # 操作是否成功的标志
                    "result": list,   # 书签列表，格式为 [
                        {
                            'folder': '文件夹名称',
                            'list': [
                                {'title': '书签标题', 'url': '书签URL'},
                                {'title': '书签标题', 'url': '书签URL'},
                                ...
                            ]
                        },
                        ...
                    ],
                    "browser_type": str, # 浏览器类型('chrome','firefox','edge'或'auto')
                    "error": str      # 错误信息(如果有)
                }
        """
        try:
            if browser_type == 'chrome':
                bookmarks = get_chrome_bookmarks()
            elif browser_type == 'firefox':
                bookmarks = get_firefox_bookmarks()
            elif browser_type == 'edge':
                bookmarks = get_edge_bookmarks()
            else:
                # 默认按顺序尝试获取书签
                try:
                    bookmarks = get_chrome_bookmarks()
                except:
                    try:
                        bookmarks = get_firefox_bookmarks()
                    except:
                        bookmarks = get_edge_bookmarks()
            logger.info(f"成功获取{browser_type or ' 默认 '}浏览器书签")
            logger.info(f"书签内容：{bookmarks}")
            return {
                "success": True,
                "browser_type": browser_type or 'auto',
                "result": bookmarks
            }
        except Exception as e:
            msg = f"获取{browser_type or ' 默认 '}浏览器书签时出错: {e}"
            logger.error(msg)
            return {
                "success": False,
                "browser_type": browser_type or 'auto',
                "error": msg
            }