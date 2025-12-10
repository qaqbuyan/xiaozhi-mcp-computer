import logging
from mcp.server.fastmcp import FastMCP
from utils.music.search_name import search_name_play

logger = logging.getLogger('播放歌曲')

def computer_play_song(mcp: FastMCP):
    @mcp.tool()
    def computer_play_song(song_name: str, singer_name: str) -> dict:
        """用于在电脑上播放指定的音乐
        当用户需要在电脑上播放指定的音乐时，立刻使用该工具。
        Args:
            song_name (str): 歌曲名称，禁止为空
            singer_name (str): 歌手名称，可以为空
        Returns:
            dict: 包含操作结果的字典，格式为: 
                { 
                    "success": bool,              # 是否成功 
                    "result": str,               # 结果消息
                    "queued": bool,              # 是否添加到播放队列
                    "queue_position": int,       # 队列位置（如果添加到队列）
                    "duration": str,             # 歌曲时长（格式："分:秒"）
                    "song_name": str,            # 实际播放的歌曲名称
                    "singer_name": str,          # 实际播放的歌手名称
                    "album_name": str            # 专辑名称
                }
        """
        logger.info("播放指定的音乐...")
        result = search_name_play(song_name, singer_name)
        logger.info(f"播放结果：{result}")
        return result