import os
import asyncio
import logging
import threading
import subprocess
from utils.file.default_handler import get_default_file_handler
from utils.speaker.get_audio_sessions import get_all_audio_sessions
from utils.music.monitor_player import monitor_player_status

logger = logging.getLogger('音乐播放')

def get_music_extension(file_path: str) -> str:
    """从文件路径中获取文件后缀名并验证是否为有效的音频格式
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        str: 有效的文件后缀名（如'.mp3'），如果无效则返回空字符串
    """
    # 有效的音频格式列表
    valid_audio_extensions = ['.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac']
    
    # 提取后缀名
    file_extension = os.path.splitext(file_path)[1].lower()
    
    # 检查是否为有效的音频格式
    if file_extension and file_extension in valid_audio_extensions:
        return file_extension
    
    # 如果无效，返回空字符串
    return ""

def play_music(file_path, duration_str="", skip_audio_check=True):
    logger.info("播放音乐")
    if not file_path:
        msg = "错误：文件路径为空"
        logger.error(msg)
        return {
            "success": False,
            "result": msg
        }
    
    # 处理相对路径
    if not os.path.isabs(file_path):
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path)
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        msg = f"错误：文件不存在 - {file_path}"
        logger.error(msg)
        return {
            "success": False,
            "result": msg
        }
    
    # 检查文件是否为音频文件
    music_extension = get_music_extension(file_path)
    if not music_extension:
        file_ext = os.path.splitext(file_path)[1].lower()
        valid_audio_extensions = ['.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac']
        msg = f"错误：不支持的音频格式 - {file_ext}，支持的格式: {', '.join(valid_audio_extensions)}"
        logger.error(msg)
        return {
            "success": False,
            "result": msg
        }

    # 检测系统音频状态
    default_handler = get_default_file_handler(music_extension)
    if default_handler["success"]:
        # 只有当skip_audio_check为False时才检测系统音频状态
        if not skip_audio_check:
            # 获取所有音频会话
            audio_sessions = get_all_audio_sessions()
            
            if audio_sessions["success"]:
                # 提取所有活动的音频会话
                active_sessions = [session for session in audio_sessions['result'] if session['is_active']]
                
                if active_sessions:
                    # 收集所有活动的应用名称
                    active_app_names = [session['app_name'] for session in active_sessions]
                    # 去重，确保每个应用只计算一次
                    unique_active_apps = list(set(active_app_names))
                    
                    # 获取默认播放器名称（去除.exe扩展名）
                    default_player = default_handler['result']
                    if default_player.lower().endswith('.exe'):
                        default_player = default_player[:-4]
                    
                    msg = f"检测到系统正在播放音频: {', '.join(unique_active_apps)}"
                    logger.info(msg)
                    
                    # 检查情况1：有多个程序正在播放音频
                    if len(unique_active_apps) > 1:
                        msg = f"检测到多个程序正在播放音频的程序: {', '.join(unique_active_apps)}"
                        logger.info(msg)
                        return {
                            "success": False,
                            "result": msg
                        }
                    # 检查情况2：只有一个程序播放音频，但不是默认播放器
                    elif len(unique_active_apps) == 1 and unique_active_apps[0] != default_player:
                        msg = f"检测到非默认播放器 {unique_active_apps[0]} 正在播放音频，暂停播放音乐"
                        logger.info(msg)
                        return {
                            "success": False,
                            "result": msg
                        }
    
    try:
        import platform
        system = platform.system()
        
        if system == "Windows":
            # Windows系统使用start命令
            subprocess.run(["start", "", file_path], shell=True, check=True)
        elif system == "Darwin":
            # macOS系统使用open命令
            subprocess.run(["open", file_path], check=True)
        else:
            # Linux系统使用xdg-open命令
            subprocess.run(["xdg-open", file_path], check=True)
        
        # 解析时长字符串为秒
        try:
            msg = f"默认播放器: {default_handler['result']}，时长: {duration_str}"
            logger.info(msg)
            minutes, seconds = map(int, duration_str.split(':'))
            total_seconds = minutes * 60 + seconds
            # 启动一个新线程来运行异步监控任务
            monitor_thread = threading.Thread(
                target=lambda: asyncio.run(
                    monitor_player_status(
                        default_handler['result'], 
                        total_seconds,
                        os.path.basename(file_path)
                    )
                )
            )
            monitor_thread.daemon = True  # 设置为守护线程，主线程结束时自动终止
            monitor_thread.start()
        except ValueError:
            msg = f"无效的时长格式 '{duration_str}'，监控功能未启动"
            logger.warning(msg)
        
        msg = f"已使用系统默认播放器打开: {os.path.basename(file_path)}"
        logger.info(msg)
        return {
            "success": True,
            "result": msg
        }
        
    except subprocess.CalledProcessError as e:
        msg = f"系统播放器启动失败: {str(e)}"
        logger.error(msg)
        return {
            "success": False,
            "result": f"系统播放器启动失败: {str(e)}"
        }
    except Exception as e:
        msg = f"播放失败: {str(e)}"
        logger.error(msg)
        return {
            "success": False,
            "result": msg
        }