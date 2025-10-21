import time
import asyncio
import logging
from utils.speaker.get_all_audio import get_all_audio_sessions

logger = logging.getLogger('播放器监控')

async def monitor_player_status(default_player_name, total_seconds, file_name):
    """异步监控播放器状态
    
    Args:
        default_player_name (str): 默认播放器名称
        total_seconds (int): 监控总时长（秒）
        file_name (str): 正在播放的文件名
    """
    logger.info(f"开始监控播放器状态")
    start_time = time.time()
    
    # 等待一小段时间确保播放器已经启动
    await asyncio.sleep(2)
    
    while time.time() - start_time < total_seconds:
        try:
            # 获取所有音频会话
            audio_sessions_result = get_all_audio_sessions(False)
            
            if not audio_sessions_result["success"]:
                logger.warning(f"获取音频会话失败: {audio_sessions_result['result']}")
                await asyncio.sleep(1)
                continue
            
            # 检查默认播放器是否在音频会话中且处于活动状态
            player_active = False
            for session in audio_sessions_result['result']:
                # 注意：get_all_audio_sessions返回的app_name没有.exe扩展名
                if session['app_name'] == default_player_name:
                    if session['is_active']:
                        player_active = True
                        break
            
            # 如果播放器不再活动或不在会话列表中
            if not player_active:
                logger.info(f"播放器 {default_player_name} 状态已更改")
                break
            
        except Exception as e:
            logger.warning(f"监控播放器状态时出错: {str(e)}")
        
        # 每秒检查一次
        await asyncio.sleep(1)
    
    # 如果是因为超时退出循环
    if time.time() - start_time >= total_seconds:
        logger.info(f"播放器状态已更改，文件 {file_name} 播放时间已达到预期时长")