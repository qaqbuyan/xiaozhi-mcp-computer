import logging
from mcp.server.fastmcp import FastMCP
from handle.missing_params import ask_on_missing
from handle.notification import send_notification

logger = logging.getLogger('通知工具')

def register_notification_tool(mcp: FastMCP):
    """注册系统通知工具"""
    @mcp.tool()
    @ask_on_missing('title', 'message', 'timeout')
    def send_system_notification(title: str, message: str, timeout: int = 5) -> dict:
        """发送系统托盘通知。
        当需要主动向用户显示右下角系统通知时，立刻使用该工具。

        Args:
            title (str): 通知标题
            message (str): 通知内容
            timeout (int): 显示时长（秒），默认 5 秒

        Returns:
            dict: 包含 success 和 result 的字典
        """
        try:
            send_notification(title, message, timeout)
            logger.info(f"已发送通知: {title} - {message}")
            return {"success": True, "result": "通知已发送"}
        except Exception as e:
            logger.error(f"发送通知失败: {str(e)}")
            return {"success": False, "result": f"发送通知失败: {str(e)}"}