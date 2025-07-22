import time
import logging
import platform
import pyautogui
import pyperclip
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('输入文本')

def input_content_by_mouse_position(mcp: FastMCP):
    @mcp.tool()
    def input_content_by_mouse_position(text, interval=0.003) -> str:
        """鼠标位置输入（写入）文本（文字）
        Use:
            1.用户需要输入（写入）文本时，立刻调用该工具
                比如:
                    1.用户需要写入内容
                    2.用户说帮我写出来
                    3.用户说输入内容
            2.用户如果需要模拟输入字符串，比如输入“Hello”，立刻使用此工具。
        Args:
            text (str): 要输入的文本（可包含中文）
            interval (float): 每个字符之间的固定间隔（秒）
        Returns:
            str: 输入完成后的文本
        """
        logger.info(f"开始输入文本 {text} ...")
        # 记录当前剪贴板内容，结束后恢复
        original_clipboard = pyperclip.paste()
        x, y = pyautogui.position()
        text_len = len(text)
        try:
            # 逐字处理文本
            for char in text:
                # 将单个字符复制到剪贴板
                pyperclip.copy(char)
                # 根据系统使用对应的粘贴快捷键
                if platform.system() in ["Windows", "Linux"]:
                    pyautogui.hotkey('ctrl', 'v')
                elif platform.system() == "Darwin":  # macOS
                    pyautogui.hotkey('command', 'v')
                time.sleep(interval)
            msg = f"在鼠标位置 ({x}, {y}) 输入完成，共 {text_len} 个字符"
            logger.info(msg)
            return msg
        except Exception as e:
            msg = f"输入失败，错误信息: {str(e)}"
            logger.error(msg)
            return msg
        finally:
            # 恢复原始剪贴板内容
            pyperclip.copy(original_clipboard)