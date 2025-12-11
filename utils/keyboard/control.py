import logging
import pyautogui
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('键盘控制')

def control_key_operations(mcp: FastMCP):
    @mcp.tool()
    def control_key(input_value: str, long_press: bool = True) -> dict:
        """控制键盘按键的按下和松开。
        当需要模拟键盘按键操作时，立刻调用该工具，
        工具会执行相应的按键操作
        Args:
            input_value (str): 模拟按下的键（必须）
            long_press (bool): 按键操作类型，为 True 则一直长按，如果为 False 则取消之前的长按（可选，默认为True）
        Returns:
            dict: 返回操作结果或错误信息，包含以下字段：
                - success (bool): 操作是否成功
                - result (str): 操作结果或错误信息
        """
        try:
            logger.info(f"开始执行键盘控制操作，输入值: {input_value}，操作类型: {'长按' if long_press else '松开'}")
            if long_press:
                pyautogui.keyDown(input_value)
                msg = f"成功长按键: {input_value}"
            else:
                pyautogui.keyUp(input_value)
                msg = f"成功松开键: {input_value}"
            logger.info(msg)
            return {"success": True, "result": msg}
        except Exception as e:
            msg = f"执行键盘控制操作时出错: {e}"
            logger.error(msg)
            return {"success": False, "result": msg}