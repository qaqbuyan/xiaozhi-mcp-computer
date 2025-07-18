import logging
from mcp.server.fastmcp import FastMCP
from utils.image_recognition.text import get_image_recognition_text

def register_image_recognition(mcp: FastMCP):
    """集中注册所有图像识别工具"""
    logger = logging.getLogger('图像识别工具')
    logger.info("开始注册...")
    # 注册图像识别文字工具
    get_image_recognition_text(mcp)
    logger.info("注册完成")