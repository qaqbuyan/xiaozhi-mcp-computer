import os
import sys
import logging
import subprocess
from handle.loader import load_config

logger = logging.getLogger('依赖安装')

def detect_active_environment():
    """检测当前激活的Python环境类型"""
    env_info = []
    
    # 检测conda环境
    if 'CONDA_DEFAULT_ENV' in os.environ or 'CONDA_PREFIX' in os.environ:
        conda_env = os.environ.get('CONDA_DEFAULT_ENV', 'unknown')
        env_info.append(f"conda({conda_env})")
    
    # 检测虚拟环境
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        env_info.append("venv/virtualenv")
    
    # 检测pyenv
    try:
        subprocess.run(['pyenv', '--version'], capture_output=True, check=True)
        env_info.append("pyenv")
    except:
        pass
    
    return env_info if env_info else ["系统Python"]

def install_requirements(requirements: str):
    """安装环境依赖"""
    if not requirements:
        logger.info("没有需要安装的依赖包")
        return True
    
    # 检测当前激活的环境
    active_envs = detect_active_environment()
    logger.info(f"当前激活的环境: {', '.join(active_envs)}")
    
    # 加载配置
    config = load_config()
    module_config = config.get('module', {})
    system_install = module_config.get('system', True)
    source = module_config.get('source', '')
    environment = module_config.get('environment', '').strip()
    
    # 根据环境设置选择安装命令
    if environment:
        if 'conda' in environment.lower() or 'anaconda' in environment.lower():
            # 检查conda是否可用
            try:
                subprocess.run(['conda', '--version'], capture_output=True, check=True)
                install_command = ['conda', 'install', '-y']
                logger.info(f"检测到conda环境，使用conda安装依赖包")
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.warning(f"配置的conda环境无效，回退到默认pip安装")
                install_command = ['pip', 'install']
        elif 'pyenv' in environment.lower():
            # Windows平台提醒
            import platform
            if platform.system() == 'Windows':
                logger.warning("⚠️  pyenv在Windows上体验较差，建议优先使用Conda环境以获得更好的兼容性")
                logger.warning("   推荐环境优先级: Conda > venv/virtualenv > pyenv")
            install_command = ['pip', 'install']
        else:
            logger.warning(f"未知的环境设置: {environment}，使用默认pip安装")
            install_command = ['pip', 'install']
    else:
        logger.info("未配置环境设置，使用默认pip安装")
        install_command = ['pip', 'install']
    
    # 构建安装命令
    pip_command = install_command
    
    # 根据配置决定安装方式
    if not system_install:
        pip_command.append('--user')
    
    # 添加下载源
    if source:
        if install_command[0] == 'conda':
            # conda使用-c参数指定频道
            if not (source.startswith('http://') or source.startswith('https://')):
                # 如果是频道名称（如conda-forge）
                pip_command.extend(['-c', source])
                logger.info(f"使用conda频道: {source}")
            else:
                logger.warning(f"conda不支持URL格式的源: {source}，跳过源配置")
        elif install_command[0] == 'pip':
            # pip使用-i参数 (适用于pip/venv/virtualenv/pyenv)
            if source.startswith('http://') or source.startswith('https://'):
                pip_command.extend(['-i', source])
                logger.info(f"使用pip源: {source}")
            else:
                logger.warning(f"pip源格式无效: {source}，应为URL格式")
    
    # 添加依赖包（空格分隔）
    requirements_list = requirements.split()
    pip_command.extend(requirements_list)
    
    # 获取当前环境信息用于日志
    env_info = []
    if environment:
        env_lower = environment.lower()
        if 'conda' in env_lower:
            env_info.append("conda")
        elif 'pyenv' in env_lower:
            env_info.append("pyenv")
        elif 'venv' in env_lower or 'virtualenv' in env_lower:
            env_info.append("venv/virtualenv")
    
    install_tool = install_command[0]
    env_str = f" ({', '.join(env_info)})" if env_info else ""
    
    logger.info(f"开始安装依赖包{env_str}: {' '.join(pip_command)}")
    
    try:
        # 执行安装命令
        result = subprocess.run(pip_command, capture_output=True, text=True, check=True)
        logger.info(f"依赖包安装成功 ({install_tool}){env_str}: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"依赖包安装失败 ({install_tool}){env_str}: {e.stderr}")
        return False