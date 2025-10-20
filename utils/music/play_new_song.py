import logging
from mcp.server.fastmcp import FastMCP
from utils.music.music import MusicPlayer
from utils.music.batch_play import batch_play_music

logger = logging.getLogger('播放新歌')

def computer_play_new_song(mcp: FastMCP):
    @mcp.tool()
    def computer_play_new_song(type: int = 1) -> dict:
        """用于在电脑上播放新歌速递
        当用户需要在电脑上播放新歌速递时，立刻使用该工具。
        Args:
            type (int): 新歌类型，0表示新发布的歌曲
                        1表示内地，2表示欧美，3表示日本，4表示韩国，6表示港台
        Returns:
            dict: 包含success和result两个键的字典
        """
        try:
            # 在主线程中获取新歌信息，以便在返回结果中包含第一个播放的歌曲信息
            song_info = MusicPlayer().get_new_songs(type)
            
            # 先判断song_info是否有效
            if song_info and isinstance(song_info, dict) and song_info.get('success'):
                song_info_list = song_info.get('result', [])
                if isinstance(song_info_list, list) and song_info_list:
                    # 获取第一个播放的歌曲信息
                    first_song = song_info_list[0] if song_info_list else {}
                    first_song_mid = first_song.get('mid', '未知歌曲')
                    first_singer = first_song.get('singer', '未知歌手')
                    
                    # 记录第一个播放的歌曲信息
                    logger.info(f"第一个播放：{first_song_mid} - {first_singer}")
                    
                    # 将新歌信息转换为批量播放所需的格式
                    song_list_data = []
                    for song in song_info_list:
                        song_list_data.append({
                            "mid": song.get('mid', ''),
                            "name": f"新歌-{song.get('mid', '')}",
                            "singer_names": song.get('singer', '未知歌手')
                        })
                    
                    # 直接调用batch_play_music，不在play_new_song中开线程
                    # batch_play_music函数内部会处理线程逻辑
                    batch_play_music(song_list_data)
                    
                    # 立即返回成功响应，包含第一个播放的歌曲信息
                    return {
                        "success": True,
                        "result": f"新歌播放任务已启动，共{len(song_list_data)}首歌曲，第一个播放：{first_song_mid} - {first_singer}"
                    }
                else:
                    return {
                        "success": False,
                        "result": "获取到的新歌列表为空或格式不正确"
                    }
            else:
                error_msg = song_info.get('result', '未知错误') if song_info else '未知错误'
                return {
                    "success": False,
                    "result": f"获取新歌速递失败: {error_msg}"
                }
        except Exception as e:
            return {
                "success": False,
                "result": f"获取新歌信息失败: {str(e)}"
            }