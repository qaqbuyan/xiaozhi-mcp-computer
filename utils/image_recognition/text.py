import logging
from mcp.server.fastmcp import FastMCP
from utils.image_recognition.identify import identify_image_text_coordinates

logger = logging.getLogger('图像文字识别')

def get_image_recognition_text(mcp: FastMCP):
    """图像识别文字坐标工具"""
    @mcp.tool()
    def get_image_recognition_text(image: str, timeout: int = 15) -> dict:
        """用于识别图像中的文字以及坐标
        用户需要识别图像中的文字或者及坐标时，立刻调用该工具，
        工具会返回图像中的文字以及坐标
        Args:
            image (str): 图像文件的路径, 支持png, jpg, jpeg, gif，比如 'C:/Users/用户名/Desktop/图片.png'
            timeout (int): 超时时间，单位秒，默认15秒
        Returns:
            dict: 返回识别结果或错误信息
        """
        logger.info("开始执行操作...")
        msg = identify_image_text_coordinates(image, timeout)
        logger.info("执行完成")
        return msg