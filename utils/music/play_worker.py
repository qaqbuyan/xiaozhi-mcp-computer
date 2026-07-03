import os
import sys
import time
import psutil
import logging
import threading
from utils.music.music import Music
from handle.loader import load_config
from utils.music.play import play_music, playback_manager
from utils.file.default_handler import get_default_file_handler
from utils.speaker.get_audio_sessions import get_all_audio_sessions

logger = logging.getLogger('播放线程')

def _terminate_self_and_children():
    """终止当前进程的所有子进程，然后退出自身"""
    try:
        current_pid = os.getpid()
        me = psutil.Process(current_pid)
        for child in me.children(recursive=True):
            try:
                child.terminate()
                child.wait(timeout=3)
            except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                pass
            except psutil.AccessDenied:
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    pass
    except Exception as e:
        logger.warning(f"终止子进程时出错: {e}")
    finally:
        # 强制退出当前后台进程，避免变成孤儿进程继续播放
        os._exit(1)

def _watch_parent_process(parent_pid, check_interval=3):
    """监控父进程状态，父进程退出时终止自身及所有子进程

    Args:
        parent_pid (int): 父进程PID
        check_interval (int): 检查间隔（秒）
    """
    logger.info(f"启动父进程监控，父进程PID: {parent_pid}，检查间隔: {check_interval}秒")
    while True:
        try:
            if not psutil.pid_exists(parent_pid):
                logger.warning(f"父进程 {parent_pid} 已不存在，准备终止自身及子进程")
                # 父进程退出前清理内存中的暂停队列和暂停歌单
                try:
                    playback_manager.paused_queue.clear()
                    playback_manager.paused_song_list_mids.clear()
                    logger.info("父进程已退出，已清理暂停队列和暂停歌单")
                except Exception as e:
                    logger.warning(f"清理暂停队列时出错: {e}")
                _terminate_self_and_children()
                return
        except Exception as e:
            logger.warning(f"检查父进程状态时出错: {e}")
        time.sleep(check_interval)

