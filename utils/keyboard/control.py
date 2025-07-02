import pyautogui
import time
import logging
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('键盘控制')

def control_key_operations(mcp: FastMCP):
    @mcp.tool()
    def control_key(input_value: str, long_press: bool = True) -> dict:
        """
        控制键盘按键的按下和松开。
        :param input_value: 模拟按下的键
        :param long_press: 为 True 则一直长按，如果为 False 则取消之前的长按
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