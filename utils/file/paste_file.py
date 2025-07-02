import os
import shutil
import logging
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('粘贴文件或文件夹')

def paste_file_or_folder(mcp: FastMCP):
    @mcp.tool()
    def paste_file_or_folder(source: str, destination: str) -> dict:
        """粘贴指定的文件或文件夹到目标地址。
        当需要粘贴文件或文件夹时，立刻使用该工具。
        Args:
            source (str): 要粘贴的文件或文件夹的源地址。（必填）
            destination (str): 粘贴文件或文件夹的目标地址。（必填）
        Returns:
            dict: 包含操作结果的字典，格式为:
                {
                    "success": bool,  # 是否成功
                    "result": str     # 结果消息
                }
        """
        logger.info(f"开始粘贴: {source} 到 {destination}")
        try:
            if not os.path.exists(source):
                msg = f"错误：源地址 {source} 不存在"
                logger.error(msg)
                return {"success": False, "result": msg}

            if os.path.isfile(source):
                shutil.copy2(source, destination)
                msg = f"文件粘贴成功: {source} 到 {destination}"
            else:
                shutil.copytree(source, destination, dirs_exist_ok=True)
                msg = f"文件夹粘贴成功: {source} 到 {destination}"
            
            logger.info(msg)
            return {"success": True, "result": msg}
        except Exception as e:
            msg = f"粘贴时出错: {str(e)}"
            logger.error(msg)
            return {"success": False, "result": msg}