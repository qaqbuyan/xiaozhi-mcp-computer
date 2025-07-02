import os
import logging
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('查看文件或文件夹属性')

def get_file_or_folder_properties(mcp: FastMCP):
    @mcp.tool()
    def get_file_or_folder_properties(path: str) -> dict:
        """查看指定文件或文件夹的属性。
        当需要查看文件或文件夹属性时，立刻使用该工具。
        Args:
            path (str): 要查看属性的文件或文件夹的地址。（必填）
        Returns:
            dict: 包含操作结果和文件（文件夹）属性的字典，格式为:
                {
                    "success": bool,  # 是否成功
                    "result": str,    # 结果消息
                    "properties": dict  # 文件或文件夹的属性
                }
        """
        logger.info(f"开始查看属性: {path}")
        try:
            if not os.path.exists(path):
                msg = f"错误：路径 {path} 不存在"
                logger.error(msg)
                return {"success": False, "result": msg, "properties": {}}

            properties = {}
            if os.path.isfile(path):
                stat = os.stat(path)
                properties = {
                    "is_file": True,
                    "size": stat.st_size,
                    "creation_time": stat.st_ctime,
                    "modification_time": stat.st_mtime,
                    "access_time": stat.st_atime
                }
            elif os.path.isdir(path):
                stat = os.stat(path)
                properties = {
                    "is_file": False,
                    "creation_time": stat.st_ctime,
                    "modification_time": stat.st_mtime,
                    "access_time": stat.st_atime
                }

            msg = f"属性查看成功: {path}"
            logger.info(msg)
            return {"success": True, "result": msg, "properties": properties}
        except Exception as e:
            msg = f"查看属性时出错: {str(e)}"
            logger.error(msg)
            return {"success": False, "result": msg, "properties": {}}