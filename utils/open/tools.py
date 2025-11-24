import logging
from handle.loader import load_config
from utils.open.file import open_file
from mcp.server.fastmcp import FastMCP
from utils.open.desktop import open_desktop
from utils.open.website import open_website
from utils.open.program import open_program
from utils.open.directory import open_directory

def register_open(mcp: FastMCP):
    """注册所有打开工具"""
    logger = logging.getLogger('打开工具')
    
    # 加载配置并检查是否有启用的工具
    config = load_config()
    open_config = config.get('utils', {}).get('open', {})
    
    # 检查是否有任何打开工具启用
    has_open_tools = any(open_config.values())
    
    if not has_open_tools:
        logger.info("所有打开工具已禁用，跳过注册")
        return
    
    logger.info("开始注册...")
    
    # 根据配置注册对应的工具
    if open_config.get('desktop', False):
        open_desktop(mcp)
    
    if open_config.get('directory', False):
        open_directory(mcp)
    
    if open_config.get('website', False):
        open_website(mcp)
    
    if open_config.get('program', False):
        open_program(mcp)
    
    if open_config.get('file', False):
        open_file(mcp)
    
    logger.info("注册完成")