import os
import yaml
import platform
from handle.path import get_config_path

_config_cache = None

def load_config():
    """配置加载器"""
    global _config_cache
    if _config_cache is not None:
        return _config_cache
    config_path = get_config_path()
    try:
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"没有找到配置文件: {config_path}")
        with open(config_path, encoding='utf-8') as f:
            _config_cache = yaml.safe_load(f)
        # 获取配置中的版本号
        version = _config_cache.get('version', 'unknown')
        # 获取系统信息
        system = platform.system()
        release = platform.release()
        architecture = platform.architecture()[0]
        if system == 'Windows':
            # 使用 platform.win32_ver() 获取更详细的系统信息
            win32_ver = platform.win32_ver()
            nt_version = win32_ver[1]
            arch_str = 'x64' if architecture == '64bit' else 'x32'
            system_info = f"Windows NT {nt_version}; {arch_str}"
        else:
            # 对于非 Windows 系统，保持原逻辑
            system_info = platform.platform()
        # 生成 user_agent
        _config_cache['user_agent'] = f"mcp_control_the_computer/{version}({system_info})"
        return _config_cache
    except Exception as e:
        raise