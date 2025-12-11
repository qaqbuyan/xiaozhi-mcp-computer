import os
import os.path
import logging
import requests
from PIL import Image
from io import BytesIO
from getmac import get_mac_address
from handle.loader import load_config

logger = logging.getLogger('图像描述')

#发送本地图片进行识别
def identify_description(question: str, img_data) -> dict:
    try:
        logger.info("开始进行图像描述识别...")
        # 判断img_data是文件路径还是字节流
        if isinstance(img_data, str) and os.path.exists(img_data):
            logger.info("使用理解为文件路径的图像描述识别...")
            # 如果是文件路径，直接使用
            img_path = img_data
            img_name = os.path.basename(img_data)
            # 验证文件后缀名只允许JPG格式（不区分大小写）
            file_ext = os.path.splitext(img_path)[1].lower()
            if file_ext not in ['.jpg', '.jpeg']:
                logger.error(f"不支持的文件格式: {file_ext}，只支持JPG/JPEG格式")
                return {"success": False, "result": f"不支持的文件格式: {file_ext}，只支持JPG/JPEG格式"}
        else:
            logger.info("使用理解为字节流的图像描述识别...")
            # 如果是字节流，保存为临时文件
            import time
            tmp_dir = os.path.join(os.getcwd(), "tmp")
            os.makedirs(tmp_dir, exist_ok=True)
            # 生成唯一的文件名
            timestamp = int(time.time() * 1000)
            temp_file_path = os.path.join(tmp_dir, f"clipboard_{timestamp}.png")
            # 使用PIL处理字节流并保存为JPG格式
            try:
                pil_image = Image.open(BytesIO(img_data))
                # 如果图片有透明通道，转换为RGB模式以支持JPG格式
                if pil_image.mode in ('RGBA', 'LA', 'P'):
                    pil_image = pil_image.convert('RGB')
                pil_image.save(temp_file_path, format='JPEG', quality=95)
                img_name = "clipboard_image.jpg"
                logger.info(f"已转换图片格式为JPG并保存到tmp目录，原格式: {pil_image.format}")
            except Exception as e:
                logger.error(f"图片格式转换失败: {str(e)}")
                return {"success": False, "result": f"图片格式转换失败: {str(e)}"}
            img_path = temp_file_path
        # 验证文件是否存在
        if not os.path.exists(img_path):
            logger.error(f"图片文件不存在: {img_path}")
            return {"success": False, "result": f"图片文件不存在: {img_path}"}
        # 直接读取本地图片文件
        with open(img_path, 'rb') as f:
            img = f.read()
        mac_address = get_mac_address()
        files = {
            'file': (img_name, img, 'image/jpeg')
        }
        data = {
            'question': question,
        }
        # 从配置中获取API参数
        config = load_config()
        ai_api_base = config.get('ai_api_base', '')
        token = config.get('token', '')
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Device-Id": mac_address,
            "Client-Id": mac_address,
        }
        logger.info(f"开始进行图像描述识别")
        logger.info("---------------")
        logger.info(f"问题描述: {question}")
        logger.info(f"图片路径: {img_path}")
        logger.info(f"图片名称: {os.path.basename(img_path)}")
        try:
            # 构建完整的API URL
            api_url = f"https://{ai_api_base}/vision/explain"
            # 设置超时时间为30秒，避免网络延迟导致的超时错误
            response = requests.post(api_url, headers=headers, files=files, data=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            logger.info(f"✓ 识别成功!")
            logger.info("识别结果：")
            logger.info(result['text'])
            logger.info("---------------")
            logger.info(f"成功识别图像描述")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            logger.error(f"✗ 识别失败!")
            logger.error(f"错误信息：")
            logger.error(error_msg)
            logger.error("---------------")
            return {"success": False, "result": error_msg}
    except FileNotFoundError:
        error_msg = f"文件未找到: {img_path}"
        logger.error(error_msg)
        return {"success": False, "result": error_msg}
    except Exception as e:
        error_msg = f"读取图片文件失败: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "result": error_msg}