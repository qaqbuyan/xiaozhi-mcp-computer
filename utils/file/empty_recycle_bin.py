import ctypes
import logging
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('清空回收站')

def empty_recycle_bin(mcp: FastMCP):
    @mcp.tool()
    def empty_recycle_bin() -> dict:
        """清空系统回收站。
        当需要清空回收站时，立刻使用该工具。
        Returns:
            dict: 包含操作结果的字典，格式为:
                {
                    "success": bool,  # 是否成功
                    "result": str     # 结果消息
                }
        """
        logger.info('开始清空回收站')
        try:
            SHEmptyRecycleBin = ctypes.windll.shell32.SHEmptyRecycleBinW
            result = SHEmptyRecycleBin(None, None, 1)
            if result == 0:
                msg = '回收站清空成功'
                logger.info(msg)
                return {"success": True, "result": msg}
            else:
                msg = '回收站清空失败'
                logger.error(msg)
                return {"success": False, "result": msg}
        except Exception as e:
            msg = f'清空回收站时出错: {str(e)}'
            logger.error(msg)
            return {"success": False, "result": msg}