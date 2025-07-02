import logging
from mcp.server.fastmcp import FastMCP
from utils.mouse.click import mouse_click
from utils.mouse.long_press import mouse_long_press
from utils.mouse.up_down_roll import mouse_up_and_down_move
from utils.mouse.horizontal_roll import mouse_horizontal_move

def register_mouse(mcp: FastMCP):
    """集中注册所有鼠标工具"""
    logger = logging.getLogger('鼠标工具')
    logger.info("开始注册...")
    # 注册鼠标点击工具
    mouse_click(mcp)
    # 注册鼠标水平滚动工具
    mouse_horizontal_move(mcp)
    # 注册鼠标上下滚动工具
    mouse_up_and_down_move(mcp)
    # 注册鼠标长按工具
    mouse_long_press(mcp)
    logger.info("注册完成")