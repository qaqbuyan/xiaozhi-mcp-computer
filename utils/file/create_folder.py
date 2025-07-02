import os
import logging
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('创建写入')

def create_folder_or_file(mcp: FastMCP):
    @mcp.tool()
    def create_folder_or_file(path: str, content: str = '') -> dict:
        """创建指定路径的文件或文件夹，并写入可选的文本内容。
        当需要创建文件写入内容或文件夹时，立刻使用该工具。
        Args:
            path (str): 要创建的路径，可以是文件或文件夹路径，如果是文件，需要指定文件名
            content (str, optional): 如果是文件，可选的文本内容
        Returns:
            dict: 包含操作结果的字典，格式为:
                {
                    "success": bool,  # 是否成功
                    "result": str,   # 结果消息包括实际创建的路径
                }
        """
        logger.info(f"创建文件或文件夹: {path}")
        try:
            # 检查路径是否已存在
            if os.path.exists(path):
                msg = f"路径已存在: {path}"
                logger.info(msg)
                return {"success": True,"result": msg}
            # 判断是创建文件还是文件夹
            if path.endswith(os.sep) or '.' not in os.path.basename(path):
                # 创建目录（包括所有必要的父目录）
                os.makedirs(path, exist_ok=True)
                msg = f"文件夹创建成功: {path}"
                logger.info(msg)
                return {"success": True,"result": msg}
            else:
                # 创建文件
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    if content:
                        f.write(content)
                msg = f"文件创建成功: {path}"
                logger.info(msg)
                return {"success": True,"result": msg}
        except Exception as e:
            msg = f"操作失败: {path} - {str(e)}"
            logger.error(msg)
            return {"success": False,"result": msg}