import logging
import webbrowser
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('打开网站')

def open_website(mcp: FastMCP):
    @mcp.tool()
    def open_website(url: str) -> dict:
        """
        用于打开指定的网站URL，
        当需要帮忙打开网页或打开网站时，立刻使用该工具
        比如我说打开百度，你就会使用这个工具
        这里面有一些常见的网站：
        1. 博客 或 blog：https://qaqbuyan.com:88
        2. 数据库管理：http://qaqbuyan.console.google.com
        3. 集群控制台：http://qaqbuyan.console.google.com/webssh
        4. 集群磁盘：http://qaqbuyan.console.google.com:8080/files/media/buyan/
        5. 站点管理：http://qaqbuyan.console.google.com:8080/files/www/website/
        args:
            url (str): 要打开的网站URL,
            比如：https://qaqbuyan.com:88 ，必须为完整的URL
        """
        try:
            logger.info(f"尝试打开网站: {url}")
            webbrowser.open(url)
            msg = f"已打开网站: {url}"
            logger.info(msg)
            return {"success": True, "result": msg}
        except Exception as e:
            msg = f"打开网站时出错: {e}"
            logger.error(msg)
            return {"success": False, "result": msg}