import os
import sys
import uuid
import time
import ctypes
import logging
import threading
from ctypes import wintypes
from handle.loader import load_config

logger = logging.getLogger('系统通知')

# 同一进程内通知图标使用稳定 GUID 标识（见下方 _NOTIFY_GUID），
# 配合 NIF_GUID 避免任务栏图标不断累积

# Windows API 常量
NIM_ADD = 0x00000000
NIM_MODIFY = 0x00000001
NIM_DELETE = 0x00000002
NIF_GUID = 0x00000020
NIF_INFO = 0x00000010
NIF_ICON = 0x00000002
NIF_MESSAGE = 0x00000001
WM_USER = 0x0400
WM_NOTIFY_CALLBACK = WM_USER + 1

class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8),
    ]

class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uFlags", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("hIcon", wintypes.HANDLE),
        ("szTip", wintypes.WCHAR * 128),
        ("dwState", wintypes.DWORD),
        ("dwStateMask", wintypes.DWORD),
        ("szInfo", wintypes.WCHAR * 256),
        ("uVersion", wintypes.UINT),
        ("szInfoTitle", wintypes.WCHAR * 64),
        ("dwInfoFlags", wintypes.DWORD),
        ("guidItem", GUID),
        ("hBalloonIcon", wintypes.HANDLE),
    ]

# 进程级稳定的通知图标 GUID：同一 GUID 的图标在重复添加/修改时会被替换，
# 且进程退出时由系统自动清理，避免 NIM_DELETE 失败导致任务栏图标累积
_NOTIFY_UID = 1
_notify_lock = threading.Lock()
_NOTIFY_GUID = GUID()
_notify_uuid = uuid.UUID('6F1D2B30-5C4A-4E7E-9B1A-3C2D4E5F6070')
_NOTIFY_GUID.Data1 = _notify_uuid.time_low
_NOTIFY_GUID.Data2 = _notify_uuid.time_mid
_NOTIFY_GUID.Data3 = _notify_uuid.time_hi_version
_NOTIFY_GUID.Data4 = (wintypes.BYTE * 8)(
    *(
        bytes([_notify_uuid.clock_seq_hi_variant, _notify_uuid.clock_seq_low])
        + _notify_uuid.node.to_bytes(6, 'big')
    )
)

def get_icon_path():
    """自动获取图标路径，适配打包和开发环境"""
    if getattr(sys, 'frozen', False):
        # 打包环境（如 PyInstaller）
        base_path = sys._MEIPASS
    else:
        # 开发环境
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    icon_path = os.path.join(base_path, 'favicon.ico')
    return icon_path if os.path.exists(icon_path) else None

def _send_notification_impl(title: str, message: str, timeout: int, icon_path: str = None):
    """实际发送通知（在子线程中运行，不阻塞主进程）"""
    try:
        from win32api import GetModuleHandle, GetLastError
        from win32gui import (
            CreateWindow, DestroyWindow, PumpWaitingMessages,
            WNDCLASS, RegisterClass, UnregisterClass,
        )
    except ImportError:
        logger.warning("缺少 win32api/win32gui，无法发送系统通知")
        return

    hinst = None
    hwnd = None
    hIcon = None
    class_atom = None

    try:
        hinst = GetModuleHandle(None)
        # 使用唯一类名，避免多个通知同时运行时 RegisterClass 冲突
        class_name = f"NotifyWindowClass_{uuid.uuid4().hex}"
        wc = WNDCLASS()
        wc.lpfnWndProc = lambda hwnd, msg, wparam, lparam: 0
        wc.hInstance = hinst
        wc.lpszClassName = class_name
        class_atom = RegisterClass(wc)

        hwnd = CreateWindow(class_atom, class_name, 0, 0, 0, 0, 0, 0, 0, hinst, None)
        logger.info(f"创建窗口: {class_name},{hwnd}")

        Shell_NotifyIconW = ctypes.windll.shell32.Shell_NotifyIconW

        # 使用稳定 GUID 与固定 uID：同一进程内通知图标唯一，
        # 重复添加/修改时替换旧图标，避免 NIM_DELETE 失败时任务栏图标累积
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = hwnd
        nid.uID = _NOTIFY_UID
        nid.uFlags = NIF_MESSAGE | NIF_GUID
        nid.uCallbackMessage = WM_NOTIFY_CALLBACK
        nid.guidItem = _NOTIFY_GUID

        if icon_path:
            # 使用 ExtractIconW 加载 ico，比 LoadImage 在 Windows 通知中更稳定
            hIcon = ctypes.windll.shell32.ExtractIconW(0, icon_path, 0)
            if hIcon:
                nid.hIcon = hIcon
                nid.uFlags |= NIF_ICON

        # 串行处理通知，避免并发操作同一 GUID 图标导致状态错乱
        with _notify_lock:
            # 先清理可能残留的旧图标，保证通知图标不重复累积
            ctypes.windll.shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid))

            # 添加托盘图标
            if not Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid)):
                err = GetLastError()
                logger.warning(f"Shell_NotifyIconW NIM_ADD 失败，错误码={err}，通知未显示")
                return

            # 再发送气泡通知，这种方式在 Windows 10/11 上更稳定
            nid.uFlags |= NIF_INFO
            nid.szInfo = message
            nid.szInfoTitle = title
            nid.dwInfoFlags = 1  # 1=信息图标
            if not Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(nid)):
                err = GetLastError()
                logger.warning(f"Shell_NotifyIconW NIM_MODIFY 失败，错误码={err}，气泡通知未显示")
            else:
                logger.info("气泡通知发送成功")

            start = time.time()
            while time.time() - start < timeout + 1:
                PumpWaitingMessages()
                time.sleep(0.05)

            # 删除前先清除气泡，避免气泡仍显示时 NIM_DELETE 返回 E_FAIL 导致图标残留
            clear_nid = NOTIFYICONDATAW()
            clear_nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
            clear_nid.hWnd = hwnd
            clear_nid.uID = _NOTIFY_UID
            clear_nid.uFlags = NIF_GUID | NIF_INFO
            clear_nid.guidItem = _NOTIFY_GUID
            clear_nid.szInfo = ''
            Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(clear_nid))
            time.sleep(0.2)

            # 删除托盘图标，失败时重试几次
            delete_nid = NOTIFYICONDATAW()
            delete_nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
            delete_nid.hWnd = hwnd
            delete_nid.uID = _NOTIFY_UID
            delete_nid.uFlags = NIF_GUID
            delete_nid.guidItem = _NOTIFY_GUID
            deleted = False
            for _ in range(3):
                if Shell_NotifyIconW(NIM_DELETE, ctypes.byref(delete_nid)):
                    deleted = True
                    break
                err = GetLastError()
                time.sleep(0.3)
            if not deleted:
                logger.warning(f"Shell_NotifyIconW NIM_DELETE 失败，错误码={err}")

    except Exception as e:
        logger.error(f"发送系统通知时出错: {e}", exc_info=True)
    finally:
        # 确保资源被释放，避免托盘图标或窗口类泄漏导致后续通知失败
        if hwnd:
            DestroyWindow(hwnd)
        if hIcon:
            ctypes.windll.user32.DestroyIcon(hIcon)
        if class_atom and hinst:
            UnregisterClass(class_atom, hinst)

