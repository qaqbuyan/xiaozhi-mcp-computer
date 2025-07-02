import win32gui

def get_window_active(window_title: str) -> bool:
    """检查指定标题的窗口是否为活动窗口"""
    active_window = win32gui.GetForegroundWindow()
    return window_title.lower() in win32gui.GetWindowText(active_window).lower()