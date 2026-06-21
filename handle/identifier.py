import hashlib
import uuid

def get_or_create_user_id() -> str:
    """获取设备唯一标识符（基于 MAC 地址的 SHA256 哈希）"""
    mac = uuid.getnode()
    return hashlib.sha256(str(mac).encode()).hexdigest()

def get_device_headers() -> dict:
    """获取携带设备标识的请求头"""
    return {"X-Device-ID": get_or_create_user_id()}