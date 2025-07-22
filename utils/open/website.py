import logging
import webbrowser
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('打开网站')

def open_website(mcp: FastMCP):
    @mcp.tool()
    def open_website(url: str) -> dict:
        """用于打开指定的网站URL。
        当需要帮忙打开网页或打开网站时，立刻使用该工具
        比如用户说打开百度，你就会使用这个工具
        Notice：
            1. 如果需要打开的网站是未知网站或者不存在的URL，
                立刻使用‘get_browser_bookmarks’书签工具获取书签，如果得到链接，再立刻使用该工具打开
                如果没有在书签工具中得到链接，提示用户该网站不存在，并要求用户提供URL
        args:
            url (str): 要打开的网站URL,比如：’https://qaqbuyan.com:88’ ，必须为完整的URL
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