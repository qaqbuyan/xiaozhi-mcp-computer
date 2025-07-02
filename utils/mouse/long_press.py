import logging
import pyautogui
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('鼠标长按')

def mouse_long_press(mcp: FastMCP):
    @mcp.tool()
    def mouse_long_press(click_type: str = "left", duration= 2 ) -> dict:
        """
        模拟鼠标长按操作。包括左键长按、右键长按、中键长按、取消长按。
            当说鼠标长按时，使用该工具，默认持续时间为 2 秒。
            当说鼠标长按锁定时，使用该工具，持续长按。
            当说取消鼠标长按时，使用该工具，取消之前的长按。
        参数:
            click_type (str): 点击类型，可选值为：
                "left"（左键）、
                "right"（右键）、
                "middle"（中键），
                默认为 "left"。
            duration (int, bool): 长按的时长（秒），默认值为 2 秒。
                如果为 True 则一直长按，如果为 False 则取消之前的长按。
        返回:
            dict: 包含操作结果的字典，格式为:
                {
                    "success": bool,  # 操作是否成功
                    "result": str     # 结果消息
                }
        """
        try:
            if isinstance(duration, bool):
                if duration:
                    logger.info(f"开始鼠标 {click_type} 长按锁定")
                else:
                    logger.info(f"开始取消鼠标 {click_type} 长按")
            else:
                logger.info(f"开始鼠标 {click_type} 长按 {duration} 秒")
            if isinstance(duration, bool):
                if duration:
                    if click_type == "left":
                        pyautogui.mouseDown(button='left')
                    elif click_type == "right":
                        pyautogui.mouseDown(button='right')
                    elif click_type == "middle":
                        pyautogui.mouseDown(button='middle')
                    else:
                        error_msg = f"不支持的点击类型: {click_type}，请使用 'left', 'right' 或 'middle'。"
                        logger.error(error_msg)
                        return {"success": False, "result": error_msg}
                    msg = f"成功开始鼠标 {click_type} 长按"
                    logger.info(msg)
                    return {"success": True, "result": msg}
                else:
                    if click_type == "left":
                        pyautogui.mouseUp(button='left')
                    elif click_type == "right":
                        pyautogui.mouseUp(button='right')
                    elif click_type == "middle":
                        pyautogui.mouseUp(button='middle')
                    else:
                        error_msg = f"不支持的点击类型: {click_type}，请使用 'left', 'right' 或 'middle'。"
                        logger.error(error_msg)
                        return {"success": False, "result": error_msg}
                    msg = f"成功取消鼠标 {click_type} 长按"
                    logger.info(msg)
                    return {"success": True, "result": msg}
            elif isinstance(duration, (int, float)):
                if click_type == "left":
                    pyautogui.mouseDown(button='left')
                elif click_type == "right":
                    pyautogui.mouseDown(button='right')
                elif click_type == "middle":
                    pyautogui.mouseDown(button='middle')
                else:
                    error_msg = f"不支持的点击类型: {click_type}，请使用 'left', 'right' 或 'middle'。"
                    logger.error(error_msg)
                    return {"success": False, "result": error_msg}
                if click_type == "left":
                    pyautogui.mouseUp(button='left')
                elif click_type == "right":
                    pyautogui.mouseUp(button='right')
                elif click_type == "middle":
                    pyautogui.mouseUp(button='middle')
                msg = f"成功完成鼠标 {click_type} 长按 {duration} 秒"
                logger.info(msg)
                return {"success": True, "result": msg}
            else:
                error_msg = f"不支持的 duration 类型: {type(duration).__name__}，请使用 int, float 或 bool 类型。"
                logger.error(error_msg)
                return {"success": False, "result": error_msg}
        except Exception as e:
            error_msg = f"鼠标长按操作过程中出错: {e}"
            logger.error(error_msg)
            return {"success": False, "result": error_msg}