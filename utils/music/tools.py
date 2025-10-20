import logging
from mcp.server.fastmcp import FastMCP
from utils.music.play_song import computer_play_song
from utils.music.play_song_list import computer_play_song_list
from utils.music.play_new_song import computer_play_new_song

def register_music(mcp: FastMCP):
    """集中注册所有音乐工具"""
    logger = logging.getLogger('音乐工具')
    logger.info("开始注册...")
    # 点歌音乐
    computer_play_song(mcp)
    # 音乐（歌单）播放
    computer_play_song_list(mcp)
    # 新歌速递
    computer_play_new_song(mcp)
    logger.info("注册完成")