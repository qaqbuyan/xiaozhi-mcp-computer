import io
import sys
import logging
from handle.loader import load_config
from mcp.server.fastmcp import FastMCP
from utils.tools import register_alone
from utils.file.tools import register_file
from utils.open.tools import register_open
from utils.scan.tools import register_scan
from utils.mouse.tools import register_mouse
from utils.music.tools import register_music
from utils.version.tools import register_version
from utils.speaker.tools import register_speaker
from utils.browser.tools import register_browser
from utils.keyboard.tools import register_keyboard
from utils.clipboard.tools import register_clipboard
from utils.automation.tools import register_automation
from utils.screenshot.tools import register_screenshot
from utils.application.tools import register_application
from utils.image.tools import register_image

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def register_tool(mcp: FastMCP, config_path: list, register_func, tool_name: str, logger):
    """统一工具注册函数"""
    # 获取配置
    config = load_config()
    tool_config = config
    for key in config_path:
        tool_config = tool_config.get(key, {})
    
    # 检查是否有启用的工具
    has_tools = any(tool_config.values()) if isinstance(tool_config, dict) else False
    
    if has_tools:
        # 注册工具
        register_func(mcp)
    else:
        logger.info(f"所有{tool_name}工具已禁用，跳过注册")

def register(mcp: FastMCP):
    """集中注册所有工具"""
    logger = logging.getLogger('集中注册')
    logger.info("进行所有工具注册...")
    
    # 工具注册配置列表
    tool_registrations = [
        (['utils', 'application'], register_application, "程序"),
        (['utils', 'automation', 'document'], register_automation, "自动化"),
        (['utils', 'file'], register_file, "文件"),
        (['utils', 'keyboard'], register_keyboard, "键盘"),
        (['utils', 'mouse'], register_mouse, "鼠标"),
        (['utils', 'open'], register_open, "打开"),
        (['utils', 'scan'], register_scan, "扫描"),
        (['utils', 'speaker'], register_speaker, "扬声器"),
        (['utils', 'browser'], register_browser, "浏览器"),
        (['utils', 'alone'], register_alone, "单独"),
        (['utils', 'image'], register_image, "图像"),
        (['utils', 'screenshot'], register_screenshot, "截图"),
        (['utils', 'clipboard'], register_clipboard, "剪贴板"),
        (['utils', 'music', 'module'], register_music, "音乐")
    ]
    
    # 批量注册所有工具
    for config_path, register_func, tool_name in tool_registrations:
        register_tool(mcp, config_path, register_func, tool_name, logger)
    
    # 注册版本工具（无需配置检查）
    register_version(mcp)
    
    logger.info("所有工具注册完成")