import logging
from handle.loader import load_config
from mcp.server.fastmcp import FastMCP
from utils.browser.bookmarks import get_browser_bookmarks

def register_browser(mcp: FastMCP):
    """集中注册所有浏览器工具"""
    logger = logging.getLogger('浏览器工具')
    
    # 加载配置并检查是否有启用的工具
    config = load_config()
    browser_config = config.get('utils', {}).get('browser', {})
    
    # 检查是否有任何浏览器工具启用
    has_browser_tools = any(browser_config.values())
    
    if not has_browser_tools:
        logger.info("所有浏览器工具已禁用，跳过注册")
        return
    
    logger.info("开始注册...")
    
    # 根据配置注册对应的工具
    if browser_config.get('bookmarks', False):
        get_browser_bookmarks(mcp)
    
    logger.info("注册完成")