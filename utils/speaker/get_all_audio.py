import logging

logger = logging.getLogger('获取音频会话')

def get_all_audio_sessions(log=True) -> dict:
    
    try:
        if log:
            logger.info("开始获取所有正在运行的音频会话...")
        import platform
        system = platform.system()
        
        if system == "Windows":
            try:
                # 尝试导入pycaw库来访问Windows Core Audio API
                from pycaw.pycaw import AudioUtilities
                # 导入pythoncom库用于初始化COM组件
                import pythoncom
                
                # 初始化COM组件
                pythoncom.CoInitialize()
                
                try:
                    # 获取所有音频会话
                    sessions = AudioUtilities.GetAllSessions()
                    audio_sessions = []
                    
                    # 遍历所有会话，收集会话信息
                    for session in sessions:
                        if session.Process:
                            app_name = session.Process.name()
                            # 去除 .exe 扩展名
                            if app_name.lower().endswith('.exe'):
                                app_name = app_name[:-4]
                            volume = session.SimpleAudioVolume.GetMasterVolume()
                            # 检查会话是否在活动状态
                            is_active = session.State == 1  # State 1 表示活动状态
                            
                            audio_sessions.append({
                                "app_name": app_name,
                                "volume": volume,
                                "is_active": is_active
                            })
                    
                    if not audio_sessions:
                        msg = "未找到任何正在运行的音频会话"
                        if log:
                            logger.warning(msg)
                        return {"success": False, "result": msg}
                    
                    if log:
                        logger.info(f"成功获取到 {len(audio_sessions)} 个音频会话")
                    return {"success": True, "result": audio_sessions}
                finally:
                    # 清理COM组件
                    pythoncom.CoUninitialize()
                
            except ImportError as e:
                # 如果pycaw库或pythoncom库不可用，返回错误信息
                error_msg = f"所需库不可用: {str(e)}"
                logger.error(error_msg)
                return {"success": False, "result": error_msg}
        else:
            # 对于非Windows系统，返回不支持的信息
            error_msg = f"不支持的操作系统: {system}"
            logger.error(error_msg)
            return {"success": False, "result": error_msg}
            
    except Exception as e:
        error_msg = f"获取音频会话时出错: {e}"
        logger.error(error_msg)
        return {"success": False, "result": error_msg}