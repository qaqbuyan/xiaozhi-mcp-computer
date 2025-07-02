import os
import logging
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('扫描文件夹')

def scan_folder_or_file(mcp: FastMCP):
    @mcp.tool()
    def scan_folder_or_file(path: str, file_ext: str = '') -> dict:
        """扫描指定路径下的所有文件夹或特定类型文件，当需要查询桌面或菜单文件或者程序时，立刻使用 'scan_statistics' 工具
        当需要查询文件夹或文件时，立刻使用该工具。
        Args:
            path (str): 要扫描的目录路径 (必填，必须是绝对路径，如：'C:/Users/Admin/Documents')
            file_ext (str): 文件扩展名(如'.txt','.py'),空字符串表示扫描文件夹，不填则默认扫描文件夹
                注意: 不支持通配符，如'*.txt'将被视为无效的扩展名
        Returns:
            dict: 包含扫描结果的字典，格式为:
                {
                    "success": bool,  # 是否成功
                    "result": str     # 结果描述信息
                }
        """
        try:
            logger.info("开始扫描...")
            if not os.path.exists(path):
                msg = f"路径不存在: {path}"
                logger.error(msg)
                return {"success": False,"result": msg}
            if not os.path.isdir(path):
                msg = f"路径不是目录: {path}"
                logger.error(msg)
                return {"success": False,"result": msg}
            if file_ext:  # 搜索特定类型文件
                files = [
                    name for name in os.listdir(path)
                    if os.path.isfile(os.path.join(path, name)) and name.endswith(file_ext)
                ]
                if files:
                    result_str = f"找到{len(files)}个{file_ext}文件: {', '.join(files)}"
                else:
                    result_str = f"没有找到{file_ext}文件"
            else:  # 默认搜索文件夹
                folders = [
                    name for name in os.listdir(path)
                    if os.path.isdir(os.path.join(path, name))
                ]
                if folders:
                    result_str = f"文件夹有{', '.join(folders)}"
                else:
                    result_str = "没有找到子文件夹"
            msg = f"扫描完成: {result_str}"
            logger.info(msg)
            return {"success": True,"result": msg}
            logger.info(f"扫描完成: {result_str}")
        except Exception as e:
            msg = f"扫描失败: {path} - {str(e)}"
            logger.error(msg)
            return {"success": False,"result": msg}