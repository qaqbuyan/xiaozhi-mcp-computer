import re
import logging
import pyperclip
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('剪切板内容')

def get_clipboard_content(mcp: FastMCP):
    @mcp.tool()
    def get_clipboard_content() -> str:
        """用于获取剪切板内容，当需要获取剪切板内容时，立刻使用该工具。
        比如我说看一下这个内容或者说复制了什么，你就会使用这个工具，直接返回剪切板内容给用户。
        注意：之前使用了这个工具就忘记它，进行重新调用。
        """
        try:
            logger.info("开始获取剪切板内容...")
            content = pyperclip.paste()
            # 去除换行符
            content = content.replace('\n', '').replace('\r', '')
            # 多个连续空格只保留一个
            content = re.sub(r'\s+', ' ', content)
            if not content.strip():
                msg = "剪切板没有有效内容"
                logger.info(msg)
                return msg
            logger.info(f"获取到剪切板内容: {content}")
            return content
        except Exception as e:
            msg = f"获取剪切板内容时出错: {e}"
            logger.error(msg)
            return msg