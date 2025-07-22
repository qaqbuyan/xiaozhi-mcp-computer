import time
import logging
import pyautogui
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('键盘模拟')

def keyboard_operations(mcp: FastMCP):
    @mcp.tool()
    def keyboard_operations(input_value: str, is_key_press: bool = True) -> dict:
        """用于模拟键盘操作，包括按键(组合键)和输入字符串。
        组合键：
            1.组合键的格式为：'ctrl+a'，表示同时按下 ctrl 和 a 键。
            2.组合键的顺序不影响结果，例如 'ctrl+a' 和 'a+ctrl' 是等效的。
            3.组合键可以包含多个键，例如 'ctrl+alt+del'。
        Use:
            1.用户当需要模拟按下某个键或组合键时，立刻使用此工具，比如：
            说到“按A键”、“关闭标签页”（ctrl+w）、“按回车键”（enter）等。
        Notice：
            1.输入字符串时，需要确保输入的字符串是合法的，避免输入非法字符或命令。
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