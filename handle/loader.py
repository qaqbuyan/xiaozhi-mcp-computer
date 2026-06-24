import os
import yaml
import platform
from handle.path import get_config_path

_config_cache = None
_config_mtime = None

def _read_config():
    """实际读取配置文件并注入派生字段"""
    config_path = get_config_path()
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"没有找到配置文件: {config_path}")

    with open(config_path, encoding='utf-8') as f:
        config = yaml.safe_load(f)

    version = config.get('version', 'unknown')

    system = platform.system()
    architecture = platform.architecture()[0]
    if system == 'Windows':
        win32_ver = platform.win32_ver()
        nt_version = win32_ver[1]
        arch_str = 'x64' if architecture == '64bit' else 'x32'
        system_info = f"Windows NT {nt_version}; {arch_str}"
    else:
        system_info = platform.platform()

    endpoint_url = config.get('endpoint', {}).get('url', '')
    token = ""
    ai_api_base = ""
    if 'token=' in endpoint_url:
        token = endpoint_url.split('token=')[1]
    if endpoint_url.startswith('wss://'):
        domain_part = endpoint_url[6:].split('/')[0]
        ai_api_base = domain_part
    elif endpoint_url.startswith('ws://'):
        domain_part = endpoint_url[5:].split('/')[0]
        ai_api_base = domain_part

    config['token'] = token
    config['ai_api_base'] = ai_api_base
    config['user_agent'] = f"mcp_control_the_computer/{version}({system_info})"
    return config

def load_config():
    """配置加载器（带修改时间校验的缓存）"""
    global _config_cache, _config_mtime

    config_path = get_config_path()
    try:
        current_mtime = os.path.getmtime(config_path)
    except OSError:
        _config_cache = _read_config()
        _config_mtime = 0
        return _config_cache

    if _config_cache is not None and _config_mtime == current_mtime:
        return _config_cache

    _config_cache = _read_config()
    _config_mtime = current_mtime
    return _config_cache


def reload_config():
    """强制重新加载配置文件"""
    global _config_cache, _config_mtime
    config_path = get_config_path()
    _config_cache = _read_config()
    _config_mtime = os.path.getmtime(config_path)
    return _config_cache