import os
import shutil
import logging
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('移动文件或文件夹')

def move_file_or_folder(mcp: FastMCP):
    @mcp.tool()
    def move_file_or_folder(source: str, destination: str) -> dict:
        """移动指定的文件或文件夹到目标地址。
        当需要移动文件或文件夹时，立刻使用该工具。
        Args:
            source (str): 要移动的文件或文件夹的源地址。（必填）
            destination (str): 移动文件或文件夹的目标地址。（必填）
        Returns:
            dict: 包含操作结果的字典，格式为:
                {
                    "success": bool,  # 是否成功
                    "result": str     # 结果消息
                }
        """
        logger.info(f"开始移动: {source} 到 {destination}")
        try:
            if not os.path.exists(source):
                msg = f"错误：源地址 {source} 不存在"
                logger.error(msg)
                return {"success": False, "result": msg}

            shutil.move(source, destination)
            msg = f"移动成功: {source} 到 {destination}"
            logger.info(msg)
            return {"success": True, "result": msg}
        except Exception as e:
            msg = f"移动时出错: {str(e)}"
            logger.error(msg)
            return {"success": False, "result": msg}