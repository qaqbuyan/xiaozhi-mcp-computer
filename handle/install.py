import logging
import subprocess
from handle.loader import load_config

logger = logging.getLogger('依赖安装')

def install_requirements(requirements: str):
    """安装环境依赖"""
    if not requirements:
        logger.info("没有需要安装的依赖包")
        return True
    
    # 加载配置
    config = load_config()
    module_config = config.get('module', {})
    system_install = module_config.get('system', True)
    source = module_config.get('source', '')
    
    # 构建pip命令
    pip_command = ['pip', 'install']
    
    # 根据配置决定安装方式
    if not system_install:
        pip_command.append('--user')
    
    # 添加下载源（仅当是有效的URL时）
    if source and (source.startswith('http://') or source.startswith('https://')):
        pip_command.extend(['-i', source])
    
    # 添加依赖包（空格分隔）
    requirements_list = requirements.split()
    pip_command.extend(requirements_list)
    
    logger.info(f"开始安装依赖包: {' '.join(pip_command)}")
    
    try:
        # 执行pip安装命令
        result = subprocess.run(pip_command, capture_output=True, text=True, check=True)
        logger.info(f"依赖包安装成功: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"依赖包安装失败: {e.stderr}")
        return False