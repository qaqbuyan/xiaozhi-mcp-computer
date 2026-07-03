import re


def parse_requirements(requirements_str: str) -> set:
    """将依赖字符串解析为依赖项集合，支持空格或换行分隔，并忽略空行/注释。"""
    if not requirements_str:
        return set()
    return {
        req.strip()
        for req in re.split(r'[\s,]+', requirements_str)
        if req.strip() and not req.strip().startswith('#')
    }


def get_package_name(req: str) -> str:
    """从依赖项中提取包名（去掉版本限定符）。"""
    if not req:
        return ''
    return re.split(r'>=|==|<=|<|>|~=', req)[0].strip().lower()


def get_new_requirements(current_requirements: str, latest_requirements: str) -> str:
    """比较当前版本和最新版本的依赖差异，返回需要安装的新依赖。

    Args:
        current_requirements: 当前版本的依赖字符串。
        latest_requirements: 最新版本的依赖字符串。

    Returns:
        str: 需要安装的新依赖字符串（空格分隔），如果没有新增依赖则返回空字符串。
    """
    if not current_requirements or not latest_requirements:
        return latest_requirements or ""

    current_set = parse_requirements(current_requirements)
    latest_set = parse_requirements(latest_requirements)

    # 找出新增的依赖（按完整依赖项比较，包含版本号差异）
    new_requirements = latest_set - current_set
    if new_requirements:
        return ' '.join(sorted(new_requirements))
    return ""
