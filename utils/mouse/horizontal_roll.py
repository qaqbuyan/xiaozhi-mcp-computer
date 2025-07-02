import logging
import pyautogui
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('鼠标水平移动')

def mouse_horizontal_move(mcp: FastMCP):
    @mcp.tool()
    def mouse_horizontal_move(is_left: bool = True, total_move: int = 100, duration: float = 0.25) -> dict:
        """
        模拟鼠标水平移动操作。包括向左移动和向右移动。当说鼠标向左或向右移动时，立刻使用该工具。
        参数:
            is_left (bool): 是否向左移动，True 表示向左，False 表示向右，默认为 True。
            total_move (int): 总移动量，默认为 100。
            duration (float): 移动用时，默认为 0.25 秒。
        返回:
            dict: 包含操作结果的字典，格式为:
                {
                    "success": bool,  # 操作是否成功
                    "result": str     # 结果消息
                }
        """
        try:
            logger.info(f"开始鼠标水平移动操作，移动方向: {'向左' if is_left else '向右'}，移动量: {total_move} 像素，用时: {duration} 秒")
            direction = -1 if is_left else 1
            pyautogui.moveRel(direction * total_move, 0, duration=duration)
            msg = f"成功完成鼠标水平移动操作，移动方向: {'向左' if is_left else '向右'}，移动量: {total_move} 像素，用时: {duration} 秒"
            logger.info(msg)
            return {"success": True, "result": msg}
        except Exception as e:
            error_msg = f"鼠标水平移动过程中出错: {e}"
            logger.error(error_msg)
            return {"success": False, "result": error_msg}