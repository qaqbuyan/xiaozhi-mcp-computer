import logging
import pyautogui
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('鼠标位置')

def get_mouse_position(mcp: FastMCP):
    @mcp.tool()
    def get_mouse_position() -> dict:
        """获取当前鼠标位置。
        返回:
            dict: 包含鼠标位置的字典，格式为:
                {
                    "success": bool,  # 操作是否成功
                    "x": int,         # 鼠标 X 坐标
                    "y": int,         # 鼠标 Y 坐标
                    "result": str     # 结果消息
                }
        """
        try:
            logger.info('开始获取鼠标位置...')
            current_x, current_y = pyautogui.position()
            msg = f"成功获取鼠标位置: X = {current_x}, Y = {current_y}"
            return {"success": True, "x": current_x, "y": current_y, "result": msg}
        except Exception as e:
            error_msg = f"获取鼠标位置过程中出错: {e}"
            return {"success": False, "x": 0, "y": 0, "result": error_msg}