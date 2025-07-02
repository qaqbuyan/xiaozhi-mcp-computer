import logging
from mcp.server.fastmcp import FastMCP
from utils.open.desktop import open_desktop
from utils.open.website import open_website
from utils.open.program import open_program
from utils.open.directory import open_directory

def register_open(mcp: FastMCP):
    """注册所有打开工具"""
    logger = logging.getLogger('打开工具')
    logger.info("开始注册...")
    # 注册打开桌面目录的工具
    open_desktop(mcp)
    # 注册打开目录的工具
    open_directory(mcp)
    # 注册打开网站的工具
    open_website(mcp)
    # 注册打开程序的工具
    open_program(mcp)
    logger.info("注册完成")