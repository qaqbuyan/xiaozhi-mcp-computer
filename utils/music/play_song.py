import logging
from mcp.server.fastmcp import FastMCP
from utils.music.search_name import search_name_play
from utils.missing_params import ask_on_missing

logger = logging.getLogger('播放歌曲')

def computer_play_song(mcp: FastMCP):
    @mcp.tool()
    @ask_on_missing('song_name')
    def computer_play_song(song_name: str = None, singer_name: str = '', force: bool = False) -> dict:
        """用于在电脑上播放指定的音乐
        当用户需要在电脑上播放指定的音乐时，立刻使用该工具。
        Args:
            song_name (str): 歌曲名称，禁止为空
            singer_name (str): 歌手名称，可以为空
            force (bool): 是否强制重新添加。为true时即使歌曲已在播放队列中也重新添加并播放；
                          为false时如果歌曲已在队列中则不重复添加，直接返回已在队列中的提示。
                          默认为false。
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
                    "album_name": str,           # 专辑名称
                    "already_in_queue": bool     # 歌曲是否已在队列中（重复请求时）
                }
        """
        logger.info("播放指定的音乐...")
        result = search_name_play(song_name, singer_name, force=force)
        logger.info(f"播放结果：{result}")
        return result