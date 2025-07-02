import os
import logging
import requests
from mcp.server.fastmcp import FastMCP
from urllib.parse import urlparse, quote
from handle.loader import load_config

logger = logging.getLogger('文件下载')

def download_file(mcp: FastMCP):
    @mcp.tool()
    def download_file(url: str, folder: str = None) -> str:
        """用于下载指定 URL 的文件到指定文件夹。
        当需要下载文件时，立刻使用该工具。
        若 URL 无效或下载过程中出现错误，将输出错误信息。
        默认下载目录为运行文件夹下的 download 文件夹，若该文件夹不存在则会创建。
        若指定了下载目录，则会将文件下载到该目录下。
        Args:
            url (str): 要下载的文件的 URL 地址。（必填）
            folder (str, optional): 下载文件的目标文件夹路径。默认为 None。
        Returns:
            str: 包含下载结果的消息。
        """
        try:
            logger.info(f"开始下载文件: {url}")
            # 加载配置并获取 user_agent
            config = load_config()
            user_agent = config.get('http_headers', {}).get('user_agent')
            headers = {}
            if user_agent:
                headers['User-Agent'] = user_agent

            # 对 URL 中的中文部分进行编码
            parsed = urlparse(url)
            path = quote(parsed.path)
            new_url = parsed._replace(path=path).geturl()

            # 检查 URL 是否有效
            if not new_url:
                msg = "错误：URL 地址不能为空"
                logger.error(msg)
                return msg
            try:
                response = requests.head(new_url, headers=headers)  # 添加 headers
                response.raise_for_status()
            except requests.RequestException as e:
                msg = f"错误：URL 无效或无法访问 - {e}"
                logger.error(msg)
                return msg
            # 确定下载目录
            if folder is None:
                current_dir = os.getcwd()
                folder = os.path.join(current_dir, 'download')
            # 创建下载目录（如果不存在）
            if not os.path.exists(folder):
                os.makedirs(folder)
            # 提取文件名
            from urllib.parse import unquote
            file_name = os.path.basename(unquote(new_url))
            file_path = os.path.join(folder, file_name)
            # 下载文件
            logger.info(f"开始下载文件: {url} 到 {file_path}")
            try:
                response = requests.get(new_url, stream=True, headers=headers)  # 添加 headers
                response.raise_for_status()
                with open(file_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
                success_msg = f"文件下载成功，下载目录地址: {folder}，文件名称: {file_name}"
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