def _batch_play_worker(mids, parent_pid=None):
    """批量播放音乐的后台工作函数

    Args:
        mids (list): 要处理的音乐mid值列表
        parent_pid (int, optional): 父进程PID，用于监控父进程是否存活
    """
    logger.info(f"批量播放后台进程已启动，共处理{len(mids)}首歌曲")

    # 如果指定了父进程PID，启动守护线程监控父进程存活状态
    if parent_pid is not None:
        watcher = threading.Thread(
            target=_watch_parent_process,
            args=(parent_pid,),
            daemon=True
        )
        watcher.start()
    
    # 添加失败计数器
    failure_count = 0
    max_failures = 3
    
    # 创建Music实例（只创建一次）
    music_player = Music()
    
    for i, mid in enumerate(mids, 1):
        # 每次循环先检查是否收到停止播放请求
        if playback_manager.stop_requested:
            logger.info("收到停止播放请求，终止批量下载任务")
            break

        logger.info(f"处理第{i}/{len(mids)}首歌曲，mid: {mid}")

        try:
            # 1. 获取音乐mid信息
            music_info_result = music_player.get_music_mid_info(mid)
            
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
            download_result = music_player.process_music_info(music_info_result)
            
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
            
            # 播放音乐（使用播放队列）
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

            # 更新 playback_manager 中的当前歌单索引（0 开始）
            try:
                playback_manager.current_song_list_index = i - 1
            except Exception as e:
                logger.warning(f"更新当前歌单索引时出错: {e}")

            logger.info(f"第 {i}/{len(mids)} 首歌曲处理完成")
            logger.info(f"正在播放: {download_result.get('song_name', '')} - {download_result.get('singer_name', '')} - {download_result.get('album_name', '')}")

            # 等待当前歌曲播放完成（使用播放队列机制）
            try:
                # 获取默认播放器名称用于监控
                default_player_name = ""
                try:
                    # 从下载结果中获取文件路径，避免重复获取默认播放器
                    file_path = download_result.get("file_path", "")
                    if file_path and os.path.exists(file_path):
                        # 直接从文件路径获取扩展名，避免重复调用
                        music_extension = os.path.splitext(file_path)[1].lower()
                        # 获取默认播放器
                        default_handler = get_default_file_handler(music_extension)
                        if default_handler and default_handler.get("success", False):
                            default_player_name = default_handler['result']
                            if default_player_name.lower().endswith('.exe'):
                                default_player_name = default_player_name[:-4]
                except Exception as e:
                    logger.error(f"获取默认播放器名称时出错: {str(e)}")

                # 如果获取到了默认播放器名称，监控播放状态
                if default_player_name:
                    logger.info(f"开始监控默认播放器 '{default_player_name}' 的状态")
                    
                    # 初始化状态标记
                    player_was_active = False
                    paused = False
                    pause_start_time = 0
                    playback_start_time = time.time()  # 记录播放开始时间
                    expected_duration_seconds = 0  # 预期的歌曲时长（秒）
                    
                    # 给播放器一点启动时间，特别是第一首歌启动播放器时需要时间
                    logger.info(f"等待播放器 '{default_player_name}' 启动...")
                    time.sleep(1)  # 等待1秒让播放器启动
                    
                    # 尝试解析预期时长
                    try:
                        duration = download_result.get("duration", "")
                        if duration:
                            minutes, seconds = map(int, duration.split(':'))
                            expected_duration_seconds = minutes * 60 + seconds
                    except ValueError:
                        pass  # 无效的时长格式，忽略
                    
                    # 循环检测播放器状态
                    max_wait_time = 600  # 最大等待10分钟
                    wait_start_time = time.time()
                    
                    while time.time() - wait_start_time < max_wait_time:
                        try:
                            # 获取所有音频会话
                            audio_sessions_result = get_all_audio_sessions(False)
                            
                            if not audio_sessions_result["success"]:
                                logger.warning(f"获取音频会话失败: {audio_sessions_result.get('result', '未知错误')}")
                                time.sleep(5)  # 失败时等待更长时间
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
                            
                            # 如果播放器不在音频会话中，认为播放完成
                            if not player_in_session:
                                logger.info(f"默认播放器 '{default_player_name}' 不在音频会话中，播放完成")
                                break
                            
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
                                    logger.info(f"歌曲已接近预期时长（{elapsed_time:.1f}/{expected_duration_seconds}秒，{elapsed_time/expected_duration_seconds*100:.1f}%），播放完成")
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
                                max_song_wait_time = expected_duration_seconds * 3  # 设置最大等待时间为歌曲时长的3倍
                                
                                if paused and (time.time() - pause_start_time) > max_song_wait_time:
                                    if pause_interval:
                                        logger.info(f"暂停时间过长（超过{max_song_wait_time}秒），继续播放下一首")
                                        break  # 退出监控循环，继续播放下一首
                                    else:
                                        logger.info(f"暂停时间过长（超过{max_song_wait_time}秒），停止整个批量播放任务")
                                        return  # 直接返回，停止整个批处理流程
                            
                        except Exception as e:
                            logger.warning(f"检测播放器状态时出错: {str(e)}")
                        
                        # 每5秒检查一次，减少系统负载
                        time.sleep(5)
                    
                    # 检查是否超时
                    if time.time() - wait_start_time >= max_wait_time:
                        logger.warning(f"等待播放完成超时（{max_wait_time}秒），继续下一首")
                else:
                    # 如果没有获取到默认播放器名称，使用简单的等待逻辑
                    try:
                        # 从download_result中获取duration信息
                        duration = download_result.get("duration", "")
                        if duration:
                            minutes, seconds = map(int, duration.split(':'))
                            total_seconds = minutes * 60 + seconds
                            logger.info(f"等待 {total_seconds} 秒后播放下一首...")
                            time.sleep(total_seconds + 5)  # 加5秒的缓冲时间
                    except ValueError:
                        logger.warning("无效的时长格式，等待30秒后继续")
                        time.sleep(30)  # 默认等待30秒
                
            except Exception as e:
                logger.warning(f"等待播放完成时出错: {str(e)}，继续下一首")
                time.sleep(5)  # 出错时等待5秒后继续
                
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