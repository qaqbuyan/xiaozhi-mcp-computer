import logging
from mcp.server.fastmcp import FastMCP
from utils.music.play_song import computer_play_song
from utils.music.play_song_list import computer_play_song_list
from utils.music.play_new_song import computer_play_new_song
from handle.loader import load_config

def register_music(mcp: FastMCP):
    """集中注册所有音乐工具"""
    logger = logging.getLogger('音乐工具')
    
    # 加载配置
    config = load_config()
    music_module_config = config.get('utils', {}).get('music', {}).get('module', {})
    
    # 检查是否有任何音乐工具启用
    has_music_tools = any(music_module_config.values())
    
    if not has_music_tools:
        logger.info("所有音乐工具已禁用，跳过注册")
        return
    
    # 验证音乐API地址配置
    music_config = config.get('utils', {}).get('music', {})
    music_api = music_config.get('music_api', '')
    
    if not music_api:
        logger.error("音乐API地址未配置，跳过音乐工具注册")
        return
    
    if not music_api.startswith(('http://', 'https://')):
        logger.error(f"无效的音乐API地址: {music_api}，必须以http://或https://开头，跳过音乐工具注册")
        return
    
    logger.info("开始注册...")
    
    # 根据配置注册对应的工具
    if music_module_config.get('request_song', False):
        # 点歌音乐
        computer_play_song(mcp)
    
    if music_module_config.get('play_song_list', False):
        # 音乐（歌单）播放
        computer_play_song_list(mcp)
    
    if music_module_config.get('play_new_song', False):
        # 新歌速递
        computer_play_new_song(mcp)
    
    logger.info("注册完成")