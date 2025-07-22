import logging
from mcp.server.fastmcp import FastMCP
from utils.automation.wechat.send_messages import send_wechat_messages_or_files
from utils.automation.wechat.get_message import get_current_wechat_chat_window_message

def register_wechat(mcp: FastMCP):
    """注册微信工具"""
    logger = logging.getLogger('微信工具')
    logger.info("开始注册...")
    # 注册发送微信消息的工具
    send_wechat_messages_or_files(mcp)
    # 注册获取微信消息的工具
    get_current_wechat_chat_window_message(mcp)
    logger.info("注册完成")