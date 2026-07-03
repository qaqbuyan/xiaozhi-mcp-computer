import re
import sys
import logging
import subprocess
from handle.logger import setup_logging
from handle.requirements import requirements

logger = setup_logging()
logger = logging.getLogger('环境检查')

def _parse_requirements(requirements_str: str) -> list:
    """将需求字符串解析为依赖项列表，忽略空行和注释行。"""
    if not requirements_str:
        return []
    return [
        req.strip()
        for req in requirements_str.strip().splitlines()
        if req.strip() and not req.strip().startswith('#')
    ]

def _get_package_name(req: str) -> str:
    """从依赖项中提取包名（去掉版本限定符）。"""
    if not req:
        return ''
    return re.split(r'>=|==|<=|<|>|~=', req)[0].strip().lower()

def _normalize_package_name(name: str) -> str:
    """规范化包名：pip 把 - 和 _ 视为等价，统一转为小写并用 - 替换 _。"""
    return name.strip().lower().replace('_', '-')

def _get_installed_packages() -> list:
    """获取已安装的包列表（freeze 格式），出错时返回空列表。"""
    try:
        installed_packages_output = subprocess.check_output(
            [sys.executable, '-m', 'pip', 'list', '--format=freeze'],
            stderr=subprocess.PIPE
        )
        try:
            installed_packages_output = installed_packages_output.decode('utf-8')
        except UnicodeDecodeError:
            installed_packages_output = installed_packages_output.decode('gbk')
        return installed_packages_output.split('\n')
    except subprocess.CalledProcessError as e:
        try:
            stderr_text = e.stderr.decode('utf-8')
        except UnicodeDecodeError:
            stderr_text = e.stderr.decode('gbk')
        logger.error(f'获取已安装库列表时出错（返回码 {e.returncode}）: {stderr_text}')
        return []

def _is_package_installed(package_name: str, installed_packages: list) -> bool:
    """判断指定包名是否已安装。"""
    target = _normalize_package_name(package_name)
    if not target:
        return False
    for installed in installed_packages:
        if not installed.strip():
            continue
        # 跳过可编辑安装标记行
        if installed.strip().startswith('-e '):
            installed = installed.split(' ', 1)[-1]
        # pip freeze 格式：package==version
        installed_name = installed.split('==')[0].strip()
        if _normalize_package_name(installed_name) == target:
            return True
    return False

def _find_missing_packages(req_list: list) -> list:
    """从给定的依赖列表中找出未安装的包。"""
    installed_packages = _get_installed_packages()
    missing_packages = []
    for req in req_list:
        package_name = _get_package_name(req)
        if not _is_package_installed(package_name, installed_packages):
            missing_packages.append(req)
    return missing_packages

def _install_with_pip(package: str) -> bool:
    """使用默认 pip 安装单个包。"""
    logger.info(f'发现缺失的库 {package}，正在安装...')
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        logger.info(f'{package} 安装成功')
        return True
    except subprocess.CalledProcessError:
        logger.error(f'{package} 安装失败')
        return False

def _install_with_config(missing_packages: list) -> bool:
    """尝试使用配置文件中的源批量安装缺失包。"""
    try:
        from handle.install import install_requirements
        requirements_str = ' '.join(missing_packages)
        return install_requirements(requirements_str)
    except Exception as e:
        logger.warning(f'使用配置安装失败，回退到默认 pip 安装: {e}')
        return False

def check_packages():
    """检查 requirements 中列出的所有依赖，并自动安装缺失项。"""
    req_list = _parse_requirements(requirements)
    if not req_list:
        logger.info('没有需要检查的依赖')
        return

    missing_packages = _find_missing_packages(req_list)
    if not missing_packages:
        logger.info('所有环境都已安装')
        return

    logger.info(f'检测到缺失依赖: {missing_packages}')

    # 优先使用配置文件中的源批量安装
    if _install_with_config(missing_packages):
        still_missing = _find_missing_packages(missing_packages)
        if not still_missing:
            logger.info('所有环境都已安装')
            return
        logger.warning(f'批量安装后仍有缺失: {still_missing}')

    # 回退到逐个 pip 安装
    for package in missing_packages:
        _install_with_pip(package)

    # 最终检查
    still_missing = _find_missing_packages(missing_packages)
    if still_missing:
        logger.error(f'以下依赖安装失败: {still_missing}')
        raise RuntimeError(f'依赖安装失败: {still_missing}')
    logger.info('所有环境都已安装')

def install_missing_package(package_name: str) -> bool:
    """运行时捕获 No module named 后，安装单个缺失包。

    Args:
        package_name: 缺失的包名（例如 'getmac'）。

    Returns:
        bool: 安装是否成功。
    """
    if not package_name:
        return False
    package_name = package_name.strip()
    logger.info(f'运行时检测到缺失模块 {package_name}，尝试安装...')

    # 先尝试在 requirements 中查找完整依赖项（带版本号）
    req_list = _parse_requirements(requirements)
    target_req = package_name
    for req in req_list:
        if _normalize_package_name(_get_package_name(req)) == _normalize_package_name(package_name):
            target_req = req
            break

    # 优先使用配置安装
    if _install_with_config([target_req]):
        return not _find_missing_packages([target_req])

    return _install_with_pip(target_req)

def install_missing_modules(missing_modules: list) -> bool:
    """运行时批量安装缺失模块。

    Args:
        missing_modules: 缺失模块名称列表。

    Returns:
        bool: 是否全部安装成功。
    """
    if not missing_modules:
        return True

    modules = [str(m).strip() for m in missing_modules if str(m).strip()]
    if not modules:
        return True

    logger.info(f'运行时检测到缺失模块: {modules}，尝试安装...')

    # 先在 requirements 中匹配完整依赖项
    req_list = _parse_requirements(requirements)
    normalized_reqs = {_normalize_package_name(_get_package_name(req)): req for req in req_list}

    target_reqs = []
    for module in modules:
        key = _normalize_package_name(module)
        target_reqs.append(normalized_reqs.get(key, module))

    # 优先批量安装
    if _install_with_config(target_reqs):
        still_missing = _find_missing_packages(target_reqs)
        return not still_missing

    # 回退逐个安装
    success = True
    for req in target_reqs:
        if not _install_with_pip(req):
            success = False
    return success and not _find_missing_packages(target_reqs)