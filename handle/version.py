import logging
import ssl
import requests
from requests.exceptions import SSLError, ConnectionError, Timeout
from handle.loader import load_config
from handle.identifier import get_device_headers

logger = logging.getLogger('版本检查')


def _get_friendly_error_message(error: Exception) -> str:
    """将网络请求异常转换为用户友好的提示信息"""
    if isinstance(error, SSLError):
        cert_error = getattr(error, 'reason', None) or str(error)
        # 检查是否为证书过期
        if 'certificate has expired' in str(cert_error):
            return (
                "无法获取版本信息：版本服务器的 SSL 证书已过期。"
                "请检查系统时间是否正确，或联系开发者更新证书。"
            )
        elif 'certificate verify failed' in str(cert_error):
            return (
                "无法获取版本信息：版本服务器的 SSL 证书验证失败。"
                "可能是证书过期或被篡改，请检查网络环境或联系开发者。"
            )
        return (
            "无法获取版本信息：连接版本服务器时出现 SSL 错误。"
            "请检查网络环境或联系开发者。"
        )
    if isinstance(error, ConnectionError):
        return (
            "无法获取版本信息：无法连接到版本服务器。"
            "请检查网络连接是否正常，或稍后重试。"
        )
    if isinstance(error, Timeout):
        return (
            "无法获取版本信息：连接版本服务器超时。"
            "请检查网络连接是否正常，或稍后重试。"
        )
    # 兜底：其他未知请求异常
    return (
        "无法获取版本信息：请求版本服务器时出现异常，请稍后重试。"
        "如果问题持续存在，请联系开发者。"
    )

def get_version(all_version: bool = False) -> dict:
    logger.info("进行获取版本更新...")
    config = load_config()
    current_version = config['version']
    user_agent = config.get('user_agent')
    url = 'https://qaqbuyan.com:88/乔安模块/?mk=sj&id=mcp-client'
    headers = {}
    if user_agent:
        headers['User-Agent'] = user_agent
    headers['x-requested-with'] = 'XMLHttpRequest'
    headers.update(get_device_headers())
    try:
        response = requests.get(url, headers=headers, timeout=5)
        # 检查状态码
        if response.status_code == 200:
            response.raise_for_status()
            json_data = response.json()
            # 检查版本是否一致
            messages = json_data.get('message', [])
            if all_version:
                all_updates = []
                for message in messages:
                    if isinstance(message, dict):
                        version_str = message.get('version')
                        version_number, _, version_type = version_str.partition('-')
                        update_info = {
                            "version": version_str,
                            "type": message.get('type', ''),
                            "content": message.get('content', ''),
                            "requirements": message.get('requirements', ''),
                            "time": message.get('time', ''),
                            "link": message.get('link', ''),
                            "size": message.get('size', ''),
                            "hash": message.get('hash', '')
                        }
                        all_updates.append(update_info)
                # 找出最新版本
                latest_version = None
                if all_updates:
                    latest = max(all_updates, key=lambda x: x["version"].partition('-')[0])
                    latest_version = f"{latest['version'].partition('-')[0]}-{latest['type'].lower()}" if latest['type'] else latest['version']
                result = {
                    "current_version": current_version,
                    "latest_version": latest_version,
                    "all_updates": all_updates
                }
                logger.info(f"返回数据: {result}")
                return result
            else:
                latest_version = None
                latest_version_number = None
                latest_content = ""
                latest_requirements = ""
                latest_link = ""
                latest_type = ""
                latest_size = ""
                latest_hash = ""
                # 找出当前版本的依赖信息
                current_requirements = ""
                for message in messages:
                    if isinstance(message, dict):
                        version_str = message.get('version')
                        version_number, _, version_type = version_str.partition('-')
                        # 如果找到当前版本的依赖信息
                        if f"{version_number}-{version_type}".lower() == current_version.lower():
                            current_requirements = message.get('requirements', '')
                            break
                # 找出最新版本
                for message in messages:
                    if isinstance(message, dict):
                        version_str = message.get('version')
                        version_number, _, version_type = version_str.partition('-')
                        original_type = message.get('type', '')
                        if latest_version_number is None or version_number > latest_version_number:
                            latest_version = f"{version_number}-{original_type.lower()}"
                            latest_version_number = version_number
                            latest_version_type = original_type
                            latest_content = message.get('content', '')
                            latest_requirements = message.get('requirements', '')
                            latest_link = message.get('link', '')
                            latest_type = original_type
                            latest_size = message.get('size', '')
                            latest_hash = message.get('hash', '')
                    else:
                        error_msg = f"消息项不是字典类型: {message}"
                        logger.error(error_msg)
                        return {
                            "error": error_msg
                        }
                if latest_version and (latest_version != current_version):
                    logger.info(f"当前版本: {current_version}")
                    msg = f"发现新版本: {latest_version}"
                    logger.info(msg)
                    result = {
                        "current_version": current_version,
                        "latest_version": latest_version,
                        "update_log": latest_content,
                        "current_requirements": current_requirements,
                        "latest_requirements": latest_requirements,
                        "type": latest_type,
                        "link": latest_link,
                        "hash": latest_hash,
                        "size": latest_size
                    }
                    logger.info(f"返回数据: {result}")
                    return result
                else:
                    msg = f"当前版本已是最新版本: {current_version}"
                    logger.info(msg)
                    return {
                        "current_version": current_version,
                        "message": msg
                    }
        else:
            error_msg = f"请求返回非 200 状态码: {response.status_code}"
            logger.error(error_msg)
            return {
                "error": error_msg
            }
    except requests.RequestException as e:
        error_msg = f"请求出错: {e}"
        logger.error(error_msg)
        # 返回用户友好的提示信息，而非原始异常堆栈
        friendly_msg = _get_friendly_error_message(e)
        return {
            "error": friendly_msg,
            "error_detail": f"请求出错: {e}"  # 仅在内部日志记录原始错误
        }