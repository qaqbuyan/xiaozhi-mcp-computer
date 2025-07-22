import logging
from mcp.server.fastmcp import FastMCP
from utils.automation.document.tools import register_document

def register_automation(mcp: FastMCP):
    """注册自动化工具"""
    logger = logging.getLogger('自动化工具')
    logger.info("开始注册...")
    # 注册文档工具
    register_document(mcp)
    logger.info("注册完成")