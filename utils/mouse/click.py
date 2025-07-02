import time
import logging
import pyautogui
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('鼠标点击')

def mouse_click(mcp: FastMCP):
    @mcp.tool()
    def mouse_click(click_type: str = "left") -> dict:
        """
        模拟鼠标点击操作。包括左键点击、右键点击、中键点击、前进键和后退键。当说点击鼠标左键、右键、中键、前进或后退时，立刻使用该工具。
        参数:
            click_type (str): 点击类型，可选值为：
            "left"（左键）、
            "right"（右键）、
            "middle"（中键）、
            "back"（后退）、
            "forward"（前进），
            默认为 "left"。
        返回:
            dict: 包含操作结果的字典，格式为:
                {
                    "success": bool,  # 操作是否成功
                    "result": str     # 结果消息
                }
        """
        try:
            logger.info(f"开始鼠标点击操作，点击类型: {click_type}")
            if click_type == "left":
                pyautogui.click(button='left')
            elif click_type == "right":
                pyautogui.click(button='right')
            elif click_type == "middle":
                pyautogui.click(button='middle')
            elif click_type == "back":
                pyautogui.hotkey('alt', 'left')  # 模拟鼠标后退
            elif click_type == "forward":
                pyautogui.hotkey('alt', 'right')  # 模拟鼠标前进
            else:
                error_msg = f"不支持的点击类型: {click_type}，请使用 'left', 'right', 'middle', 'back' 或 'forward'。"
                logger.error(error_msg)
                return {"success": False, "result": error_msg}
            
            msg = f"成功完成鼠标 {click_type} 操作"
            logger.info(msg)
            return {"success": True, "result": msg}
        except Exception as e:
            error_msg = f"鼠标操作过程中出错: {e}"
            logger.error(error_msg)
            return {"success": False, "result": error_msg}