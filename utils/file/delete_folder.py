import os
import shutil
import logging
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('删除文件')

def delete_folder_or_file(mcp: FastMCP):
    @mcp.tool()
    def delete_folder_or_file(path: str, clear_content: bool = False) -> dict:
        """删除指定路径的文件或文件夹，或清空文件内容
        Args:
            path (str): 要操作的路径，可以是文件或文件夹路径
            clear_content (bool): 如果是文件且为True，则只清空内容而不删除文件
        Returns:
            dict: 包含操作结果的字典，格式为:
                {
                    "success": bool,  # 是否成功
                    "result": str     # 结果消息
                }
        """
        logger.info(f"删除文件或文件夹: {path}")
        try:
            if not os.path.exists(path):
                msg = f"路径不存在: {path}"
                logger.info(msg)
                return {"success": False,"result": msg}
            if os.path.isdir(path):
                shutil.rmtree(path)
                msg = f"文件夹删除成功: {path}"
                logger.info(msg)
                return {"success": True,"result": msg}
            else:
                if clear_content:
                    # 清空文件内容
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write('')
                    msg = f"文件内容已清空: {path}"
                    logger.info(msg)
                    return {"success": True,"result": msg}
                else:
                    # 删除文件
                    os.remove(path)
                    msg = f"文件删除成功: {path}"
                    logger.info(msg)
                    return {"success": True,"result": msg}
        except Exception as e:
            msg = f"操作失败: {path} - {str(e)}"
            logger.error(msg)
            return {"success": False,"result": msg}