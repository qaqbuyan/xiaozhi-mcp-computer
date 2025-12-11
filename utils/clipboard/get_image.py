import os
import io
import logging
from PIL import Image
from PIL import ImageGrab

logger = logging.getLogger('剪切板图片')

def get_image() -> dict:
    try:
        logger.info("开始获取剪切板图片...")
        img = ImageGrab.grabclipboard()
        if img is None:
            msg = "错误：剪贴板中没有图片内容" 
            logger.error(msg)
            return {"success": False, "result": msg}
        # 打印剪贴板内容的类型和值，便于调试
        logger.info(f"剪贴板内容类型: {type(img)}, 值: {img}")
        # 检查获取到的对象是否为文件路径列表
        if isinstance(img, list):
            if img and isinstance(img[0], str) and os.path.exists(img[0]):
                # 如果是文件路径列表，直接返回第一个文件路径
                logger.info(f"获取到剪切板图片路径: {img[0]}")
                return {"success": True, "result": img[0]}
            elif img and isinstance(img[0], Image.Image):
                img = img[0]
            else:
                msg = "错误：剪贴板中的内容不是有效的图片列表或文件路径列表" 
                logger.error(msg)
                return {"success": False, "result": msg}
        elif isinstance(img, Image.Image):
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            logger.info("获取到剪切板图片字节流")
            return {"success": True, "result": img_byte_arr.getvalue()}
        else:
            msg = "错误：剪贴板中的内容不是有效的图片对象或文件路径" 
            logger.error(msg)
            return {"success": False, "result": msg}
    except Exception as e:
        msg = f"从剪贴板获取图片失败：{str(e)}"
        logger.error(msg)
        return {"success": False, "result": msg}