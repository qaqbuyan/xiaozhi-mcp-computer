import os
import logging
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('修改文件')

def modify_file(mcp: FastMCP):
    @mcp.tool()
    def modify_file_content(file_path: str, new_content: str, overwrite: bool = True) -> dict:
        """修改指定文件的内容
        Args:
            file_path (str): 要修改的文件路径，必须
            new_content (str): 要写入的新内容，必须
            overwrite (bool): True表示覆盖文件，False表示追加内容
        Returns:
            dict: 包含操作结果的字典，格式为:
                {
                    "success": bool,  # 是否成功
                    "result": str     # 结果消息
                }
        """
        logger.info(f"修改文件: {file_path}")
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                msg = f"文件不存在: {file_path}"
                logger.error(msg)
                return {"success": False,"result": msg}
            # 检查是否是文件
            if not os.path.isfile(file_path):
                msg = f"路径不是文件: {file_path}"
                logger.error(msg)
                return {"success": False,"result": msg}
            # 根据overwrite参数决定写入模式
            mode = 'w' if overwrite else 'a'
            with open(file_path, mode, encoding='utf-8') as f:
                f.write(new_content)
            action = "覆盖" if overwrite else "追加"
            msg = f"文件内容{action}成功: {file_path}"
            logger.info(msg)
            return {"success": True,"result": msg}
        except Exception as e:
            msg = f"操作失败: {file_path} - {str(e)}"
            logger.error(msg)
            return {"success": False,"result": msg}