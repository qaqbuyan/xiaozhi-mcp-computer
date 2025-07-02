import win32gui

def find_window_by_title(window_title: str) -> int:
    """查找包含指定标题的窗口句柄"""
    hwnd = 0
    def callback(hwnd, ctx):
        nonlocal window_title
        if win32gui.IsWindowVisible(hwnd) and window_title.lower() in win32gui.GetWindowText(hwnd).lower():
            ctx.append(hwnd)
        return True
    windows = []
    win32gui.EnumWindows(callback, windows)
    return windows[0] if windows else 0