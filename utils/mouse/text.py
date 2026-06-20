import time
import threading
import logging
import platform
import pyautogui
import pyperclip
from mcp.server.fastmcp import FastMCP
from utils.missing_params import ask_on_missing

logger = logging.getLogger('输入文本')

# 最大允许执行时间（毫秒），超过则使用直接粘贴
MAX_EXECUTION_TIME_MS = 1000
# 单字符输入的预估耗时（毫秒），包含 pyperclip.copy + pyautogui.hotkey + time.sleep
# 实际耗时因系统性能而异，此处取保守平均值
CHAR_INPUT_TIME_MS = 30

# 防重复输入：记录当前正在输入的文本
_pending_text = None
_pending_text_lock = threading.Lock()


def _get_paste_keys():
    """根据操作系统返回粘贴快捷键"""
    if platform.system() in ["Windows", "Linux"]:
        return ['ctrl', 'v']
    elif platform.system() == "Darwin":  # macOS
        return ['command', 'v']
    return ['ctrl', 'v']


def input_content_by_mouse_position(mcp: FastMCP):
    @mcp.tool()
    @ask_on_missing('text')
    def input_content_by_mouse_position(text=None, force: bool = False) -> str:
        """鼠标位置输入（写入）文本（文字）
        Use:
            1.用户需要输入（写入）文本时，立刻调用该工具
                比如:
                    1.用户需要写入内容
                    2.用户说帮我写出来
                    3.用户说输入内容
            2.用户如果需要模拟输入字符串，比如输入"Hello"，立刻使用此工具。
        Args:
            text (str): 要输入的文本（可包含中文，英文，字符串，数字等）
            force (bool): 是否强制重复输入。为true时即使相同文本正在输入也重新执行；
                          为false时如果相同文本正在输入则跳过并提示用户确认。
                          默认为false。
        Returns:
            str: 输入完成后的文本
        """
        logger.info(f"开始输入文本 {text} ...")

        # 防重复检测（非强制模式）
        if not force:
            with _pending_text_lock:
                if _pending_text is not None and _pending_text == text:
                    msg = (
                        f"文本内容已在输入中，确认需要再次输入相同的内容吗？"
                        f"如果需要强制重复输入，请设置 force=true 后重试。"
                    )
                    logger.info(msg)
                    return msg

        # 记录当前正在输入的文本
        with _pending_text_lock:
            _pending_text = text

        # 记录当前剪贴板内容，结束后恢复
        original_clipboard = pyperclip.paste()
        x, y = pyautogui.position()
        text_len = len(text)
        paste_keys = _get_paste_keys()
        try:
            # 预估逐字输入总耗时（包含固定函数开销 ~30ms）
            estimated_time_ms = text_len * CHAR_INPUT_TIME_MS + 30
            logger.info(
                f"文本长度 {text_len}，预估逐字输入耗时 {estimated_time_ms}ms，"
                f"最大允许 {MAX_EXECUTION_TIME_MS}ms"
            )

            if estimated_time_ms > MAX_EXECUTION_TIME_MS:
                # 预估超过时间限制 → 直接粘贴整个文本
                logger.info(f"预估耗时超出限制，使用直接粘贴方式")
                pyperclip.copy(text)
                pyautogui.hotkey(*paste_keys)
            else:
                # 在时间限制内 → 逐字输入（打字效果）
                logger.info(f"预估耗时在限制内，使用逐字输入方式")
                for char in text:
                    pyperclip.copy(char)
                    pyautogui.hotkey(*paste_keys)
                    time.sleep(0.002)

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
            # 清除待输入标记
            with _pending_text_lock:
                _pending_text = None