def send_notification(title: str, message: str, timeout: int = 5):
    """
    发送 Windows 系统托盘通知（非阻塞版）

    Args:
        title: 通知标题
        message: 通知内容
        timeout: 显示时长（秒），默认 5 秒
    """
    icon_path = get_icon_path()
    threading.Thread(
        target=_send_notification_impl,
        args=(title, message, timeout),
        kwargs={"icon_path": icon_path},
        daemon=True,
    ).start()

def _extract_tool_title(tool) -> str:
    """提取工具标题，优先使用模块中 logger 的名称"""
    # 工具可能被 @ask_on_missing 装饰器包装，先尝试获取原始函数
    original_fn = getattr(tool.fn, "__wrapped__", tool.fn)
    fn_globals = getattr(original_fn, "__globals__", {})
    logger = fn_globals.get("logger")
    if logger and hasattr(logger, "name"):
        return logger.name

    desc = (tool.description or "").strip()
    if desc:
        first_line = desc.split("\n")[0].strip()
        if first_line:
            return first_line
    return tool.name

def _format_result_content(title: str, result) -> str:
    """根据工具返回结果生成通知内容，优先展示具体结果文本"""
    content = ""
    if isinstance(result, dict):
        # 优先使用 result 字段中的具体信息
        detail = result.get("result", "")
        if detail:
            content = str(detail)
        elif result.get("success") is False:
            content = "执行失败"
        else:
            content = "执行完成"
    elif isinstance(result, str):
        content = result
    else:
        content = str(result) if result is not None else "执行完成"

    # 限制长度，避免通知内容过长
    if len(content) > 80:
        content = content[:77] + "..."
    return content

def attach_tool_notifications(mcp):
    """为所有已注册工具附加调用通知（当配置开启时），在工具返回后触发"""
    config = load_config()
    if not config.get("handle", {}).get("display_notification", True):
        return

    for name, tool in mcp._tool_manager._tools.items():
        # 避免通知工具自身触发通知
        if name == "send_system_notification":
            continue

        original_fn = tool.fn
        title = _extract_tool_title(tool)

        if tool.is_async:
            def make_async_wrapper(orig, t):
                async def wrapper(*args, **kwargs):
                    result = await orig(*args, **kwargs)
                    send_notification(t, _format_result_content(t, result), timeout=5)
                    return result
                return wrapper
            tool.fn = make_async_wrapper(original_fn, title)
        else:
            def make_sync_wrapper(orig, t):
                def wrapper(*args, **kwargs):
                    result = orig(*args, **kwargs)
                    send_notification(t, _format_result_content(t, result), timeout=5)
                    return result
                return wrapper
            tool.fn = make_sync_wrapper(original_fn, title)