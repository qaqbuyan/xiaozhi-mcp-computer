import os
import logging
import requests
from handle.loader import load_config
from requests.exceptions import ConnectionError

logger = logging.getLogger('图像文字识别')

def identify_image_text_coordinates(image: str) -> dict:
    logger.info(f"开始识别图像 {image} 的文字...")
    if not os.path.exists(image):
        msg = f"错误：文件 {image} 不存在"
        logger.error(msg)
        return {"success": False, "result": msg}
    try:
        # 获取配置
        config_data = load_config()
        
        # 从配置中获取超时时间，使用默认值15秒作为回退
        timeout = config_data.get('utils', {}).get('image', {}).get('timeout', 15)
        
        # 设置 User-Agent 头
        headers = {
            'User-Agent': config_data.get('user_agent')
        }
        # 根据文件扩展名确定 MIME 类型
        _, ext = os.path.splitext(image)
        mime_type = { 
            '.png': 'image/png', 
            '.jpg': 'image/jpeg', 
            '.jpeg': 'image/jpeg', 
            '.gif': 'image/gif' 
        }.get(ext.lower(), 'application/octet-stream')
        config_data = load_config()
        ocr_url_config = config_data.get('utils', {}).get('image', {}).get('text', {}).get('ocr')
        if ocr_url_config is None or ocr_url_config == 'https://qaqbuyan.com:88/api/ocr/':
            ocr_url = 'https://qaqbuyan.com:88/api/ocr/'
            logger.info("使用公益默认OCR接口，如需更高性能请配置自定义OCR服务")
        else:
            ocr_url = ocr_url_config
            logger.info(f"使用自定义OCR接口: {ocr_url}")
        
        # 验证OCR URL格式
        if not ocr_url.startswith(('http://', 'https://')):
            msg = f"错误：OCR URL格式不正确，必须以http://或https://开头，当前URL: {ocr_url}"
            logger.error(msg)
            return {"success": False, "result": msg}
        
        # 验证URL基本格式
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(ocr_url)
            if not parsed_url.netloc:  # 检查是否有有效的主机名
                msg = f"错误：OCR URL格式不正确，缺少有效的主机名，当前URL: {ocr_url}"
                logger.error(msg)
                return {"success": False, "result": msg}
        except Exception as e:
            msg = f"错误：OCR URL解析失败，当前URL: {ocr_url}，错误: {str(e)}"
            logger.error(msg)
            return {"success": False, "result": msg}
        
        r = requests.post(
            ocr_url,
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