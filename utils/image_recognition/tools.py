import logging
from handle.loader import load_config
from mcp.server.fastmcp import FastMCP
from utils.image_recognition.text import get_image_recognition_text

def register_image_recognition(mcp: FastMCP):
    """集中注册所有图像识别工具"""
    logger = logging.getLogger('图像识别工具')
    
    # 加载配置并检查是否有启用的工具
    config = load_config()
    image_recognition_config = config.get('utils', {}).get('image_recognition', {})
    
    # 检查是否有任何图像识别工具启用
    has_image_recognition_tools = any(image_recognition_config.values())
    
    if not has_image_recognition_tools:
        logger.info("所有图像识别工具已禁用，跳过注册")
        return
    
    logger.info("开始注册...")
    
    # 根据配置注册对应的工具
    if image_recognition_config.get('text', False):
        get_image_recognition_text(mcp)
    
    logger.info("注册完成")