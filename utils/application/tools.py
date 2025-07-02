import logging
from mcp.server.fastmcp import FastMCP
from utils.application.close import close_application
from utils.application.set_active import set_window_active_tool

def register_application(mcp: FastMCP):
    """注册所有程序工具"""
    logger = logging.getLogger('程序工具')
    logger.info("开始注册...")
    # 关闭指定名称的程序
    close_application(mcp)
    # 设置窗口状态
    set_window_active_tool(mcp)
    logger.info("注册完成")