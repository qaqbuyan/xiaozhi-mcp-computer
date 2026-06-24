import platform

def get_paste_keys():
    """根据操作系统返回粘贴快捷键

    Returns:
        list: 粘贴快捷键列表，Windows/Linux 返回 ['ctrl', 'v']，macOS 返回 ['command', 'v']
    """
    if platform.system() in ["Windows", "Linux"]:
        return ['ctrl', 'v']
    elif platform.system() == "Darwin":  # macOS
        return ['command', 'v']
    return ['ctrl', 'v']