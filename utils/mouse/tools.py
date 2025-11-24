import logging
from handle.loader import load_config
from mcp.server.fastmcp import FastMCP
from utils.mouse.click import mouse_click
from utils.mouse.region import move_mouse_region
from utils.mouse.long_press import mouse_long_press
from utils.mouse.position import get_mouse_position
from utils.mouse.up_down_roll import mouse_up_and_down_move
from utils.mouse.horizontal_roll import mouse_horizontal_move
from utils.mouse.identify_move import identify_move_page_position
from utils.mouse.text import input_content_by_mouse_position

def register_mouse(mcp: FastMCP):
    """集中注册所有鼠标工具"""
    logger = logging.getLogger('鼠标工具')
    
    # 加载配置
    config = load_config()
    mouse_config = config.get('utils', {}).get('mouse', {})
    
    # 检查是否有任何工具需要注册
    has_tools_to_register = any(mouse_config.values())
    
    if not has_tools_to_register:
        logger.info("所有鼠标工具已禁用，跳过注册")
        return
    
    logger.info("开始注册...")
    
    # 根据配置注册对应的工具
    if mouse_config.get('click', False):
        mouse_click(mcp)
    
    if mouse_config.get('horizontal', False):
        mouse_horizontal_move(mcp)
    
    if mouse_config.get('scroll', False):
        mouse_up_and_down_move(mcp)
    
    if mouse_config.get('long_press', False):
        mouse_long_press(mcp)
    
    if mouse_config.get('position', False):
        get_mouse_position(mcp)
    
    if mouse_config.get('region', False):
        move_mouse_region(mcp)
    
    if mouse_config.get('identify_move_page_position', False):
        identify_move_page_position(mcp)
    
    if mouse_config.get('input_content_by_mouse_position', False):
        input_content_by_mouse_position(mcp)
    
    logger.info("注册完成")