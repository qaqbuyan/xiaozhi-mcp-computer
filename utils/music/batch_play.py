import logging
import threading
import multiprocessing
import queue
from utils.music.play_worker import _batch_play_worker

logger = logging.getLogger('批量播放')

def batch_play_music(song_list):
    """批量播放音乐
    
    Args:
        song_list (list): 歌曲信息列表，每个元素包含mid、name、singers等字段
        
    Returns:
        dict: 包含success和result两个键的字典
    """
    def batch_play_background():
        """后台执行批量播放任务"""
        try:
            logger.info(f"开始批量播放音乐任务，共{len(song_list)}首歌曲")
            
            # 检查song_list参数
            if not song_list or not isinstance(song_list, list):
                msg = "song_list参数必须是一个非空数组"
                logger.error(msg)
                return
            
            # 创建要处理的歌曲列表的副本
            songs_to_process = song_list.copy()
            
            # 获取第一个播放的歌曲信息
            first_song = songs_to_process[0] if songs_to_process else {}
            first_song_name = first_song.get('name', '未知歌曲')
            first_singer_names = first_song.get('singer_names', '未知歌手')
            
            # 提取mid列表用于后台播放
            mids_to_process = [song.get('mid', '') for song in songs_to_process if song.get('mid')]
            
            # 创建并启动后台进程
            try:
                # 创建后台进程，设置为daemon=True，当主进程退出时自动终止
                process = multiprocessing.Process(
                    target=_batch_play_worker,
                    args=(mids_to_process,)
                )
                process.daemon = True
                process.start()
                
                # 构建返回消息，包含第一个播放的歌曲信息
                msg = f"批量播放后台进程已启动，将播放{len(songs_to_process)}首歌曲"
                if first_song_name and first_singer_names:
                    msg += f"，第一个播放：{first_song_name} - {first_singer_names}"
                
                logger.info(msg)
            except Exception as e:
                msg = f"启动批量播放后台进程失败: {str(e)}"
                logger.error(msg)
        except Exception as e:
            logger.error(f"批量播放后台任务执行失败: {str(e)}")
    
    # 启动后台线程执行批量播放任务
    thread = threading.Thread(target=batch_play_background)
    thread.daemon = True  # 设置为守护线程，主程序退出时自动结束
    thread.start()
    
    # 返回成功信息
    return {"success": True, "result": "批量播放已开始"}