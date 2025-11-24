import logging
from handle.loader import load_config
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
    
    # 加载配置并检查是否有启用的工具
    config = load_config()
    speaker_config = config.get('utils', {}).get('speaker', {})
    
    # 检查是否有任何扬声器工具启用
    has_speaker_tools = any(speaker_config.values())
    
    if not has_speaker_tools:
        logger.info("所有扬声器工具已禁用，跳过注册")
        return
    
    logger.info("开始注册...")
    
    # 根据配置注册对应的工具
    if speaker_config.get('get_volume', False):
        get_volume(mcp)
    
    if speaker_config.get('set_volume', False):
        set_volume(mcp)
    
    if speaker_config.get('toggle_mute', False):
        toggle_mute(mcp)
    
    if speaker_config.get('get_audio_sessions', False):
        get_audio_sessions(mcp)
    
    if speaker_config.get('get_mute', False):
        get_mute(mcp)
    
    if speaker_config.get('set_app_volume', False):
        set_app_volume(mcp)
    
    logger.info("注册完成")