import logging
from mcp.server.fastmcp import FastMCP
from utils.scan.folder_or_file import scan_folder_or_file
from utils.scan.statistics import scan_statistics

def register_scan(mcp: FastMCP):
    """集中注册所有扫描工具"""
    logger = logging.getLogger('扫描工具')
    logger.info("开始注册...")
    # 注册扫描统计的工具
    scan_statistics(mcp)
    # 注册扫描文件夹或文件的工具
    scan_folder_or_file(mcp)
    logger.info("注册完成")