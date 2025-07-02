import os

def get_config_path():
    """配置文件获取器"""
    return os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'config.yaml'
    )