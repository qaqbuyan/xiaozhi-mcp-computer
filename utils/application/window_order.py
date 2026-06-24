import logging
import win32gui
import win32con
from typing import List, Tuple, Optional

logger = logging.getLogger('窗口Z序')

# ANSI 颜色定义
class _C:
    RST = '\033[0m'
    YLW = '\033[33m'     # 黄色
    BWHT = '\033[1;37m'  # 亮白色
    GRN = '\033[32m'     # 绿色
    BLU = '\033[34m'     # 蓝色
    CYN = '\033[36m'     # 青色

# 系统级窗口类名（不可关闭）
_SYSTEM_CLASSES = {
    'Progman',       # 桌面图标层
    'WorkerW',       # 桌面壁纸层
    'Shell_TrayWnd', # 任务栏
    'TrayNotifyWnd', # 通知区域
    'NotifyIconOverflowWindow', # 通知区域溢出
    'WindowsShell',  # Windows Shell
    'Shell_SecondaryTrayWnd',  # 副任务栏
}

# 程序自身窗口标题前缀（禁止关闭）
_PROTECTED_TITLE_PREFIX = "小智控制电脑 V"

def is_system_window(hwnd: int) -> bool:
    """判断是否为系统级窗口（桌面、任务栏等不可关闭的窗口）"""
    class_name = win32gui.GetClassName(hwnd)
    return class_name in _SYSTEM_CLASSES

def get_visible_windows() -> List[Tuple[int, str, Tuple[int, int, int, int]]]:
    """获取桌面所有可见窗口（按Z序从底层到顶层）

    Returns:
        List[(hwnd, title, rect)]: 窗口句柄、标题、位置矩形
    """
    windows = []
    hwnd = win32gui.GetWindow(win32gui.GetDesktopWindow(), win32con.GW_CHILD)
    while hwnd:
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and not is_system_window(hwnd) and not title.startswith(_PROTECTED_TITLE_PREFIX):
                rect = win32gui.GetWindowRect(hwnd)
                windows.append((hwnd, title, rect))
        hwnd = win32gui.GetWindow(hwnd, win32con.GW_HWNDNEXT)
    return windows

def get_z_order_top_to_bottom() -> List[Tuple[int, str, Tuple[int, int, int, int]]]:
    """获取桌面窗口Z轴层级顺序（从上到下）

    注意事项：
        1. 桌面（Progman/WorkerW）、任务栏（Shell_TrayWnd）等系统窗口已过滤
        2. 有些程式会弹出「是否要保存」的确认对话框，WM_CLOSE 只会弹出对话框
        3. 多标签页窗口（如浏览器）WM_CLOSE 可能只关当前标签页
        4. 需要管理员权限才能关闭某些系统级窗口

    Returns:
        List[(hwnd, title, rect)]: 从上到下的窗口列表
    """
    windows = get_visible_windows()
    # GW_CHILD 获取的是最底层，反转得到最上层
    z_order = list(reversed(windows))

    # 打印窗口列表日志（带颜色：编号=黄色，标题=亮白，句柄=绿色，位置=蓝色）
    header = f"当前桌面窗口顺序（从上到下共{len(z_order)}个）："
    sep = f"{'─'*60}"
    col_header = (
        f"{_C.YLW}编号{_C.RST}  "
        f"{_C.BWHT}标题{_C.RST}  "
        f"{_C.GRN}|  {_C.GRN}句柄{_C.RST}  "
        f"{_C.GRN}|  {_C.GRN}位置{_C.RST}"
    )
    items = [
        f"{_C.YLW}{i:>2}.{_C.RST} "
        f"{_C.BWHT}{title}{_C.RST}  "
        f"{_C.GRN}|{_C.RST}  {_C.GRN}{hwnd}{_C.RST}  "
        f"{_C.GRN}|{_C.RST}  {_C.BLU}{rect}{_C.RST}"
        for i, (hwnd, title, rect) in enumerate(z_order, 1)
    ]
    logger.info("\n".join([header, sep, col_header] + items))

    return z_order

def close_window(hwnd: int) -> bool:
    """向窗口发送关闭消息

    Returns:
        bool: 是否成功发送关闭消息
    """
    try:
        title = win32gui.GetWindowText(hwnd)
        if title.startswith(_PROTECTED_TITLE_PREFIX):
            logger.warning(f"禁止关闭程序自身窗口：{title}")
            return False
        win32gui.SendMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        logger.info(f"已向窗口发送关闭消息：{title} (句柄：{hwnd})")
        return True
    except Exception as e:
        logger.error(f"关闭窗口失败：{e}")
        return False