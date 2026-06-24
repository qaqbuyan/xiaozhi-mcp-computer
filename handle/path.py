import os
import sys

def get_config_path():
    """配置文件获取器"""
    env_path = os.environ.get('MCP_CONFIG_PATH')
    if env_path and os.path.exists(env_path):
        return env_path

    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        return os.path.join(exe_dir, 'config.yaml')
    else:
        return os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'config.yaml'
        )