import logging
from mcp.server.fastmcp import FastMCP
from utils.application.window_order import (
    get_z_order_top_to_bottom,
    get_visible_windows,
)

logger = logging.getLogger('窗口列表')

def list_desktop_windows(mcp: FastMCP):
    @mcp.tool()
    def list_desktop_windows() -> dict:
        """获取桌面所有可见窗口的Z轴层级顺序（从上到下）及详细信息。

        使用场景：
            1.当需要查看当前打开了哪些窗口时，调用该工具查看
            2.当不确定要关闭哪个窗口时，先调用此工具查看窗口列表
            3.窗口列表按Z序从上到下排列，索引越小越靠上

        Returns:
            dict: 包含窗口列表的字典，格式为:
                {
                    "success": bool,
                    "total_windows": int,
                    "windows": [{"index": int, "title": str, "hwnd": int, "rect": [int, int, int, int]}]
                }
        """
        logger.info("获取桌面窗口Z轴层级顺序 ...")

        try:
            # 获取可见窗口完整列表
            all_windows = get_visible_windows()
            # 获取Z序（从上到下）
            z_order = get_z_order_top_to_bottom()

            window_list = []
            for i, (hwnd, title, rect) in enumerate(z_order, 1):
                window_list.append({
                    "index": i,
                    "title": title,
                    "hwnd": hwnd,
                    "rect": list(rect),
                })

            result = {
                "success": True,
                "total_windows": len(window_list),
                "windows": window_list,
            }
            logger.info(f"获取到 {len(window_list)} 个可见窗口")
            return result

        except Exception as e:
            msg = f"获取桌面窗口Z序时出错: {e}"
            logger.error(msg)
            return {
                "success": False,
                "total_windows": 0,
                "windows": [],
            }