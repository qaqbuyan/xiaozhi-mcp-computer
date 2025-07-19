import os
import logging
import requests
from handle.loader import load_config
from urllib.parse import urlparse, quote

logger = logging.getLogger('文件下载')

def download_file(url: str, save_path: str = None, headers: dict = None) -> str:
    try:
        logger.info(f"下载文件: {url}")
        logger.info(f"下载目录: {save_path}")
        config = load_config()
        user_agent = config.get('user_agent')
        request_headers = {} if headers is None else headers.copy()
        if user_agent:
            request_headers['User-Agent'] = user_agent
        parsed = urlparse(url)
        path = quote(parsed.path)
        new_url = parsed._replace(path=path).geturl()
        if not new_url:
            msg = "错误：URL 地址不能为空"
            logger.error(msg)
            return msg
        try:
            response = requests.head(new_url, headers=request_headers)
            response.raise_for_status()
        except requests.RequestException as e:
            msg = f"错误：URL 无效或无法访问 - {e}"
            logger.error(msg)
            return msg
        if save_path is None:
            current_dir = os.getcwd()
            save_path = os.path.join(current_dir, 'download')
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        from urllib.parse import unquote
        file_name = os.path.basename(unquote(new_url))
        file_path = os.path.join(save_path, file_name)
        logger.info(f"开始下载文件: {url} 到 {file_path}")
        try:
            response = requests.get(new_url, stream=True, headers=request_headers)
            response.raise_for_status()
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            success_msg = f"文件下载成功，下载目录地址: {save_path}，文件名称: {file_name}"
            logger.info(success_msg)
            return success_msg
        except requests.exceptions.ConnectionError as conn_error:
            msg = f"下载文件时发生连接错误: {conn_error}"
            logger.error(msg)
            return msg
    except Exception as e:
        msg = f"下载文件时出错: {e}"
        logger.error(msg)
        return msg