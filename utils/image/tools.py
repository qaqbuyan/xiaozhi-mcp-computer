import logging
from handle.loader import load_config
from mcp.server.fastmcp import FastMCP
from utils.image.text import get_image_recognition_text
from utils.image.description import get_image_description

def register_image(mcp: FastMCP):
    """集中注册所有图像识别工具"""
    logger = logging.getLogger('图像识别工具')
    
    # 加载配置并检查是否有启用的工具
    config = load_config()
    image_config = config.get('utils', {}).get('image', {})
    
    # 检查是否有任何图像识别工具启用
    has_image_tools = any(image_config.values())
    
    if not has_image_tools:
        logger.info("所有图像识别工具已禁用，跳过注册")
        return
    
    logger.info("开始注册...")
    
    # 根据配置注册对应的工具
    if image_config.get('text', {}).get('position', False):
        get_image_recognition_text(mcp)

    # 图片描述
    if image_config.get('description', False):
        get_image_description(mcp)
    
    logger.info("注册完成")