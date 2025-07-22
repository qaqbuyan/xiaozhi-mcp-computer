import logging
from mcp.server.fastmcp import FastMCP
from utils.system import get_system_status
from utils.download import download_url_file
from utils.command import run_computer_command

def register_alone(mcp: FastMCP):
    """注册单独工具"""
    logger = logging.getLogger('单独工具')
    logger.info("开始注册...")
    # 注册获取系统状态的工具
    get_system_status(mcp)
    # 注册下载文件工具
    download_url_file(mcp)
    # 注册执行命令工具
    run_computer_command(mcp)
    logger.info("注册完成")