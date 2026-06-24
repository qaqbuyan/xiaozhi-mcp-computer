import logging
from mcp.server.fastmcp import FastMCP
from handle.missing_params import ask_on_missing
from utils.application.window_order import (
    get_z_order_top_to_bottom,
    close_window,
    _PROTECTED_TITLE_PREFIX,
)

logger = logging.getLogger('关闭窗口')

def close_top_window(mcp: FastMCP):
    @mcp.tool()
    @ask_on_missing('target_title')
    def close_top_window(target_title: str = None) -> dict:
        """按桌面窗口Z轴层级顺序（从上到下）关闭窗口，每次调用只关闭一个窗口。

        使用场景：
            1.当你需要关闭某个窗口/程序，但不知道具体程序名时，先调用 list_desktop_windows 查看窗口层级
            2.当你已经知道窗口层级时，直接调用本工具关闭指定窗口
            3.当需要逐个关闭窗口直到关掉目标窗口时，反复调用本工具

        关闭规则：
            - 如果提供了 target_title：在所有可见窗口中按标题模糊匹配，关闭匹配到的窗口
            - 如果未提供 target_title：直接关闭当前最顶层的窗口
            - 每次调用只关闭一个窗口
            - ⚠️ **如果你是关闭第一个窗口（最顶层窗口），直接调用本工具即可，不需要先调用 list_desktop_windows**
            - ⚠️ **如果你已经知道要关闭的窗口标题，直接传入 target_title 即可，不需要先调用 list_desktop_windows**

        询问用户规则：
            - ⚠️ **如果你不知道用户要关闭的窗口标题，先调用 list_desktop_windows 查看当前窗口列表**
            - ⚠️ **通过 list_desktop_windows 获取到窗口标题后，再传入 target_title 调用本工具关闭**
            - ⚠️ **禁止在不知道用户意图的情况下擅自关闭最顶层窗口！除非用户明确表达了关闭最顶层窗口的意图**

        注意事项：
            1. 系统窗口（桌面、任务栏等）已被过滤，不会被关闭
            2. 有些程序会弹出「是否保存」对话框，WM_CLOSE 只弹出对话框，需要手动处理
            3. 多标签页程序（如浏览器）WM_CLOSE 可能只关闭当前标签页
            4. 建议先调用 list_desktop_windows 查看窗口信息，确认后再关闭

        Args:
            target_title (str): 要关闭的窗口标题关键词，如果不确定用户要关闭哪个窗口，必须询问用户获取窗口标题后再调用
        Returns:
            dict: 包含操作结果的字典，格式为:
                {
                    "success": bool,  # 是否成功
                    "result": str,   # 结果消息
                    "closed_window": str,  # 被关闭的窗口标题（有关闭时）
                    "z_order_list": [{"index": int, "title": str, "hwnd": int, "rect": [int, int, int, int]}],  # 当前Z序列表
                }
        """
        logger.info(f"开始按Z序关闭窗口，目标: {target_title or '最顶层窗口'} ...")

        try:
            # 获取当前Z序（从上到下）
            z_order = get_z_order_top_to_bottom()

            if not z_order:
                msg = "当前没有可关闭的可见窗口"
                logger.info(msg)
                return {
                    "success": False,
                    "result": msg,
                    "closed_window": "",
                    "z_order_list": [],
                }

            # 构造窗口列表信息（供AI参考）
            z_list = []
            for i, (hwnd, title, rect) in enumerate(z_order, 1):
                z_list.append({
                    "index": i,
                    "title": title,
                    "hwnd": hwnd,
                    "rect": list(rect),
                })

            if target_title:
                # 模糊匹配目标标题
                target_lower = target_title.lower()
                matched = [
                    (hwnd, title, rect) for hwnd, title, rect in z_order
                    if target_lower in title.lower()
                ]
                if not matched:
                    msg = f"未找到标题包含「{target_title}」的窗口，当前窗口Z序共 {len(z_order)} 个"
                    logger.info(msg)
                    return {
                        "success": False,
                        "result": msg,
                        "closed_window": "",
                        "z_order_list": z_list,
                    }
                # 关闭匹配到的第一个（Z序最靠上的）
                hwnd, title, rect = matched[0]
                # 检查是否为程序自身窗口，禁止关闭
                if title.startswith(_PROTECTED_TITLE_PREFIX):
                    msg = f"禁止关闭程序自身窗口：{title}"
                    logger.warning(msg)
                    return {
                        "success": False,
                        "result": msg,
                        "closed_window": "",
                        "z_order_list": z_list,
                    }
                logger.info(f"匹配到窗口：{title} (句柄: {hwnd})，准备关闭")
            else:
                # 未指定目标，关闭最顶层窗口
                if not z_order:
                    msg = "当前没有可关闭的可见窗口"
                    return {
                        "success": False,
                        "result": msg,
                        "closed_window": "",
                        "z_order_list": z_list,
                    }
                hwnd, title, rect = z_order[0]

            # 发送关闭消息
            result = close_window(hwnd)
            if result:
                msg = f"已关闭窗口: {title}"
                logger.info(msg)
                return {
                    "success": True,
                    "result": msg,
                    "closed_window": title,
                    "z_order_list": z_list,
                }
            else:
                msg = f"关闭窗口失败: {title}（可能需要管理员权限或该窗口无法通过消息关闭）"
                logger.error(msg)
                return {
                    "success": False,
                    "result": msg,
                    "closed_window": "",
                    "z_order_list": z_list,
                }

        except Exception as e:
            msg = f"按Z序关闭窗口时出错: {e}"
            logger.error(msg)
            return {
                "success": False,
                "result": msg,
                "closed_window": "",
                "z_order_list": [],
            }