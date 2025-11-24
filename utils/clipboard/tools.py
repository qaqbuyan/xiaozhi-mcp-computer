import logging
from mcp.server.fastmcp import FastMCP
from utils.clipboard.text import get_clipboard_text
from utils.clipboard.image import get_clipboard_image
from handle.loader import load_config

def register_clipboard(mcp: FastMCP):
    """集中注册剪切板所有工具"""
    logger = logging.getLogger('剪切板工具')
    
    # 加载配置
    config = load_config()
    clipboard_config = config.get('utils', {}).get('clipboard', {})
    
    # 检查是否有任何剪贴板工具启用
    has_clipboard_tools = any(clipboard_config.values())
    
    if not has_clipboard_tools:
        logger.info("所有剪贴板工具已禁用，跳过注册")
        return
    
    logger.info("开始注册...")
    
    # 根据配置注册对应的工具
    if clipboard_config.get('get_text', False):
        # 注册获取剪切板文字的工具
        get_clipboard_text(mcp)
    
    if clipboard_config.get('get_image', False):
        # 注册获取剪切板图片的工具
        get_clipboard_image(mcp)
    
    logger.info("注册完成")