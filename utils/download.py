import logging
from mcp.server.fastmcp import FastMCP
from utils.file.download import download_file

logger = logging.getLogger('文件下载')

def download_url_file(mcp: FastMCP):
    @mcp.tool()
    def download_url_file(url: str, save_path: str = None, request_headers: dict = None) -> str:
        """用于下载指定 URL 的文件到指定文件夹。
        当需要下载文件时，立刻使用该工具。
        若 URL 无效或下载过程中出现错误，将输出错误信息。
        默认下载目录为运行文件夹下的 download 文件夹，若该文件夹不存在则会创建。
        若指定了下载目录，则会将文件下载到该目录下。
        Args:
            url (str): 要下载的文件的 URL 地址。（必填）
            save_path (str): 下载文件的目标文件夹路径。默认为 None，此时会使用默认下载目录。
            request_headers (dict): HTTP 请求头，用于自定义请求信息。默认为 None。
        Returns:
            str: 包含下载结果的消息，成功时返回成功信息，失败时返回错误信息。
        """
        logger.info("进行文件下载...")
        msg = download_file(url, save_path, request_headers)
        return msg