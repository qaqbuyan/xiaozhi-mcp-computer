import logging
from mcp.server.fastmcp import FastMCP
from utils.keyboard.combined import keyboard_operations
from utils.keyboard.control import control_key_operations
from utils.keyboard.text import input_content_by_mouse_position

def register_keyboard(mcp: FastMCP):
    """集中注册所有键盘工具"""
    logger = logging.getLogger('键盘工具')
    logger.info("开始注册...")
    # 注册组合输入的工具
    keyboard_operations(mcp)
    # 注册键盘控制工具
    control_key_operations(mcp)
    # 注册鼠标位置输入文本工具
    input_content_by_mouse_position(mcp)
    logger.info("注册完成")