import os
import logging
from utils.music.play import play_music
from utils.music.music import MusicPlayer

logger = logging.getLogger('音乐搜索')

def search_name_play(song_name: str, singer_name: str = "") -> dict:
    logger.info(f"开始搜索并播放 {song_name} - {singer_name}")
    if not song_name:
        return {
            "success": False,
            "result": "错误：歌曲名称不能为空"
        }
    
    try:
        # 获取音乐信息
        music_info_result = MusicPlayer().get_music_name_info(song_name, singer_name)
        
        # 验证音乐信息是否正常获取
        if not music_info_result or not music_info_result.get("success", False):
            error_msg = music_info_result.get('result', '') if music_info_result else '未知错误'
            msg = f"无法获取音乐信息: {error_msg}"
            logger.error(msg)
            return {
                "success": False,
                "result": msg
            }
        
        # 处理音乐信息并下载
        download_result = MusicPlayer().process_music_info(music_info_result)
        if not download_result or not download_result.get("success", False):
            error_msg = download_result.get('result', '') if download_result else '未知错误'
            msg = f"下载失败: {error_msg}"
            logger.error(msg)
            return {
                "success": False,
                "result": msg
            }
        
        # 播放下载的音乐
        file_path = download_result.get("file_path", "")
        duration = download_result.get("duration", "")
        
        if not file_path or not os.path.exists(file_path):
            msg = f"错误：下载的音乐文件不存在 - {file_path}"
            logger.error(msg)
            return {
                "success": False,
                "result": msg
            }
        
        # 播放音乐
        play_result = play_music(file_path, duration)
        
        if play_result.get("success", False):
            logger.info(f"正在播放: {download_result.get('song_name', '')} - {download_result.get('singer_name', '')} - {download_result.get('album_name', '')}")
            return {
                "success": True,
                "result": f"音乐下载和播放成功: {play_result['result']}",
                "duration": duration,
                "song_name": download_result.get('song_name', ''),
                "singer_name": download_result.get('singer_name', ''),
                "album_name": download_result.get('album_name', '')
            }
        else:
            return {
                "success": False,
                "result": f"音乐下载成功，但播放失败: {play_result.get('result', '')}",
                "duration": duration,
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