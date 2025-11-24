import logging
from handle.loader import load_config
from mcp.server.fastmcp import FastMCP
from utils.screenshot.take import take_screenshot

def register_screenshot(mcp: FastMCP):
    """注册截图工具"""
    logger = logging.getLogger('截图工具')
    
    # 加载配置并检查是否有启用的工具
    config = load_config()
    screenshot_config = config.get('utils', {}).get('screenshot', {})
    
    # 检查是否有任何截图工具启用
    has_screenshot_tools = any(screenshot_config.values())
    
    if not has_screenshot_tools:
        logger.info("所有截图工具已禁用，跳过注册")
        return
    
    logger.info("开始注册...")
    
    # 根据配置注册对应的工具
    if screenshot_config.get('take', False):
        take_screenshot(mcp)
    
    logger.info("注册完成")