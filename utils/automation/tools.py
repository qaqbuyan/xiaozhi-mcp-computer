import logging
from handle.loader import load_config
from mcp.server.fastmcp import FastMCP
from utils.automation.document.tools import register_document

def register_automation(mcp: FastMCP):
    """注册自动化工具"""
    logger = logging.getLogger('自动化工具')
    
    # 加载配置
    config = load_config()
    document_config = config.get('utils', {}).get('automation', {}).get('document', {})
    
    # 检查是否有任何文档工具需要注册
    has_document_tools = any(document_config.values())
    
    if not has_document_tools:
        logger.info("所有文档工具已禁用，跳过注册")
        return
    
    logger.info("开始注册...")
    # 注册文档工具
    register_document(mcp)
    logger.info("注册完成")