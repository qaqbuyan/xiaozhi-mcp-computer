import os
import logging
import platform

logger = logging.getLogger('默认方式')

def get_default_file_handler(file_extension: str) -> dict:
    """获取指定文件后缀的系统默认打开方式
    
    Args:
        file_extension (str): 文件后缀名，可以带点（如.mp3）或不带点（如mp3）
        
    Returns:
        dict: 包含success和result两个键的字典
            success: bool - 获取是否成功
            result: str - 默认程序的名称（包括后缀名），如果失败则返回错误信息
    """
    logger.info(f"获取文件后缀 {file_extension} 的默认打开方式")
    try:
        system = platform.system()
        
        # 确保文件后缀名带有点号
        if file_extension and not file_extension.startswith('.'):
            file_extension = '.' + file_extension
        elif not file_extension:
            msg = "文件后缀名不能为空"
            logger.error(msg)
            return {
                "success": False,
                "result": msg
            }
        
        if system == "Windows":
            # 在Windows系统中，通过注册表获取默认打开方式
            try:
                import winreg
                
                # 打开HKEY_CLASSES_ROOT键
                with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, file_extension) as key:
                    # 获取该文件类型的关联程序ID
                    prog_id, _ = winreg.QueryValueEx(key, "")
                    
                # 打开该程序ID对应的shell\open\command键
                command_path = f"{prog_id}\\shell\\open\\command"
                with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, command_path) as key:
                    # 获取默认命令行
                    command, _ = winreg.QueryValueEx(key, "")
                    
                    # 提取程序路径（去除参数）
                    import re
                    # 正则表达式匹配引号内的路径或直接路径
                    match = re.match(r'^"([^"]+)"|^([^\s]+)', command)
                    if match:
                        program_path = match.group(1) or match.group(2)
                        # 只返回程序的名称（包括后缀名），不返回完整路径
                        program_name = os.path.basename(program_path)
                        logger.info(f"Windows查询默认应用程序成功: {program_name}")
                        return {
                            "success": True,
                            "result": program_name
                        }
                    else:
                        msg = f"未找到文件类型 '{file_extension}' 的关联程序"
                        logger.error(msg)
                        return {
                            "success": False,
                            "result": msg
                        }
                        
            except FileNotFoundError:
                msg = f"未找到文件类型 '{file_extension}' 的关联程序"
                logger.error(msg)
                return {
                    "success": False,
                    "result": msg
                }
            except Exception as e:
                msg = f"读取注册表失败: {str(e)}"
                logger.error(msg)
                return {
                    "success": False,
                    "result": msg
                }
        elif system == "Darwin":  # macOS
            # 在macOS系统中，使用LaunchServices
            try:
                import subprocess
                
                # 使用duti命令获取默认应用程序
                # 注意：duti命令可能需要单独安装（使用brew install duti）
                result = subprocess.run(
                    ["duti", "-x", file_extension.lstrip('.')],
                    capture_output=True, text=True, timeout=10
                )
                
                if result.returncode == 0:
                    # 解析输出结果
                    output_lines = result.stdout.strip().split('\n')
                    if len(output_lines) >= 1:
                        app_name = output_lines[0].strip()
                        logger.info(f"duti命令获取默认应用程序成功: {app_name}")
                        return {
                            "success": True,
                            "result": app_name
                        }
                    else:
                        msg = f"duti命令返回空输出: {result.stdout}"
                        logger.error(msg)
                        return {
                            "success": False,
                            "result": msg
                        }
                else:
                    # 如果duti不可用，尝试使用osascript
                    script = f'tell application "Finder" to get name of (application file id (do shell script "defaults read NSGlobalDomain NSHandler{file_extension}"))'
                    result = subprocess.run(
                        ["osascript", "-e", script],
                        capture_output=True, text=True, timeout=10
                    )
                    
                    if result.returncode == 0 and result.stdout.strip():
                        app_name = result.stdout.strip()
                        logger.info(f"osascript获取默认应用程序成功: {app_name}")
                        return {
                            "success": True,
                            "result": app_name
                        }
                    else:
                        msg = f"osascript获取默认应用程序失败: {result.stderr or '未知错误'}"
                        logger.error(msg)
                        return {
                            "success": False,
                            "result": msg
                        }
                        
            except Exception as e:
                msg = f"获取默认应用程序失败: {str(e)}"
                logger.error(msg)
                return {
                    "success": False,
                    "result": msg
                }
        else:  # Linux和其他系统
            # 在Linux系统中，使用xdg-mime命令
            try:
                import subprocess
                
                result = subprocess.run(
                    ["xdg-mime", "query", "default", f"application/{file_extension.lstrip('.')}"],
                    capture_output=True, text=True, timeout=10
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    # 得到的是.desktop文件，提取应用名称
                    desktop_file = result.stdout.strip()
                    app_name = os.path.splitext(desktop_file)[0]
                    logger.info(f"xdg-mime查询默认应用程序成功: {app_name}")
                    return {
                        "success": True,
                        "result": app_name
                    }
                else:
                    msg = f"xdg-mime查询默认应用程序失败: {result.stderr or '未知错误'}"
                    logger.error(msg)
                    return {
                        "success": False,
                        "result": msg
                    }
                    
            except Exception as e:
                msg = f"获取默认应用程序失败: {str(e)}"
                logger.error(msg)
                return {
                    "success": False,
                    "result": msg
                }
                
    except Exception as e:
        msg = f"获取默认打开方式时发生错误: {str(e)}"
        logger.error(msg)
        return {
            "success": False,
            "result": msg
        }