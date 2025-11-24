import logging
from handle.loader import load_config
from mcp.server.fastmcp import FastMCP
from utils.system import get_system_status
from utils.download import download_url_file
from utils.command import run_computer_command

def register_alone(mcp: FastMCP):
    """注册单独工具"""
    logger = logging.getLogger('单独工具')
    
    # 加载配置
    config = load_config()
    alone_config = config.get('utils', {}).get('alone', {})
    
    # 检查是否有任何工具需要注册
    has_tools_to_register = any(alone_config.values())
    
    if not has_tools_to_register:
        logger.info("所有单独工具已禁用，跳过注册")
        return
    
    logger.info("开始注册...")
    
    # 根据配置注册对应的工具
    if alone_config.get('system_status', False):
        get_system_status(mcp)
    
    if alone_config.get('download_file', False):
        download_url_file(mcp)
    
    if alone_config.get('run_command', False):
        run_computer_command(mcp)
    
    logger.info("注册完成")