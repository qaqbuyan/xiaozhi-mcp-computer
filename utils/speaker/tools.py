import logging
from mcp.server.fastmcp import FastMCP
from utils.speaker.get_mute import get_mute
from utils.speaker.set_mute import toggle_mute
from utils.speaker.get_volume import get_volume
from utils.speaker.set_volume import set_volume
from utils.speaker.set_app_volume import set_app_volume
from utils.speaker.get_audio_sessions import get_audio_sessions

def register_speaker(mcp: FastMCP):
    """集中注册所有扬声器工具"""
    logger = logging.getLogger('扬声器工具')
    logger.info("开始注册...")
    # 获取扬声器音量
    get_volume(mcp)
    # 设置扬声器音量
    set_volume(mcp)
    # 切换扬声器静音状态
    toggle_mute(mcp)
    # 获取所有正在运行的音频会话
    get_audio_sessions(mcp)
    # 获取扬声器静音状态
    get_mute(mcp)
    # 设置指定应用程序音量
    set_app_volume(mcp)
    logger.info("注册完成")