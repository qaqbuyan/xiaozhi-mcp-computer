import win32gui
import win32con
import logging
from mcp.server.fastmcp import FastMCP
from utils.application.find_title import find_window_by_title
from utils.application.check_activity import get_window_active

logger = logging.getLogger('设置窗口状态')

def set_window_active_tool(mcp: FastMCP):
    @mcp.tool()
    def set_window_active(window_title: str) -> dict:
        """
        设置指定标题的窗口为活动状态
        Args:
            window_title: 窗口标题（部分匹配），例如 "笔记.txt"
        Returns:
            dict: 包含操作结果的字典，格式为:
                {
                    "success": bool,  # 是否成功
                    "result": str   # 结果消息
                }
        """
        logger.info(f"尝试设置窗口 '{window_title}' 为活动状态 ...")
        try:
            # 检查窗口是否已激活
            if get_window_active(window_title):
                msg = f"窗口 '{window_title}' 已经是活动状态"
                logger.info(msg)
                return {"success": True, "result": msg}
            # 查找窗口句柄
            hwnd = find_window_by_title(window_title)
            if hwnd == 0:
                msg = f"未找到窗口: {window_title}"
                logger.info(msg)
                return {"success": False, "result": msg}
            # 确保窗口未最小化
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            # 设置为活动窗口
            win32gui.SetForegroundWindow(hwnd)
            active_window_title = win32gui.GetWindowText(hwnd)
            msg = f"已激活窗口: {active_window_title}"
            logger.info(msg)
            return {"success": True, "result": msg}
        except Exception as e:
            msg = f"激活窗口时出错: {str(e)}"
            logger.error(msg)
            return {"success": False, "result": msg}