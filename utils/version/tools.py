import logging
from mcp.server.fastmcp import FastMCP
from utils.version.check import check_version
from utils.version.update import update_client

def register_version(mcp: FastMCP):
    """注册版本工具"""
    logger = logging.getLogger('版本工具')
    logger.info("开始注册...")
    # 注册版本检查工具
    check_version(mcp)
    # 注册版本更新工具
    update_client(mcp)
    logger.info("注册完成")