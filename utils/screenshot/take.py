import logging
from mcp.server.fastmcp import FastMCP
from utils.screenshot.save import save_screenshot

logger = logging.getLogger('屏幕截图')

def take_screenshot(mcp: FastMCP):
    @mcp.tool()
    def take_screenshot(save_dir: str = None) -> dict:
        """进行屏幕截图并保存到指定路径。
        当需要进行屏幕截图时，立刻使用该工具。
        Args:
            save_dir (str): 截图保存的目录，若未提供，则保存到当前运行目录下的 'tem' 文件夹。
        """
        logger.info("开始执行操作...")
        msg = save_screenshot(save_dir)
        logger.info("执行完成")
        return msg