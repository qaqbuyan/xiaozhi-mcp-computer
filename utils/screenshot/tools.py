import logging
from mcp.server.fastmcp import FastMCP
from utils.screenshot.take import take_screenshot

def register_screenshot(mcp: FastMCP):
    """注册截图工具"""
    logger = logging.getLogger('截图工具')
    logger.info("开始注册...")
    # 注册截图工具
    take_screenshot(mcp)
    logger.info("注册完成")