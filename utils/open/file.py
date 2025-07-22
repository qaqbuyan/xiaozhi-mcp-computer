import os
import logging
import subprocess
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('打开文件')

def open_file(mcp: FastMCP):
    @mcp.tool()
    def open_file(file_path: str) ->str:
        """用于打开指定路径的文件，支持 img、word(docx)、excel、ppt、pdf 等文件格式。
        当需要某一个文件时，立刻使用该工具。
        Notice：
            1.不是所有文件格式都支持，例如 ppt 等格式需要安装 Office 软件才能打开。
            2.如果是程序请使用 ’open_program’ 工具来打开
        Args:
            file_path (str): 文件的完整路径，例如: C:/Users/Administrator/Desktop/1.txt
        Returns:
            str: 打开文件的结果
        """
        try:
            logger.info(f"开始打开文件: {file_path}")
            if not os.path.exists(file_path):
                msg = f"文件不存在: {file_path}"
                logger.error(msg)
                return msg
            # Windows 系统使用 start 命令打开文件
            subprocess.run(['start', '', file_path], shell=True, check=True)
            msg = f"成功打开文件: {file_path}"
            logger.info(msg)
            return msg
        except Exception as e:
            msg = f"打开文件时出错: {str(e)}"
            logger.error(msg)
            return msg