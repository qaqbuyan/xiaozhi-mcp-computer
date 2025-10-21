import os
import time
import logging
from handle.loader import load_config
from utils.music.play import play_music
from utils.music.music import MusicPlayer
from utils.file.default_handler import get_default_file_handler
from utils.speaker.get_audio_sessions import get_all_audio_sessions

logger = logging.getLogger('播放线程')

def _batch_play_worker(mids):
    """批量播放音乐的后台工作函数
    
    Args:
        mids (list): 要处理的音乐mid值列表
    """
    logger.info(f"批量播放后台进程已启动，共处理{len(mids)}首歌曲")
    
    # 添加失败计数器
    failure_count = 0
    max_failures = 3
    
    for i, mid in enumerate(mids, 1):
        logger.info(f"处理第{i}/{len(mids)}首歌曲，mid: {mid}")
        
        try:
            # 1. 获取音乐mid信息
            music_info_result = MusicPlayer().get_music_mid_info(mid)
            
            if not music_info_result or not music_info_result.get("success", False):
                error_msg = music_info_result.get('result', '') if music_info_result else '未知错误'
                logger.error(f"获取音乐信息失败: {error_msg}")
                failure_count += 1
                logger.error(f"当前连续失败次数: {failure_count}/{max_failures}")
                if failure_count >= max_failures:
                    logger.error(f"连续失败达到{max_failures}次，停止批量播放任务")
                    break
                continue
            
            # 处理音乐信息并下载
            download_result = MusicPlayer().process_music_info(music_info_result)
            
            if not download_result or not download_result.get("success", False):
                error_msg = download_result.get('result', '') if download_result else '未知错误'
                logger.error(f"下载音乐失败: {error_msg}")
                failure_count += 1
                logger.error(f"当前连续失败次数: {failure_count}/{max_failures}")
                if failure_count >= max_failures:
                    logger.error(f"连续失败达到{max_failures}次，停止批量播放任务")
                    break
                continue
            
            # 播放下载的音乐
            file_path = download_result.get("file_path", "")
            duration = download_result.get("duration", "")
            
            if not file_path or not os.path.exists(file_path):
                error_msg = f"下载的音乐文件不存在 - {file_path}"
                logger.error(f"播放音乐失败: {error_msg}")
                failure_count += 1
                logger.error(f"当前连续失败次数: {failure_count}/{max_failures}")
                if failure_count >= max_failures:
                    logger.error(f"连续失败达到{max_failures}次，停止批量播放任务")
                    break
                continue
            
            # 播放音乐
            play_result = play_music(file_path, duration)
            
            if not play_result or not play_result.get("success", False):
                error_msg = play_result.get('result', '') if play_result else '未知错误'
                logger.error(f"播放音乐失败: {error_msg}")
                failure_count += 1
                logger.error(f"当前连续失败次数: {failure_count}/{max_failures}")
                if failure_count >= max_failures:
                    logger.error(f"连续失败达到{max_failures}次，停止批量播放任务")
                    break
                continue
            
            # 成功处理后重置失败计数器
            failure_count = 0
            
            logger.info(f"第 {i}/{len(mids)} 首歌曲处理完成")
            logger.info(f"正在播放: {download_result.get('song_name', '')} - {download_result.get('singer_name', '')} - {download_result.get('album_name', '')}")

            # 尝试获取默认播放器名称
            default_player_name = ""
            try:
                # 获取下载链接
                link_result = MusicPlayer().get_download_link(music_info_result["result"])
                if link_result and link_result.get("success", False):
                    music_extension = MusicPlayer().get_music_extension(link_result["result"])
                    # 获取默认播放器
                    default_handler = get_default_file_handler(music_extension)
                    if default_handler and default_handler.get("success", False):
                        default_player_name = default_handler['result']
                        if default_player_name.lower().endswith('.exe'):
                            default_player_name = default_player_name[:-4]
            except Exception as e:
                logger.error(f"获取默认播放器名称时出错: {str(e)}")

            # 如果获取到了默认播放器名称，循环检测播放器状态
            if default_player_name:
                logger.info(f"开始监控默认播放器 '{default_player_name}' 的状态")
                
                # 初始化状态标记
                player_was_active = False
                paused = False
                pause_start_time = 0
                playback_start_time = time.time()  # 记录播放开始时间
                expected_duration_seconds = 0  # 预期的歌曲时长（秒）
                
                # 尝试解析预期时长
                try:
                    duration = download_result.get("duration", "")
                    if duration:
                        minutes, seconds = map(int, duration.split(':'))
                        expected_duration_seconds = minutes * 60 + seconds
                except ValueError:
                    pass  # 无效的时长格式，忽略
                
                # 循环检测播放器状态
                while True:
                    try:
                        # 获取所有音频会话
                        audio_sessions_result = get_all_audio_sessions(False)
                        
                        if not audio_sessions_result["success"]:
                            logger.warning(f"获取音频会话失败: {audio_sessions_result.get('result', '未知错误')}")
                            time.sleep(1)
                            continue
                        
                        # 检查默认播放器是否在音频会话中且处于活动状态
                        player_active = False
                        player_in_session = False
                        for session in audio_sessions_result['result']:
                            if session['app_name'] == default_player_name:
                                player_in_session = True
                                if session['is_active']:
                                    player_active = True
                                    break
                        
                        # 如果播放器不在音频会话中，停止播放全部音乐
                        if not player_in_session:
                            logger.warning(f"默认播放器 '{default_player_name}' 不在音频会话中，停止播放全部音乐")
                            return  # 直接返回，停止整个批处理流程
                        
                        # 计算已播放时间
                        elapsed_time = time.time() - playback_start_time
                        
                        # 状态变化逻辑
                        if not player_was_active and player_active:
                            # 播放器从非活动变为活动
                            if paused:
                                logger.info(f"播放器 '{default_player_name}' 已恢复播放")
                                paused = False
                                # 调整播放开始时间，扣除暂停的时间
                                playback_start_time += time.time() - pause_start_time
                            else:
                                logger.info(f"播放器 '{default_player_name}' 已开始播放")
                            player_was_active = True
                        elif player_was_active and not player_active:
                            # 播放器从活动变为非活动
                            # 检查是否接近预期时长（95%以上）
                            if expected_duration_seconds > 0 and elapsed_time >= expected_duration_seconds * 0.95:
                                # 已接近预期时长，认为是播放完成
                                logger.info(f"歌曲已接近预期时长（{elapsed_time:.1f}/{expected_duration_seconds}秒，{elapsed_time/expected_duration_seconds*100:.1f}%），继续播放下一首")
                                break  # 退出监控循环，继续播放下一首
                            else:
                                # 未接近预期时长，认为是暂停播放
                                if not paused:
                                    logger.info(f"播放器 '{default_player_name}' 状态已更改，暂停播放")
                                    paused = True
                                    pause_start_time = time.time()
                                player_was_active = False
                        
                        # 检查是否达到了歌曲的最大播放时间（防止无限暂停）
                        if expected_duration_seconds > 0:
                            # 从配置中获取暂停间隔设置
                            config = load_config()
                            pause_interval = config.get('utils', {}).get('music', {}).get('pause_interval', True)
                            max_wait_time = expected_duration_seconds * 2  # 设置最大等待时间为歌曲时长的2倍
                            
                            if paused and (time.time() - pause_start_time) > max_wait_time:
                                if pause_interval:
                                    logger.info(f"暂停时间过长（超过{max_wait_time}秒），继续播放下一首")
                                    break  # 退出监控循环，继续播放下一首
                                else:
                                    logger.info(f"暂停时间过长（超过{max_wait_time}秒），停止整个批量播放任务")
                                    return  # 直接返回，停止整个批处理流程
                        
                    except Exception as e:
                        logger.warning(f"检测播放器状态时出错: {str(e)}")
                    
                    # 每秒检查一次
                    time.sleep(1)
            else:
                # 如果没有获取到默认播放器名称，使用原始的等待逻辑
                try:
                    # 从download_result中获取duration信息
                    duration = download_result.get("duration", "")
                    if duration:
                        minutes, seconds = map(int, duration.split(':'))
                        total_seconds = minutes * 60 + seconds
                        logger.info(f"等待 {total_seconds} 秒后播放下一首...")
                        time.sleep(total_seconds + 2)  # 加2秒的缓冲时间
                except ValueError:
                    logger.warning("无效的时长格式，直接播放下一首")
                    time.sleep(2)  # 给播放器启动时间
                
        except Exception as e:
            logger.error(f"处理歌曲 mid: {mid} 时发生错误: {str(e)}")
            failure_count += 1
            logger.error(f"当前连续失败次数: {failure_count}/{max_failures}")
            if failure_count >= max_failures:
                logger.error(f"连续失败达到{max_failures}次，停止批量播放任务")
                break
            continue
    
    if failure_count < max_failures:
        logger.info("批量播放任务正常已完成")
    else:
        logger.error(f"批量播放任务因连续{max_failures}次失败而终止")