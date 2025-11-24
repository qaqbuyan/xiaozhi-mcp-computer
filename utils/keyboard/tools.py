import logging
from handle.loader import load_config
from mcp.server.fastmcp import FastMCP
from utils.keyboard.combined import keyboard_operations
from utils.keyboard.control import control_key_operations

def register_keyboard(mcp: FastMCP):
    """集中注册所有键盘工具"""
    logger = logging.getLogger('键盘工具')
    
    # 加载配置
    config = load_config()
    keyboard_config = config.get('utils', {}).get('keyboard', {})
    
    # 检查是否有任何工具需要注册
    has_tools_to_register = any(keyboard_config.values())
    
    if not has_tools_to_register:
        logger.info("所有键盘工具已禁用，跳过注册")
        return
    
    logger.info("开始注册...")
    
    # 根据配置注册对应的工具
    if keyboard_config.get('combinatorial_input', False):
        keyboard_operations(mcp)
    
    if keyboard_config.get('control_keys', False):
        control_key_operations(mcp)
    
    logger.info("注册完成")