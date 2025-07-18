import os
import logging
import requests
from handle.loader import load_config
from mcp.server.fastmcp import FastMCP
from requests.exceptions import ConnectionError

logger = logging.getLogger('图像文字识别')

def get_image_recognition_text(mcp: FastMCP):
    """图像识别文字坐标工具"""
    @mcp.tool()
    def get_image_recognition_text(image: str) -> dict:
        """用于识别图像中的文字以及坐标
        Args:
            image (str): 图像文件的路径, 支持png, jpg, jpeg, gif，比如 'C:/Users/用户名/Desktop/图片.png'
        Returns:
            dict: 返回识别结果或错误信息
        """
        logger.info(f"开始识别图像 {image} 的文字...")
        if not os.path.exists(image):
            msg = f"错误：文件 {image} 不存在"
            logger.error(msg)
            return {"success": False, "result": msg}
        try:
            # 设置 User-Agent 头
            headers = {
                'User-Agent': load_config().get('http_headers', {}).get('user_agent')
            }
            # 根据文件扩展名确定 MIME 类型
            _, ext = os.path.splitext(image)
            mime_type = { 
                '.png': 'image/png', 
                '.jpg': 'image/jpeg', 
                '.jpeg': 'image/jpeg', 
                '.gif': 'image/gif' 
            }.get(ext.lower(), 'application/octet-stream')
            r = requests.post(
                'https://qaqbuyan.com:88/api/ocr/',
                files={'image': (image, open(image, 'rb'), mime_type)},
                headers=headers,
                timeout=10
            )
            ocr_out = r.json()['results']
            logger.info(f"成功识别图像 {image} 的文字")
            logger.info(f"识别结果: {ocr_out}")
            return {"success": True, "result": ocr_out}
        except ConnectionError as e:
            msg = f"错误：无法连接到OCR服务：{str(e)}"
            logger.error(msg)
            return {"success": False, "result": msg}
        except Exception as e:
            msg = f"处理错误：{str(e)}"
            logger.error(msg)
            return {"success": False, "result": msg}