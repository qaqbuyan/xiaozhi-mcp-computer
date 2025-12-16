import os
import sys
import time
import atexit
import signal
import psutil
import asyncio
import logging
import threading
import subprocess
from utils.is_process_running import is_process_running
from utils.music.monitor_player import monitor_player_status
from utils.file.default_handler import get_default_file_handler
from utils.speaker.get_audio_sessions import get_all_audio_sessions

logger = logging.getLogger('音乐播放')

# 全局进程管理器
class GlobalProcessManager:
    """全局进程管理器，确保所有子进程都能被正确清理"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.all_processes = []  # 所有需要管理的进程
        self.process_lock = threading.Lock()
        self.cleanup_registered = False
        self._register_cleanup_handlers()
    
    def _register_cleanup_handlers(self):
        """注册清理处理器"""
        if not self.cleanup_registered:
            # 注册atexit处理器
            atexit.register(self.cleanup_all_processes)
            
            # 注册信号处理器
            def signal_handler(signum, frame):
                logger.info(f"收到信号 {signum}，开始清理所有进程...")
                self.cleanup_all_processes()
                sys.exit(0)
            
            # 注册常见终止信号
            for sig in [signal.SIGINT, signal.SIGTERM, signal.SIGBREAK]:
                try:
                    signal.signal(sig, signal_handler)
                except (OSError, ValueError):
                    pass  # 某些信号在某些平台上不可用
            
            self.cleanup_registered = True
    
    def add_process(self, process):
        """添加进程到管理列表"""
        with self.process_lock:
            self.all_processes.append(process)
            logger.info(f"添加进程到管理列表: PID {process.pid if hasattr(process, 'pid') else 'unknown'}")
    
    def remove_process(self, process):
        """从管理列表移除进程"""
        with self.process_lock:
            if process in self.all_processes:
                self.all_processes.remove(process)
                logger.info(f"从管理列表移除进程: PID {process.pid if hasattr(process, 'pid') else 'unknown'}")
    
    def cleanup_all_processes(self):
        """清理所有管理的进程"""
        with self.process_lock:
            if not self.all_processes:
                return
            
            logger.info(f"开始清理 {len(self.all_processes)} 个管理的进程...")
            terminated_count = 0
            
            for process in self.all_processes[:]:
                try:
                    if hasattr(process, 'is_alive') and process.is_alive():
                        # multiprocessing.Process
                        process.terminate()
                        process.join(timeout=3)
                        if process.is_alive():
                            process.kill()
                        terminated_count += 1
                        logger.info(f"已终止multiprocessing进程: PID {process.pid}")
                    
                    elif hasattr(process, 'poll') and process.poll() is None:
                        # subprocess.Popen
                        process.terminate()
                        try:
                            process.wait(timeout=3)
                        except subprocess.TimeoutExpired:
                            process.kill()
                        terminated_count += 1
                        logger.info(f"已终止subprocess进程: PID {process.pid}")
                    
                    else:
                        # 尝试通过PID终止
                        if hasattr(process, 'pid') and process.pid:
                            try:
                                parent = psutil.Process(process.pid)
                                for child in parent.children(recursive=True):
                                    child.terminate()
                                parent.terminate()
                                parent.wait(timeout=3)
                                terminated_count += 1
                                logger.info(f"已终止进程树: PID {process.pid}")
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                pass
                
                except Exception as e:
                    logger.warning(f"终止进程失败: {str(e)}")
            
            self.all_processes.clear()
            logger.info(f"进程清理完成，共终止 {terminated_count} 个进程")


# 全局播放状态管理
class MusicPlaybackManager:
    """音乐播放状态管理器"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.process_manager = GlobalProcessManager()  # 获取进程管理器实例
        self.is_playing = False
        self.current_file = None
        self.current_player = None
        self.current_song_name = None
        self.current_singer_name = None
        self.play_queue = []
        self.queue_lock = threading.Lock()
        self.playback_lock = threading.Lock()
        self.stop_requested = False
        self.current_song_list_id = None
        self.active_processes = []  # 记录所有活动的播放器进程
        
        # 初始化时清理所有临时音乐文件
        try:
            # 获取当前工作目录下的tmp文件夹路径
            current_working_dir = os.getcwd()
            tmp_dir = os.path.join(current_working_dir, "tmp")
            
            if os.path.exists(tmp_dir):
                # 删除所有以"music_"开头的音乐文件
                for filename in os.listdir(tmp_dir):
                    if filename.startswith("music_") and filename.endswith((".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac")):
                        tmp_file_path = os.path.join(tmp_dir, filename)
                        try:
                            os.remove(tmp_file_path)
                            logger.info(f"初始化时已删除临时音乐文件: {filename}")
                        except (IOError, PermissionError) as e:
                            logger.warning(f"初始化时无法删除临时音乐文件 {filename}: {str(e)}")
        except Exception as e:
            logger.error(f"初始化时清理临时音乐文件发生错误: {str(e)}")
    
    def add_to_queue(self, file_path, duration_str="", song_name="", singer_name=""):
        """添加音乐到播放队列
        
        Args:
            file_path (str): 音乐文件路径
            duration_str (str): 音乐时长字符串
            song_name (str): 歌曲名称
            singer_name (str): 歌手名称
            
        Returns:
            int: 新添加歌曲在队列中的位置（从1开始）
        """
        with self.queue_lock:
            # 在添加前计算队列长度，这样显示的是添加前的队列状态
            queue_length_before = len(self.play_queue)
            
            # 创建歌曲信息对象
            song_info = {
                "file_path": file_path, 
                "duration": duration_str,
                "song_name": song_name or os.path.basename(file_path),
                "singer_name": singer_name or ""
            }
            self.play_queue.append(song_info)
            
            # 返回新歌曲在队列中的位置（队列长度，从1开始）
            return queue_length_before + 1
    
    def start_playback(self):
        """开始播放队列中的音乐"""
        if not self.is_playing:
            playback_thread = threading.Thread(target=self._playback_worker, daemon=True)
            playback_thread.start()
    
    def _playback_worker(self):
        """播放队列工作线程"""
        try:
            while True:
                # 检查是否收到停止播放请求
                with self.queue_lock:
                    if self.stop_requested:
                        self.is_playing = False
                        self.current_file = None
                        self.current_player = None
                        self.current_song_name = None
                        self.current_singer_name = None
                        self.current_song_list_id = None
                        logger.info("收到停止播放请求，停止播放")
                        break
                
                # 在获取下一首歌曲前检查队列状态
                with self.queue_lock:
                    if not self.play_queue:
                        self.is_playing = False
                        self.current_file = None
                        self.current_player = None
                        self.current_song_name = None
                        self.current_singer_name = None
                        self.current_song_list_id = None
                        logger.info("播放队列为空，停止播放")
                        break
                
                # 再次检查停止请求，避免在等待锁时错过了停止请求
                with self.queue_lock:
                    if self.stop_requested:
                        self.is_playing = False
                        self.current_file = None
                        self.current_player = None
                        self.current_song_name = None
                        self.current_singer_name = None
                        self.current_song_list_id = None
                        logger.info("收到停止播放请求，停止播放")
                        break
                
                # 从队列中获取下一首歌曲
                with self.queue_lock:
                    if self.play_queue:
                        next_song = self.play_queue.pop(0)
                        file_path = next_song["file_path"]
                        duration_str = next_song["duration"]
                        song_name = next_song.get("song_name", "")
                        singer_name = next_song.get("singer_name", "")
                        
                        # 立即记录要播放的歌曲信息，避免竞态条件
                        display_name = song_name or os.path.basename(file_path)
                        if singer_name:
                            display_name += f" - {singer_name}"
                        logger.info(f"准备播放: {display_name}")
                        
                        # 立即更新当前播放信息，确保日志一致性
                        self.current_file = file_path
                        self.current_song_name = song_name or os.path.basename(file_path)
                        self.current_singer_name = singer_name or ""
                    else:
                        # 队列为空，跳出循环
                        self.is_playing = False
                        self.current_file = None
                        self.current_player = None
                        self.current_song_name = None
                        self.current_singer_name = None
                        self.current_song_list_id = None
                        logger.info("播放队列为空，停止播放")
                        break
                
                # 再次检查停止请求，避免在处理歌曲前错过了停止请求
                with self.queue_lock:
                    if self.stop_requested:
                        self.is_playing = False
                        self.current_file = None
                        self.current_player = None
                        self.current_song_name = None
                        self.current_singer_name = None
                        self.current_song_list_id = None
                        logger.info("收到停止播放请求，停止播放")
                        break
                
                # 播放音乐（在锁外执行，避免阻塞其他操作）
                self._play_single_song(file_path, duration_str)
                
                # 播放完成后，检查是否还有下一首歌曲
                with self.queue_lock:
                    if not self.play_queue:
                        self.is_playing = False
                        self.current_file = None
                        self.current_player = None
                        self.current_song_name = None
                        self.current_singer_name = None
                        self.current_song_list_id = None
                        logger.info("播放队列为空，停止播放")
                        break
        except Exception as e:
            logger.error(f"播放线程发生错误: {str(e)}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            # 发生错误时，确保播放状态被正确重置
            with self.queue_lock:
                self.is_playing = False
                self.current_file = None
                self.current_player = None
                self.current_song_name = None
                self.current_singer_name = None
                self.current_song_list_id = None
    
    def _play_single_song(self, file_path, duration_str):
        """播放单首音乐"""
        with self.playback_lock:
            self.is_playing = True
            
            # 使用_playback_worker中已经设置的歌曲信息
            display_name = self.current_song_name
            if self.current_singer_name:
                display_name += f" - {self.current_singer_name}"
            logger.info(f"正在播放: {display_name}")
            
            try:
                # 检查文件是否存在
                if not os.path.exists(file_path):
                    logger.error(f"音乐文件不存在: {file_path}")
                    # 如果文件不存在，清理当前播放信息并删除文件
                    with self.queue_lock:
                        self.is_playing = False
                        self.current_file = None
                        self.current_player = None
                        self.current_song_name = None
                        self.current_singer_name = None
                    # 删除临时文件
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            logger.info(f"已删除不存在的临时音乐文件: {os.path.basename(file_path)}")
                        except (IOError, PermissionError) as e:
                            logger.warning(f"无法删除不存在的临时音乐文件 {os.path.basename(file_path)}: {str(e)}")
                    return
                
                # 获取默认播放器
                music_extension = get_music_extension(file_path)
                if not music_extension:
                    logger.error(f"不支持的音频格式: {file_path}")
                    # 如果格式不支持，清理当前播放信息并删除文件
                    with self.queue_lock:
                        self.is_playing = False
                        self.current_file = None
                        self.current_player = None
                        self.current_song_name = None
                        self.current_singer_name = None
                    # 删除临时文件
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            logger.info(f"已删除不支持格式的临时音乐文件: {os.path.basename(file_path)}")
                        except (IOError, PermissionError) as e:
                            logger.warning(f"无法删除不支持格式的临时音乐文件 {os.path.basename(file_path)}: {str(e)}")
                    return
                
                default_handler = get_default_file_handler(music_extension)
                if not default_handler["success"]:
                    logger.error("无法获取默认播放器")
                    # 如果无法获取默认播放器，清理当前播放信息并删除文件
                    with self.queue_lock:
                        self.is_playing = False
                        self.current_file = None
                        self.current_player = None
                        self.current_song_name = None
                        self.current_singer_name = None
                    # 删除临时文件
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            logger.info(f"已删除无法播放的临时音乐文件: {os.path.basename(file_path)}")
                        except (IOError, PermissionError) as e:
                            logger.warning(f"无法删除无法播放的临时音乐文件 {os.path.basename(file_path)}: {str(e)}")
                    return
                
                self.current_player = default_handler['result']
                if self.current_player.lower().endswith('.exe'):
                    self.current_player = self.current_player[:-4]
                
                # 等待文件可用（避免文件锁定）
                max_wait_time = 30  # 最大等待30秒
                wait_time = 0
                
                # 显示歌曲信息而不是文件名
                display_name = self.current_song_name
                if self.current_singer_name:
                    display_name += f" - {self.current_singer_name}"
                
                while wait_time < max_wait_time:
                    try:
                        # 尝试打开文件检查是否被锁定
                        with open(file_path, 'rb') as f:
                            f.read(1)  # 读取一个字节测试
                        break  # 文件可用，跳出循环
                    except (IOError, PermissionError):
                        logger.info(f"文件 {display_name} 被锁定，等待中... ({wait_time}/{max_wait_time}秒)")
                        time.sleep(1)
                        wait_time += 1
                
                if wait_time >= max_wait_time:
                    logger.error(f"文件 {display_name} 长时间被锁定，跳过播放")
                    # 如果文件长时间被锁定，清理当前播放信息并删除文件
                    with self.queue_lock:
                        self.is_playing = False
                        self.current_file = None
                        self.current_player = None
                        self.current_song_name = None
                        self.current_singer_name = None
                    # 删除临时文件
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            logger.info(f"已删除被锁定的临时音乐文件: {os.path.basename(file_path)}")
                        except (IOError, PermissionError) as e:
                            logger.warning(f"无法删除被锁定的临时音乐文件 {os.path.basename(file_path)}: {str(e)}")
                    return
                
                # 使用系统默认播放器播放
                import platform
                system = platform.system()
                
                try:
                    if system == "Windows":
                        # 使用start命令启动播放器，不等待完成
                        process = subprocess.Popen(["start", "", file_path], shell=True)
                    elif system == "Darwin":
                        process = subprocess.Popen(["open", file_path])
                    else:
                        process = subprocess.Popen(["xdg-open", file_path])
                    
                    # 记录播放器进程到全局管理器
                    self.process_manager.add_process(process)
                    
                    # 同时记录到本地列表用于快速访问
                    with self.queue_lock:
                        self.active_processes.append(process)
                    
                    logger.info(f"已使用系统默认播放器启动播放: {display_name}")
                except Exception as e:
                    logger.error(f"启动播放器失败: {str(e)}")
                    return
                
                # 监控播放状态
                if duration_str:
                    try:
                        minutes, seconds = map(int, duration_str.split(':'))
                        total_seconds = minutes * 60 + seconds
                        
                        # 启动监控线程
                        monitor_thread = threading.Thread(
                            target=lambda: asyncio.run(
                                monitor_player_status(
                                    self.current_player, 
                                    total_seconds,
                                    display_name
                                )
                            ),
                            daemon=True
                        )
                        monitor_thread.start()
                        
                        # 等待播放完成
                        monitor_thread.join(timeout=total_seconds + 10)  # 超时保护
                        
                    except ValueError:
                        logger.warning(f"无效的时长格式 '{duration_str}'，跳过监控")
                
            except Exception as e:
                logger.error(f"播放音乐失败: {str(e)}")
            finally:
                # 保存播放器名称以便后续检查
                player_name = self.current_player
                
                # 重置当前播放信息
                self.current_file = None
                self.current_player = None
                self.current_song_name = None
                self.current_singer_name = None
                
                # 删除当前播放的临时音乐文件
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        logger.info(f"已删除临时音乐文件: {os.path.basename(file_path)}")
                    except (IOError, PermissionError) as e:
                        logger.warning(f"无法删除临时音乐文件 {os.path.basename(file_path)}: {str(e)}")
                
                # 检查播放器是否仍在运行
                if player_name:
                    # 检查播放器是否在运行
                    if not is_process_running(player_name + '.exe'):
                        logger.info(f"播放器 {player_name} 已停止运行")
                        # 只清理当前正在播放的临时音乐文件，不清理所有临时文件
                        # 避免歌单切换时删除新下载的歌曲文件
                        if file_path and os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                                logger.info(f"已删除当前播放的临时音乐文件: {os.path.basename(file_path)}")
                            except (IOError, PermissionError) as e:
                                logger.warning(f"无法删除当前播放的临时音乐文件 {os.path.basename(file_path)}: {str(e)}")
                
                # 检查播放器是否仍在运行
                if self.current_file and os.path.exists(self.current_file):
                    try:
                        os.remove(self.current_file)
                        logger.info(f"已删除当前播放的临时音乐文件: {os.path.basename(self.current_file)}")
                    except (IOError, PermissionError) as e:
                        logger.warning(f"无法删除当前播放的临时音乐文件 {os.path.basename(self.current_file)}: {str(e)}")
    
    def is_music_playing(self):
        """检查是否有音乐正在播放"""
        return self.is_playing
    
    def get_current_playback_info(self):
        """获取当前播放信息"""
        with self.queue_lock:
            # 队列长度应该是等待播放的歌曲数量，不包括当前正在播放的歌曲
            queue_length = len(self.play_queue)
            
            # 构建当前播放歌曲的显示名称
            current_display_name = ""
            if self.current_file:
                if self.current_song_name:
                    current_display_name = self.current_song_name
                    if self.current_singer_name:
                        current_display_name += f" - {self.current_singer_name}"
                else:
                    current_display_name = os.path.basename(self.current_file)
            
            return {
                "is_playing": self.is_playing,
                "current_file": self.current_file,
                "current_player": self.current_player,
                "current_display_name": current_display_name,
                "current_song_name": self.current_song_name,
                "current_singer_name": self.current_singer_name,
                "queue_length": queue_length,
                "current_song_list_id": self.current_song_list_id
            }
    
    def clear_queue_and_play_song_list(self, song_list_data, song_list_id=None):
        """清理当前队列并播放新的歌单
        
        Args:
            song_list_data (list): 新的歌单数据
            song_list_id (str): 歌单ID，用于标识当前播放的歌单
        """
        logger.info(f"开始清理队列并播放新歌单，共{len(song_list_data)}首歌曲，歌单ID: {song_list_id}")
        
        # 立即执行快速操作：停止当前播放、清理队列、设置新状态
        # 1. 请求停止当前播放线程（如果正在播放）
        with self.queue_lock:
            if self.is_playing:
                logger.info("检测到当前有播放线程在运行，请求停止")
                self.stop_requested = True
        
        # 2. 快速清理队列并重置状态（不等待线程完全停止）
        with self.queue_lock:
            # 确保停止请求标志为False
            self.stop_requested = False
            
            # 清理当前播放队列
            self.play_queue.clear()
            
            # 设置新的歌单ID
            self.current_song_list_id = song_list_id
            
            logger.info(f"已快速清理队列并准备添加新的歌单，共{len(song_list_data)}首歌曲，歌单ID: {song_list_id}")
        
        # 3. 提取mid列表
        mids_to_process = [song.get('mid', '') for song in song_list_data if song.get('mid')]
        
        if not mids_to_process:
            logger.error("没有有效的歌曲mid列表，无法启动歌单播放")
            return
        
        # 4. 立即启动后台进程处理歌曲下载
        try:
            # 导入需要的模块
            from utils.music.play_worker import _batch_play_worker
            import multiprocessing
            
            # 创建后台进程，设置为daemon=True，当主进程退出时自动终止
            process = multiprocessing.Process(
                target=_batch_play_worker,
                args=(mids_to_process,)
            )
            process.daemon = True
            process.start()
            
            # 注册到全局进程管理器
            self.process_manager.add_process(process)
            
            logger.info("已立即启动歌单播放后台进程")
            
        except Exception as e:
            logger.error(f"启动歌单播放后台进程失败: {str(e)}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return  # 如果进程启动失败，直接返回
        
        # 5. 立即启动播放线程（不等待后台进程）
        try:
            logger.info("准备立即启动播放线程")
            self.start_playback()
            logger.info("播放线程已立即启动")
        except Exception as e:
            logger.error(f"启动播放线程失败: {str(e)}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
        
        # 6. 启动后台线程处理清理和等待工作（不阻塞主流程）
        def _background_cleanup():
            try:
                # 等待播放线程停止（最多等待10秒）
                wait_time = 0
                max_wait_time = 10
                while self.is_playing and wait_time < max_wait_time:
                    time.sleep(0.5)
                    wait_time += 0.5
                    logger.info(f"后台等待当前播放线程停止... ({wait_time}/{max_wait_time}秒)")
                
                if self.is_playing:
                    logger.warning(f"当前播放线程在{max_wait_time}秒内未停止，后台强制清理资源")
                    # 强制重置播放状态
                    with self.queue_lock:
                        self.is_playing = False
                        self.current_file = None
                        self.current_player = None
                        self.current_song_name = None
                        self.current_singer_name = None
                else:
                    logger.info("后台检测到当前播放线程已成功停止")
            except Exception as e:
                logger.error(f"后台清理线程发生错误: {str(e)}")
                import traceback
                logger.error(f"详细错误信息: {traceback.format_exc()}")
        
        # 启动后台线程处理清理工作
        import threading
        thread = threading.Thread(target=_background_cleanup, daemon=True)
        thread.start()
        logger.info("后台清理任务已启动，主流程继续执行")
    
    def stop_current_playback(self):
        """停止当前播放并清理所有临时音乐文件"""
        logger.info("开始停止当前播放并清理所有临时音乐文件")
        
        # 将耗时操作放到后台线程中执行，避免阻塞主线程
        def _stop_and_cleanup():
            try:
                # 1. 请求停止播放
                with self.queue_lock:
                    self.stop_requested = True
                    self.play_queue.clear()
                    logger.info("已请求停止当前播放并清理队列")
                
                # 2. 等待播放线程停止（最多等待10秒）
                wait_time = 0
                max_wait_time = 10
                while self.is_playing and wait_time < max_wait_time:
                    time.sleep(0.5)
                    wait_time += 0.5
                    logger.info(f"等待当前播放线程停止... ({wait_time}/{max_wait_time}秒)")
                
                if self.is_playing:
                    logger.warning(f"当前播放线程在{max_wait_time}秒内未停止，强制清理资源")
                    # 强制重置播放状态
                    with self.queue_lock:
                        self.is_playing = False
                        self.current_file = None
                        self.current_player = None
                        self.current_song_name = None
                        self.current_singer_name = None
                        self.current_song_list_id = None
                else:
                    logger.info("当前播放线程已成功停止")
                
                # 3. 终止所有活动的播放器进程
                try:
                    with self.queue_lock:
                        if self.active_processes:
                            logger.info(f"开始终止{len(self.active_processes)}个播放器进程...")
                            terminated_count = 0
                            for process in self.active_processes:
                                try:
                                    if process.poll() is None:  # 进程仍在运行
                                        process.terminate()
                                        process.wait(timeout=5)  # 等待进程终止
                                        terminated_count += 1
                                        logger.info(f"已终止播放器进程: PID {process.pid}")
                                    else:
                                        logger.info(f"播放器进程已停止: PID {process.pid}")
                                except Exception as e:
                                    logger.warning(f"终止播放器进程失败 (PID {process.pid}): {str(e)}")
                            logger.info(f"共终止{terminated_count}个播放器进程")
                            self.active_processes.clear()
                        else:
                            logger.info("没有活动的播放器进程需要终止")
                except Exception as e:
                    logger.error(f"终止播放器进程发生错误: {str(e)}")
                    import traceback
                    logger.error(f"详细错误信息: {traceback.format_exc()}")
                    
                # 4. 清理所有临时音乐文件
                try:
                    # 获取当前工作目录下的tmp文件夹路径
                    current_working_dir = os.getcwd()
                    tmp_dir = os.path.join(current_working_dir, "tmp")
                    
                    if os.path.exists(tmp_dir):
                        # 删除所有以"music_"开头的音乐文件
                        deleted_count = 0
                        for filename in os.listdir(tmp_dir):
                            if filename.startswith("music_") and filename.endswith((".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac")):
                                tmp_file_path = os.path.join(tmp_dir, filename)
                                try:
                                    os.remove(tmp_file_path)
                                    logger.info(f"已删除临时音乐文件: {filename}")
                                    deleted_count += 1
                                except (IOError, PermissionError) as e:
                                    logger.warning(f"无法删除临时音乐文件 {filename}: {str(e)}")
                        
                        logger.info(f"共清理{deleted_count}个临时音乐文件")
                    else:
                        logger.info("tmp文件夹不存在，无需清理临时音乐文件")
                except Exception as e:
                    logger.error(f"清理临时音乐文件发生错误: {str(e)}")
                    import traceback
                    logger.error(f"详细错误信息: {traceback.format_exc()}")
            except Exception as e:
                logger.error(f"停止播放并清理资源时发生错误: {str(e)}")
                import traceback
                logger.error(f"详细错误信息: {traceback.format_exc()}")
            finally:
                logger.info("停止播放并清理临时音乐文件完成")
        
        # 启动后台线程处理停止播放和清理工作
        import threading
        thread = threading.Thread(target=_stop_and_cleanup, daemon=True)
        thread.start()
        logger.info("停止播放任务已提交到后台线程处理")
    
    def cleanup_all_processes(self):
        """清理所有管理的进程"""
        logger.info("开始清理所有管理的进程...")
        terminated_count = 0
        
        try:
            # 终止所有活动的播放器进程
            with self.queue_lock:
                if self.active_processes:
                    logger.info(f"开始终止{len(self.active_processes)}个播放器进程...")
                    for process in self.active_processes[:]:
                        try:
                            if process.poll() is None:  # 进程仍在运行
                                process.terminate()
                                process.wait(timeout=5)  # 等待进程终止
                                terminated_count += 1
                                logger.info(f"已终止播放器进程: PID {process.pid}")
                            else:
                                logger.info(f"播放器进程已停止: PID {process.pid}")
                        except Exception as e:
                            logger.warning(f"终止播放器进程失败 (PID {process.pid}): {str(e)}")
                    
                    logger.info(f"共终止{terminated_count}个播放器进程")
                    self.active_processes.clear()
                else:
                    logger.info("没有活动的播放器进程需要终止")
        except Exception as e:
            logger.error(f"终止播放器进程发生错误: {str(e)}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
        
        logger.info(f"进程清理完成，共终止 {terminated_count} 个进程")
    
    def get_active_processes_info(self):
        """获取当前活跃进程信息，用于调试"""
        with self.queue_lock:
            active_processes = []
            for process in self.active_processes:
                try:
                    if hasattr(process, 'poll') and process.poll() is None:
                        active_processes.append(f"subprocess.PID:{process.pid}")
                    elif hasattr(process, 'pid') and process.pid:
                        active_processes.append(f"PID:{process.pid}")
                except:
                    pass
            return active_processes


# 全局播放管理器实例
playback_manager = MusicPlaybackManager()

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

def play_music(file_path, duration_str="", skip_audio_check=True, song_name="", singer_name=""):
    """播放音乐（使用播放队列管理）
    
    Args:
        file_path (str): 音乐文件路径
        duration_str (str): 音乐时长字符串（格式："分:秒"）
        skip_audio_check (bool): 是否跳过音频状态检查
        song_name (str): 歌曲名称
        singer_name (str): 歌手名称
        
    Returns:
        dict: 包含播放状态的字典
    """
    logger.info("播放音乐")
    
    # 基本参数验证
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

    # 检测系统音频状态（可选）
    if not skip_audio_check:
        default_handler = get_default_file_handler(music_extension)
        if default_handler["success"]:
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
    
    # 使用播放管理器处理播放
    try:
        # 获取当前播放状态信息（在添加队列前）
        playback_info_before = playback_manager.get_current_playback_info()
        is_currently_playing = playback_info_before["is_playing"]
        
        # 添加到播放队列，传递歌曲信息，并获取正确的队列位置
        queue_position = playback_manager.add_to_queue(file_path, duration_str, song_name, singer_name)
        
        # 获取当前播放状态信息（在添加队列后）
        playback_info_after = playback_manager.get_current_playback_info()
        
        # 开始播放（如果还没有在播放）
        playback_manager.start_playback()
        
        # 返回播放状态信息
        if is_currently_playing:
            # 如果当前有音乐正在播放，返回正确的队列位置信息
            msg = f"已添加到播放队列，队列位置: {queue_position}"
            if playback_info_before["current_display_name"]:
                msg += f"，当前正在播放: {playback_info_before['current_display_name']}"
        else:
            # 如果没有音乐正在播放，立即开始播放
            msg = f"已开始播放: {os.path.basename(file_path)}"
        
        return {
            "success": True,
            "result": msg,
            "queue_position": playback_info_after["queue_length"],
            "is_playing": playback_info_after["is_playing"],
            "queued": is_currently_playing
        }
        
    except Exception as e:
        msg = f"播放音乐失败: {str(e)}"
        logger.error(msg)
        return {
            "success": False,
            "result": msg
        }