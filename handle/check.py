import re
import sys
import logging
import subprocess
from handle.logger import setup_logging
from handle.requirements import requirements

logger = setup_logging()
logger = logging.getLogger('环境检查')

def check_packages():
    logger.info('检查环境...')
    # 将需求字符串转换为列表
    req_list = [req.strip() for req in requirements.strip().split('\n')]
    missing_packages = []
    # 获取已安装的库列表
    try:
        installed_packages_output = subprocess.check_output([sys.executable, '-m', 'pip', 'list', '--format=freeze'], stderr=subprocess.PIPE, text=True, encoding='utf-8')
        installed_packages = installed_packages_output.lower().split('\n')
    except subprocess.CalledProcessError as e:
        logger.error(f'获取已安装库列表时出错: {e.stderr}')
        installed_packages = []  # 出错时设置为空列表，继续后续检查
    # 检查每个包是否安装
    for req in req_list:
        # 提取包名和版本要求，使用正则表达式正确提取包名
        package_name = re.split(r'>=|==|<=|<|>|~=', req)[0].strip().lower()
        # 检查包是否在已安装列表中
        found = False
        for installed in installed_packages:
            if installed.startswith(package_name.lower()):
                found = True
                break
        if not found:
            missing_packages.append(req)
    if missing_packages:
        logger.info('发现缺失的库，正在安装...')
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                logger.info(f'{package} 安装成功')
            except subprocess.CalledProcessError:
                logger.error(f'{package} 安装失败')
    else:
        logger.info('所有环境都已安装')