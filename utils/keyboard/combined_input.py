import pyautogui
import time
import logging
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('键盘模拟')

def keyboard_operations(mcp: FastMCP):
    @mcp.tool()
    def keyboard_operations(input_value: str, is_key_press: bool = True) -> dict:
        """
        用于模拟键盘操作，包括按键和输入字符串。
        当需要模拟按下某个键或输入一段字符串时，使用此工具，比如：
            说到“按A键”、“关闭标签页”（'ctrl+w'）、“输入Hello”等。
        注意：
        - 输入字符串时，需要确保输入的字符串是合法的，避免输入非法字符或命令。
        Args:
            input_value (str): 模拟按下的键或要输入的字符串。可以为单个键（如 'a'），也可以是多个键的组合（如 'ctrl+a'）。
            is_key_press (bool): 默认为 True，表示按键操作；False 表示模拟输入字符串。
        Returns:
            dict: 包含操作结果的字典，格式为:
                {
                    "success": bool,  # 操作是否成功
                    "result": str     # 结果消息
                }
        """
        try:
            logger.info(f"开始执行键盘操作，输入值: {input_value}，操作类型: {'按键' if is_key_press else '输入字符串'}")
            if is_key_press:
                if '+' in input_value:
                    keys = [key.strip() for key in input_value.split('+')]
                    pyautogui.hotkey(*keys)
                else:
                    pyautogui.press(input_value)
                msg = f"成功模拟按下键: {input_value}"
            else:
                pyautogui.typewrite(input_value)
                msg = f"成功模拟输入字符串: {input_value}"
            logger.info(msg)
            return {"success": True, "result": msg}
        except Exception as e:
            msg = f"执行键盘操作时出错: {e}"
            logger.error(msg)
            return {"success": False, "result": msg}