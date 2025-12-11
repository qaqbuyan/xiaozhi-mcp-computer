import logging
from mcp.server.fastmcp import FastMCP
from utils.clipboard.get_image import get_image
from utils.image.identify_description import identify_description

logger = logging.getLogger('图像描述')

def get_image_description(mcp: FastMCP):
    """图像描述工具"""
    @mcp.tool()
    def get_image_description(question: str, img_path: str) -> dict:
        """用于描述图像信息，用户需要询问图像(剪切板的图片)中的信息时，立刻调用该工具。
        比如用户说"请描述图片内容"，立刻调用该工具，工具会返回图像中的描述。
        注意：
            1.这是用来获取图像中的描述（询问的问题），如果是图片识别文字或者坐标，请使用'get_image_recognition_text'工具，
            2.只要用户需要描述图像中的内容，就必须使用这个工具
            3.这个工具只能描述图像中的内容，不能识别图像中的文字或者坐标
            4.这个工具可能会超时，如果超时，请重新调用该工具，不需要确认立刻再调用
        Args:
            question (str): 需要询问的问题（必须），例如"请描述图片内容","这个图片是啥"
            img_path (str): 图像路径（可选），如果为空时是获取剪切板的图片，
                - 如果要填写路径, 只支持jpg, jpeg格式, 比如 'C:/Users/用户名/Desktop/图片.jpg'
        Returns:
            dict: 返回图像描述或错误信息，包含以下字段：
                - success (bool): 操作是否成功
                - result (str): 识别结果或错误信息
        """
        if not img_path:
            logger.info("开始获取剪切板图片...")
            clipboard_result = get_image()
            if not clipboard_result.get("success", False):
                error_msg = f"获取剪切板图片失败: {clipboard_result.get('result', '未知错误')}"
                logger.error(error_msg)
                return {"success": False, "result": error_msg}
            msg = identify_description(question, clipboard_result["result"])
            return msg
        msg = identify_description(question, img_path)
        return msg