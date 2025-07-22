import logging
from mcp.server.fastmcp import FastMCP
from utils.clipboard.text import get_clipboard_text
from utils.clipboard.image import get_clipboard_image

def register_clipboard(mcp: FastMCP):
    """集中注册剪切板所有工具"""
    logger = logging.getLogger('剪切板工具')
    logger.info("开始注册...")
    # 注册获取剪切板文字的工具
    get_clipboard_text(mcp)
    # 注册获取剪切板图片的工具
    get_clipboard_image(mcp)
    logger.info("注册完成")