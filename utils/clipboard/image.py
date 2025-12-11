import logging
from mcp.server.fastmcp import FastMCP
from utils.clipboard.get_image import get_image

logger = logging.getLogger('剪切板图片')

def get_clipboard_image(mcp: FastMCP):
    @mcp.tool()
    def get_clipboard_image() -> dict:
        """用于获取剪切板图片，当需要获取剪切板图片时，立刻使用该工具。
        比如用户说看一下这个剪切板图片或者复制的图片，立刻使用这个工具，
        如果用户需要图片的文字内容，立刻使用 'get_image_recognition_text' 工具获取图片的文字内容。
        返回包含是否成功和结果的字典。
        """
        logger.info("开始执行操作...")
        msg = get_image()
        logger.info("执行完成")
        return msg