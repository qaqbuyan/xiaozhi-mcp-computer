import logging
import requests
from handle.loader import load_config

logger = logging.getLogger('版本检查')

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
        return {
            "error": error_msg
        }