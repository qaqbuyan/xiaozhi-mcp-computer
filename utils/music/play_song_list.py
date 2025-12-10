import logging
from utils.music.music import Music
from mcp.server.fastmcp import FastMCP
from utils.music.play import playback_manager
from utils.music.batch_play import batch_play_song_list_with_queue

logger = logging.getLogger('播放歌单')

def computer_play_song_list(mcp: FastMCP):
    @mcp.tool()
    def computer_play_song_list(song_list: int, shuffle: bool = False) -> dict:
        """用于在电脑上批量播放歌单列表
        当用户需要在电脑上批量播放歌单列表时，立刻使用该工具。
        Args:
            song_list (int): 歌单id
            shuffle (bool): 是否打乱播放顺序，默认为False（顺序播放）
        Returns:
            dict: 包含success和result两个键的字典
        """
        try:
            # 在主线程中获取歌单信息，以便在返回结果中包含第一个播放的歌曲信息
            song_info = Music().get_song_list(song_list)
            
            # 先判断song_info是否有效
            if song_info and isinstance(song_info, dict) and song_info.get('success'):
                song_list_data = song_info.get('result', [])
                if isinstance(song_list_data, list) and song_list_data:
                    # 如果需要打乱播放顺序，提前打乱
                    if shuffle:
                        import random
                        random.shuffle(song_list_data)
                        logger.info("已打乱播放顺序")
                    else:
                        logger.info("按顺序播放")
                    # 获取第一个播放的歌曲信息
                    first_song = song_list_data[0] if song_list_data else {}
                    first_song_name = first_song.get('name', '未知歌曲')
                    first_singer_names = first_song.get('singer_names', '未知歌手')
                    
                    # 记录第一个播放的歌曲信息
                    if first_song_name and first_singer_names:
                        logger.info(f"第一个播放：{first_song_name} - {first_singer_names}")
                    
                    # 检查当前是否有歌单正在播放
                    current_playback_info = playback_manager.get_current_playback_info()
                    
                    if current_playback_info["is_playing"] and current_playback_info["current_song_list_id"]:
                        # 如果有歌单正在播放，使用新的歌单切换功能
                        logger.info(f"当前正在播放歌单ID: {current_playback_info['current_song_list_id']}，将切换到新的歌单")
                        batch_play_song_list_with_queue(song_list_data, str(song_list))
                    else:
                        # 如果没有歌单正在播放，使用传统的批量播放
                        logger.info("当前没有歌单正在播放，开始新的歌单播放")
                        batch_play_song_list_with_queue(song_list_data, str(song_list))
                    
                    # 立即返回成功响应，包含第一个播放的歌曲信息
                    if first_song_name and first_singer_names:
                        return {
                            "success": True,
                            "result": f"歌单播放任务已启动，包含{len(song_list_data)}首歌曲，请在音乐播放窗口查看播放状态，第一个播放：{first_song_name} - {first_singer_names}"
                        }
                    else:
                        return {
                            "success": True,
                            "result": f"歌单播放任务已启动，包含{len(song_list_data)}首歌曲，音乐将在后台继续播放"
                        }
                else:
                    return {
                        "success": False,
                        "result": "获取到的歌曲列表为空或格式不正确"
                    }
            else:
                error_msg = song_info.get('result', '未知错误') if song_info else '未知错误'
                return {
                    "success": False,
                    "result": f"获取歌单失败: {error_msg}"
                }
        except Exception as e:
            return {
                "success": False,
                "result": f"获取歌单信息失败: {str(e)}"
            }