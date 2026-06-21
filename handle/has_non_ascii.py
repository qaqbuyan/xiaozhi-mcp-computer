def has_non_ascii(text: str) -> bool:
    """检查字符串是否包含非 ASCII 字符（中文等多字节字符）

    Args:
        text: 要检查的字符串

    Returns:
        bool: 包含非 ASCII 字符返回 True，否则返回 False
    """
    return any(ord(c) > 127 for c in text)