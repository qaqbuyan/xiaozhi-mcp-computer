import logging
import pyautogui
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('鼠标滚动')

def mouse_up_and_down_move(mcp: FastMCP):
    @mcp.tool()
    def mouse_up_and_down_move(is_downward: bool = True, total_scroll: int = 2000, step_size: int = 100) -> dict:
        """
        模拟鼠标滚轮滚动操作。包括向下滚动和向上滚动。当说滚动，向下滑或向上滑时，立刻使用该工具。
        参数:
            is_downward (bool): 是否向下滚动，True 表示向下，False 表示向上，默认为 True。
            total_scroll (int): 总滚动量，默认为 2000。
            step_size (int): 每次滚动步长，默认为 100。
        返回:
            dict: 包含操作结果的字典，格式为:
                {
                    "success": bool,  # 操作是否成功
                    "result": str     # 结果消息
                }
        """
        try:
            logger.info(f"开始鼠标滚动操作，总滚动量: {total_scroll}，步长: {step_size}，滚动方向: {'向下' if is_downward else '向上'}")
            direction = -1 if is_downward else 1
            for _ in range(0, total_scroll, step_size):
                pyautogui.scroll(direction * step_size)
            msg = f"成功完成鼠标滚动操作，滚动方向: {'向下' if is_downward else '向上'}"
            logger.info(msg)
            return {"success": True, "result": msg}
        except Exception as e:
            error_msg = f"鼠标滚动过程中出错: {e}"
            logger.error(error_msg)
            return {"success": False, "result": error_msg}