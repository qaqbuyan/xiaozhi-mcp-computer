import logging
from mcp.server.fastmcp import FastMCP
from utils.automation.document.save_data_xlsx import save_data_to_xlsx
from utils.automation.document.save_data_word import save_data_to_word


def register_document(mcp: FastMCP):
    """注册文档工具"""
    logger = logging.getLogger('文档工具')
    logger.info("开始注册...")
    # 注册xlsx处理工具
    save_data_to_xlsx(mcp)
    # 注册Word处理工具
    save_data_to_word(mcp)
    logger.info("注册完成")