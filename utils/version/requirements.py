def get_new_requirements(current_requirements: str, latest_requirements: str) -> str:
    """比较当前版本和最新版本的依赖差异，返回需要安装的新依赖
    Args:
        current_requirements: 当前版本的依赖字符串
        latest_requirements: 最新版本的依赖字符串
    Returns:
        str: 需要安装的新依赖字符串，如果没有新增依赖则返回空字符串
    """
    if not current_requirements or not latest_requirements:
        return latest_requirements
    # 将依赖字符串转换为集合
    current_set = set(req.strip() for req in current_requirements.split() if req.strip())
    latest_set = set(req.strip() for req in latest_requirements.split() if req.strip())
    # 找出新增的依赖
    new_requirements = latest_set - current_set
    if new_requirements:
        return ' '.join(sorted(new_requirements))
    else:
        return ""