import logging
from mcp.server.fastmcp import FastMCP
from utils.keyboard.control import control_key_operations
from utils.keyboard.combined_input import keyboard_operations

def register_keyboard(mcp: FastMCP):
    """集中注册所有键盘工具"""
    logger = logging.getLogger('键盘工具')
    logger.info("开始注册...")
    # 注册组合输入的工具
    keyboard_operations(mcp)
    # 注册键盘控制工具
    control_key_operations(mcp)
    logger.info("注册完成")