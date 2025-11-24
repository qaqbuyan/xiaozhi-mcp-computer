import logging
from handle.loader import load_config
from mcp.server.fastmcp import FastMCP
from utils.automation.document.save_data_xlsx import save_data_to_xlsx
from utils.automation.document.save_data_word import save_data_to_word

def register_document(mcp: FastMCP):
    """注册文档工具"""
    logger = logging.getLogger('文档工具')
    
    # 加载配置
    config = load_config()
    document_config = config.get('utils', {}).get('automation', {}).get('document', {})
    
    # 检查是否有任何工具需要注册
    has_tools_to_register = any(document_config.values())
    
    if not has_tools_to_register:
        logger.info("所有文档工具已禁用，跳过注册")
        return
    
    logger.info("开始注册...")
    
    # 根据配置注册对应的工具
    if document_config.get('xlsx', False):
        save_data_to_xlsx(mcp)
    
    if document_config.get('word', False):
        save_data_to_word(mcp)
    
    logger.info("注册完成")