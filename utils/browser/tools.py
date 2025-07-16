import logging
from mcp.server.fastmcp import FastMCP
from utils.browser.bookmarks import get_browser_bookmarks

def register_browser(mcp: FastMCP):
    """集中注册所有浏览器工具"""
    logger = logging.getLogger('浏览器工具')
    logger.info("开始注册...")
    # 注册获取浏览器书签的工具
    get_browser_bookmarks(mcp)
    logger.info("注册完成")