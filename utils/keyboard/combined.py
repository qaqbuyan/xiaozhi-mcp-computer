import logging
import pyautogui
from mcp.server.fastmcp import FastMCP
from handle.missing_params import ask_on_missing

logger = logging.getLogger('组合键输入')

def keyboard_operations(mcp: FastMCP):
    @mcp.tool()
    @ask_on_missing('keys')
    def combinatorial_input(keys: str = None) -> dict:
        """组合键输入（如 Ctrl+C、Alt+Tab、Win+D 等快捷键组合）
        Use:
            用户需要模拟按下键盘组合键（快捷键）时，立刻调用该工具。
            例如：
                1. 复制内容 -> Ctrl+C
                2. 粘贴内容 -> Ctrl+V
                3. 切换窗口 -> Alt+Tab
                4. 显示桌面 -> Win+D
                5. 全选 -> Ctrl+A
                6. 撤销 -> Ctrl+Z
        Args:
            keys (str): 组合键字符串，多个键之间用加号连接，如 "ctrl+c"、"alt+tab"、"win+d"
        Returns:
            dict: 包含操作结果或错误信息
        """
        try:
            logger.info(f"开始执行组合键输入: {keys}")
            # 解析键名，多个键以加号分隔
            key_list = [k.strip().lower() for k in keys.split('+')]
            pyautogui.hotkey(*key_list)
            msg = f"成功执行组合键: {keys}"
            logger.info(msg)
            return {"success": True, "result": msg}
        except Exception as e:
            msg = f"执行组合键输入时出错: {e}"
            logger.error(msg)
            return {"success": False, "result": msg}