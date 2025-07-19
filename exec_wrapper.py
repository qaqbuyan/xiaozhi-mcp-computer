import io
import os
import sys
import time
import yaml
import ctypes
import logging
import asyncio
import winshell
import threading
import tkinter as tk
from PIL import Image
from tkinter import messagebox
from handle.loader import load_config
from handle.logger import setup_logging
from pystray import Icon as TrayIcon, Menu as TrayMenu, MenuItem as TrayMenuItem

# 设置编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 获取配置文件中的版本号
config = load_config()
version = config['version']
# 提取版本号中的数字部分
version_parts = version.split('-')[0].split('.')
file_vers = tuple(map(int, version_parts[:3])) + (0,)
# 将元组转换为字符串版本号
str_version = '.'.join(map(str, version_parts))

tray_icon = None
# 获取控制台窗口句柄
HWND = ctypes.windll.kernel32.GetConsoleWindow()

def main():
    global tray_icon
    # 提前设置控制台窗口标题
    ctypes.windll.kernel32.SetConsoleTitleW(f"小智控制电脑 V{str_version}")

    # 创建主窗口但不显示
    root = tk.Tk()
    root.withdraw()
    root.title(f"小智控制电脑 V{str_version}")

    # 新增窗口显示状态变量
    window_hidden = False  # 初始状态为显示

    # 修改切换窗口显示/隐藏的函数，控制控制台窗口
    def toggle_window(icon, item):
        nonlocal window_hidden
        def do_toggle():
            nonlocal window_hidden
            if window_hidden:
                ctypes.windll.user32.ShowWindow(HWND, 1)  # 显示窗口
            else:
                ctypes.windll.user32.ShowWindow(HWND, 0)  # 隐藏窗口
            window_hidden = not window_hidden
        root.after(0, do_toggle)

    # 新增托盘图标功能
    def quit_app(icon, item):
        """退出应用程序"""
        root.quit()
        icon.stop()

    def stop_tray_icon():
        if tray_icon:
            tray_icon.stop()

    # 显示系统托盘图标
    try:
        # 尝试加载图标文件
        if getattr(sys, 'frozen', False):
            # 打包后环境 - 使用PyInstaller的临时资源目录
            base_path = sys._MEIPASS
            icon_path = os.path.join(base_path, 'favicon.ico')
        else:
            # 开发环境
            icon_path = os.path.join(os.path.dirname(__file__), 'favicon.ico')
        logger.info("初始化准备中...")  # 添加日志以便调试
        if os.path.exists(icon_path):
            image = Image.open(icon_path)
        else:
            # 创建默认蓝色图标
            image = Image.new('RGB', (64, 64), color='blue')
            logger.warning("出现问题，但是仍然可以正常运行")
    except Exception as e:
        logger.error("出现问题，但是仍然可以正常运行")
        # 创建默认红色图标
        image = Image.new('RGB', (64, 64), color='red')
    logger.info("初始化完成")

    # 创建托盘菜单
    tray_menu = TrayMenu(
        TrayMenuItem('显示/隐藏', toggle_window),
        TrayMenuItem('退出', quit_app)
    )
    # 创建并运行托盘图标
    tray_icon = TrayIcon("小智控制电脑", image, f"小智控制电脑 V{str_version}", tray_menu)

    def run_tray_icon():
        tray_icon.run()

    # 在单独线程中启动托盘图标
    tray_thread = threading.Thread(target=run_tray_icon, daemon=True)
    tray_thread.start()

    # Windows下禁用控制台鼠标点击暂停
    if os.name == 'nt':
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), 128)

    try:
        # 设置工作目录为可执行文件所在目录
        os.chdir(os.path.dirname(sys.executable))
        # 检查配置文件是否存在，如果不存在则创建
        config_path = 'config.yaml'
        if not os.path.exists(config_path):
            logger.info("配置文件不存在，正在创建默认配置")
            default_config = """# MCP管道连接配置
# 文件版本
version: 0.2.2-beta

# MCP管道连接配置
reconnection:
  # 初始重连等待时间(秒)
  initial_backoff: 1
  # 最大重连等待时间(秒)
  max_backoff: 600
  # 当前重连尝试次数(初始为0)
  reconnect_attempt: 0
  # 当前退避时间(初始为1秒)
  backoff: 1

# WebSocket端点配置
endpoint:
  # MCP服务器WebSocket端点(必须以wss://或ws://开头)
  url: \"\""""
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(default_config)
            logger.info("默认配置文件已创建，请修改配置后重新运行程序")
            time.sleep(30)  # 等待30秒后退出
            return 0  # 正常退出
        
        # 加载YAML配置
        with open(config_path, encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        # 检查是否是打包环境
        if getattr(sys, 'frozen', False):
            import multiprocessing
            multiprocessing.freeze_support()
        
        mcp_pipe_path = os.path.join(os.path.dirname(__file__), 'mcp_pipe.py')
        aggregate_path = os.path.join(os.path.dirname(__file__), 'aggregate.py')
        
        if not os.path.exists(mcp_pipe_path) or not os.path.exists(aggregate_path):
            logger.error("缺少必要的脚本文件")
            time.sleep(30)  # 等待30秒
            raise FileNotFoundError("缺少必要的脚本文件")
            
        # 修改为直接导入mcp_pipe模块并调用其main函数
        logger.info("导入管道服务")
        from mcp_pipe import main as mcp_main
        
        logger.info("启动管道服务")
        if not config['endpoint']['url'].startswith(('wss://', 'ws://')):
            logger.error("请确认配置，WebSocket端点URL必须以wss://或ws://开头")
            time.sleep(30)
            return 1
            
        # 创建事件循环并运行
        def run_pipe_service():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # 确保mcp_main返回的是协程并立即执行
                return_code = loop.run_until_complete(mcp_main([aggregate_path], on_process_end=stop_tray_icon))
            except KeyboardInterrupt:
                logger.info("接收到Ctrl+C信号，正在关闭程序...")
                return_code = 0
            except Exception as e:
                logger.error(f"程序运行出错: {str(e)}")
                return_code = 1
            finally:
                # 清理所有待处理的任务
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                loop.close()
            logger.info(f"管道服务已退出，返回码: {return_code}")
            root.after(0, root.quit)

        pipe_thread = threading.Thread(target=run_pipe_service, daemon=True)
        pipe_thread.start()

        # 处理窗口关闭事件
        def on_closing():
            root.destroy()
            stop_tray_icon()

        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()

    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
        messagebox.showerror("错误", f"程序运行出错: {str(e)}")
        return 1

def set_startup():
    try:
        # 获取当前程序的路径
        exe_path = os.path.abspath(__file__)
        # 如果是打包后的可执行文件，需要获取 sys.executable
        import sys
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable

        startup_folder = winshell.startup()
        # 设置快捷方式名称
        shortcut_path = os.path.join(startup_folder, '小智控制电脑.lnk')
        with winshell.shortcut(shortcut_path) as shortcut:
            shortcut.path = exe_path
            shortcut.description = '小智AI控制电脑'
            # 设置发布者
            shortcut.working_directory = os.path.dirname(exe_path)
            shortcut.company = 'Buyan'
            # 设置图标
            icon_path = os.path.join(os.path.dirname(exe_path), 'favicon.ico')
            if os.path.exists(icon_path):
                shortcut.icon_location = (icon_path, 0)
        logger.info("开机自启创建成功")
    except Exception as e:
        logger.error(f"创建开机自启时出错: {e}")



if __name__ == "__main__":
    logger = setup_logging()
    logger = logging.getLogger('代理运行')
    set_startup()
    sys.exit(main())