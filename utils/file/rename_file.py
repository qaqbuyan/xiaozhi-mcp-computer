import os
import logging
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('重命名文件')

def rename_file(mcp: FastMCP):
    @mcp.tool()
    def rename_file(old_path: str, new_name: str) -> dict:
        """修改文件或文件夹的名称
        Args:
            old_path (str): 原文件/文件夹路径
            new_name (str): 新的名称(不含路径)
            
        Returns:
            dict: 包含操作结果的字典，格式为:
                {
                    "success": bool,  # 是否成功
                    "result": str     # 结果消息
                }
        """
        logger.info(f"重命名文件: {old_path} -> {new_name}")
        try:
            # 检查路径是否存在
            if not os.path.exists(old_path):
                msg = f"路径不存在: {old_path}"
                logger.error(msg)
                return {"success": False,"result": msg}
            # 获取父目录和新路径
            parent_dir = os.path.dirname(old_path)
            new_path = os.path.join(parent_dir, new_name)
            # 检查新路径是否已存在
            if os.path.exists(new_path):
                msg = f"目标名称已存在: {new_path}"
                logger.error(msg)
                return {"success": False,"result": msg}
            os.rename(old_path, new_path)
            msg = f"重命名成功: {old_path} -> {new_path}"
            logger.info(msg)
            return {"success": True,"result": msg}
        except Exception as e:
            msg = f"重命名失败: {old_path} - {str(e)}"
            logger.error(msg)
            return {"success": False,"result": msg}