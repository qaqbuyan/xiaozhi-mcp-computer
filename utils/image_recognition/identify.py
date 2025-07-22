import os
import logging
import requests
from handle.loader import load_config
from requests.exceptions import ConnectionError

logger = logging.getLogger('图像文字识别')

def identify_image_text_coordinates(image: str, timeout: int = 15) -> dict:
    logger.info(f"开始识别图像 {image} 的文字...")
    if not os.path.exists(image):
        msg = f"错误：文件 {image} 不存在"
        logger.error(msg)
        return {"success": False, "result": msg}
    try:
        # 设置 User-Agent 头
        headers = {
            'User-Agent': load_config().get('user_agent')
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
            timeout=timeout
        )
        # 检查响应状态码
        if r.status_code != 200:
            msg = f"OCR服务返回错误状态码：{r.status_code}，响应内容：{r.text}"
            logger.error(msg)
            return {"success": False, "result": msg}
        try:
            ocr_out = r.json()['results']
        except ValueError:
            msg = f"OCR服务返回非JSON格式内容：{r.text}"
            logger.error(msg)
            return {"success": False, "result": msg}
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