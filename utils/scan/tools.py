import logging
from handle.loader import load_config
from mcp.server.fastmcp import FastMCP
from utils.scan.statistics import scan_statistics
from utils.scan.folder_or_file import scan_folder_or_file

def register_scan(mcp: FastMCP):
    """集中注册所有扫描工具"""
    logger = logging.getLogger('扫描工具')
    
    # 加载配置并检查是否有启用的工具
    config = load_config()
    scan_config = config.get('utils', {}).get('scan', {})
    
    # 检查是否有任何扫描工具启用
    has_scan_tools = any(scan_config.values())
    
    if not has_scan_tools:
        logger.info("所有扫描工具已禁用，跳过注册")
        return
    
    logger.info("开始注册...")
    
    # 根据配置注册对应的工具
    if scan_config.get('directory', False):
        scan_folder_or_file(mcp)
    
    if scan_config.get('file', False):
        scan_statistics(mcp)
    
    logger.info("注册完成")