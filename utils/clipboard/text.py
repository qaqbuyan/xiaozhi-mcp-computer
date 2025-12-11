import re
import logging
import pyperclip
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('剪切板文字')

def get_clipboard_text(mcp: FastMCP):
    @mcp.tool()
    def get_clipboard_text() -> str:
        """用于获取剪切板文字，当需要获取剪切板文字时，立刻使用该工具。
        如果用户需要询问图像(剪切板的图片)中的信息时，立刻调用'get_image_description'工具，
        比如用户说看一下这个剪切板内容或者复制的文字，就使用这个工具，直接返回剪切板内容给用户。
        """
        try:
            logger.info("开始获取剪切板文字...")
            content = pyperclip.paste()
            # 去除换行符
            content = content.replace('\n', '').replace('\r', '')
            # 多个连续空格只保留一个
            content = re.sub(r'\s+', ' ', content)
            if not content.strip():
                msg = "剪切板没有有效文字"
                logger.info(msg)
                return msg
            logger.info(f"获取到剪切板文字: {content}")
            return content
        except Exception as e:
            msg = f"获取剪切板内容时出错: {e}"
            logger.error(msg)
            return msg