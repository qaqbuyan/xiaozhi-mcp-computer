import logging
from handle.loader import load_config
from mcp.server.fastmcp import FastMCP
from utils.application.close import close_application
from utils.application.set_active import set_window_active_tool

def register_application(mcp: FastMCP):
    """注册所有程序工具"""
    logger = logging.getLogger('程序工具')
    
    # 加载配置
    config = load_config()
    application_config = config.get('utils', {}).get('application', {})
    
    # 检查是否有任何工具需要注册
    has_tools_to_register = any(application_config.values())
    
    if not has_tools_to_register:
        logger.info("所有程序工具已禁用，跳过注册")
        return
    
    logger.info("开始注册...")
    
    # 根据配置注册对应的工具
    if application_config.get('close', False):
        close_application(mcp)
    
    if application_config.get('set_active', False):
        set_window_active_tool(mcp)
    
    logger.info("注册完成")