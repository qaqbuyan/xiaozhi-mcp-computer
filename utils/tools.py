import logging
from mcp.server.fastmcp import FastMCP
from utils.download import download_file
from utils.system import get_system_status
from utils.screenshot import take_screenshot

def register_alone(mcp: FastMCP):
    """注册单独工具"""
    logger = logging.getLogger('单独工具')
    logger.info("开始注册...")
    # 注册获取系统状态的工具
    get_system_status(mcp)
    # 注册截图工具
    take_screenshot(mcp)
    # 注册下载文件工具
    download_file(mcp)
    logger.info("注册完成")