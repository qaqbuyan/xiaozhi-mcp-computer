import os
import logging
from utils.music.music import Music
from utils.music.play import play_music, playback_manager

logger = logging.getLogger('音乐搜索')

def search_name_play(song_name: str, singer_name: str = "") -> dict:
    """根据歌曲名和歌手名搜索并播放音乐
    
    Args:
        song_name (str): 歌曲名
        singer_name (str): 歌手名（可选）
        
    Returns:
        dict: 包含播放状态的字典
    """
    logger.info(f"搜索并播放音乐: {song_name} - {singer_name}")
    
    # 参数验证
    if not song_name:
        msg = "错误：歌曲名为空"
        logger.error(msg)
        return {
            "success": False,
            "result": msg
        }
    
    try:
        # 创建Music实例（只创建一次）
        music_player = Music()
        
        # 获取音乐信息
        music_info_result = music_player.get_music_name_info(song_name, singer_name)
        
        # 验证音乐信息是否正常获取
        if not music_info_result or not music_info_result.get("success", False):
            error_msg = music_info_result.get('result', '') if music_info_result else '未知错误'
            msg = f"获取音乐信息失败: {error_msg}"
            logger.error(msg)
            return {
                "success": False,
                "result": msg
            }
        
        # 处理音乐信息（下载音乐文件）
        download_result = music_player.process_music_info(music_info_result)
        if not download_result or not download_result.get("success", False):
            error_msg = download_result.get('result', '') if download_result else '未知错误'
            msg = f"处理音乐信息失败: {error_msg}"
            logger.error(msg)
            return {
                "success": False,
                "result": msg
            }
        
        # 获取文件路径
        file_path = download_result.get("file_path", "")
        if not file_path or not os.path.exists(file_path):
            msg = f"错误：音乐文件不存在 - {file_path}"
            logger.error(msg)
            return {
                "success": False,
                "result": msg
            }
        
        # 播放音乐（快速返回，不等待播放完成），传递歌曲信息
        play_result = play_music(
            file_path, 
            download_result.get("duration", ""),
            song_name=download_result.get('song_name', ''),
            singer_name=download_result.get('singer_name', '')
        )
        
        # 返回结果（无论播放是否成功，都快速返回）
        if play_result.get("success", False):
            # 获取当前播放状态信息
            playback_info = playback_manager.get_current_playback_info()
            
            # 构建显示信息
            if play_result.get("queued", False):
                # 如果音乐被添加到队列而不是立即播放
                msg = f"已添加到播放队列，队列位置: {play_result.get('queue_position', 0)}"
                if playback_info["current_display_name"]:
                    msg += f"，当前正在播放: {playback_info['current_display_name']}"
            else:
                # 如果没有音乐正在播放，立即开始播放
                msg = f"已开始播放: {song_name}"
                if singer_name:
                    msg += f" - {singer_name}"
            
            logger.info(msg)
            return {
                "success": True,
                "result": msg,
                "queued": play_result.get("queued", False),
                "queue_position": play_result.get("queue_position", 0),
                "duration": download_result.get("duration", ""),
                "song_name": download_result.get('song_name', ''),
                "singer_name": download_result.get('singer_name', ''),
                "album_name": download_result.get('album_name', '')
            }
        else:
            msg = f"播放处理失败: {play_result.get('result', '未知错误')}"
            logger.error(msg)
            return {
                "success": False,
                "result": msg,
                "duration": download_result.get("duration", ""),
                "song_name": download_result.get('song_name', ''),
                "singer_name": download_result.get('singer_name', ''),
                "album_name": download_result.get('album_name', '')
            }
    except Exception as e:
        msg = f"操作过程中发生错误: {str(e)}"
        logger.error(msg)
        return {
            "success": False,
            "result": msg
        }