import logging
import multiprocessing
from utils.music.play import playback_manager
from utils.music.play_worker import _batch_play_worker

logger = logging.getLogger('批量播放')

def batch_play_music(song_list):
    """批量播放音乐
    
    Args:
        song_list (list): 歌曲信息列表，每个元素包含mid、name、singers等字段
        
    Returns:
        dict: 包含success和result两个键的字典
    """
    # 立即检查song_list参数（在主线程中快速完成）
    if not song_list or not isinstance(song_list, list):
        msg = "song_list参数必须是一个非空数组"
        logger.error(msg)
        return {"success": False, "result": msg}
    
    # 获取第一个播放的歌曲信息（快速操作）
    first_song = song_list[0] if song_list else {}
    first_song_name = first_song.get('name', '未知歌曲')
    first_singer_names = first_song.get('singer_names', '未知歌手')
    
    # 快速提取mid列表
    mids_to_process = [song.get('mid', '') for song in song_list if song.get('mid')]
    
    # 直接在主线程中创建并启动后台进程，避免额外的线程嵌套
    try:
        # 创建后台进程，设置为daemon=True，当主进程退出时自动终止
        process = multiprocessing.Process(
            target=_batch_play_worker,
            args=(mids_to_process,)
        )
        process.daemon = True
        process.start()
        
        # 记录日志
        logger.info(f"开始批量播放音乐任务，共{len(song_list)}首歌曲")
        msg_log = f"批量播放后台进程已启动，将播放{len(song_list)}首歌曲"
        if first_song_name and first_singer_names:
            msg_log += f"，第一个播放：{first_song_name} - {first_singer_names}"
        logger.info(msg_log)
        
        # 构建并立即返回响应消息
        return_msg = "批量播放已开始"
        if first_song_name and first_singer_names:
            return_msg += f"，将播放{len(song_list)}首歌曲，第一个播放：{first_song_name} - {first_singer_names}"
        
    except Exception as e:
        return_msg = f"启动批量播放后台进程失败: {str(e)}"
    
    # 立即返回成功信息，不阻塞主流程
    logger.info(return_msg)
    return {"success": True, "result": return_msg}

def batch_play_song_list_with_queue(song_list, song_list_id=None):
    """使用播放队列管理批量播放歌单
    
    Args:
        song_list (list): 歌曲信息列表，每个元素包含mid、name、singers等字段
        song_list_id (str): 歌单ID，用于标识当前播放的歌单
        
    Returns:
        dict: 包含success和result两个键的字典
    """
    # 立即检查song_list参数（在主线程中快速完成）
    if not song_list or not isinstance(song_list, list):
        msg = "song_list参数必须是一个非空数组"
        logger.error(msg)
        return {"success": False, "result": msg}
    
    # 获取第一个播放的歌曲信息（快速操作）
    first_song = song_list[0] if song_list else {}
    first_song_name = first_song.get('name', '未知歌曲')
    first_singer_names = first_song.get('singer_names', '未知歌手')
    
    try:
        # 使用播放管理器清理队列并播放新的歌单
        playback_manager.clear_queue_and_play_song_list(song_list, song_list_id)
        
        msg_log = f"已切换到新的歌单播放，共{len(song_list)}首歌曲，歌单ID: {song_list_id}"
        if first_song_name and first_singer_names:
            msg_log += f"，第一个播放：{first_song_name} - {first_singer_names}"
        logger.info(msg_log)
        
        # 构建并立即返回响应消息
        return_msg = "歌单切换成功，已开始播放新的歌单"
        if first_song_name and first_singer_names:
            return_msg += f"，将播放{len(song_list)}首歌曲，第一个播放：{first_song_name} - {first_singer_names}"
        
    except Exception as e:
        return_msg = f"切换歌单失败: {str(e)}"
        logger.error(return_msg)
        return {"success": False, "result": return_msg}
    
    # 立即返回成功信息，不阻塞主流程
    logger.info(return_msg)
    return {"success": True, "result": return_msg}