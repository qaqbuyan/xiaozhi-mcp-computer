import io
import sys
import logging
from mcp.server.fastmcp import FastMCP
from utils.tools import register_alone
from utils.file.tools import register_file
from utils.open.tools import register_open
from utils.scan.tools import register_scan
from utils.mouse.tools import register_mouse
from utils.version.tools import register_version
from utils.speaker.tools import register_speaker
from utils.browser.tools import register_browser
from utils.keyboard.tools import register_keyboard
from utils.clipboard.tools import register_clipboard
from utils.application.tools import register_application
from utils.image_recognition.tools import register_image_recognition

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def register(mcp: FastMCP):
    """集中注册所有工具"""
    logger = logging.getLogger('集中注册')
    logger.info("进行所有工具注册...")
    # 注册程序工具
    register_application(mcp)
    # 注册文件工具
    register_file(mcp)
    # 注册键盘工具
    register_keyboard(mcp)
    # 注册鼠标工具
    register_mouse(mcp)
    # 注册打开工具
    register_open(mcp)
    # 注册扫描工具
    register_scan(mcp)
    # 注册扬声器工具
    register_speaker(mcp)
    # 注册浏览器工具
    register_browser(mcp)
    # 注册单独工具
    register_alone(mcp)
    # 注册版本工具
    register_version(mcp)
    # 注册图像识别工具
    register_image_recognition(mcp)
    # 注册剪贴板工具
    register_clipboard(mcp)
    logger.info("所有工具注册完成")