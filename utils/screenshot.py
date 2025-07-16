import os
import logging
import pyautogui
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('屏幕截图')

def take_screenshot(mcp: FastMCP):
    @mcp.tool()
    def take_screenshot(save_dir: str = None) -> str:
        """进行屏幕截图并保存到指定路径。
        当需要进行屏幕截图时，立刻使用该工具。
        比如说，我需要截图，你就会使用这个工具，直接返回截图的路径给用户。
        参数:
            save_dir (str): 截图保存的目录，若未提供，则保存到当前运行目录下的 'tem' 文件夹。
        """
        try:
            logger.info("开始进行屏幕截图...")
            if save_dir is None:
                # 获取当前运行目录
                current_dir = os.getcwd()
                save_dir = os.path.join(current_dir, 'tem')
            # 检查目录是否存在，不存在则创建
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            file_path = os.path.join(save_dir, 'screenshot.png')
            # 确保路径使用反斜杠
            file_path = os.path.normpath(file_path)
            # 执行截图
            screenshot = pyautogui.screenshot()
            # 保存截图
            screenshot.save(file_path)
            success_msg = f"屏幕截图已保存到 {file_path}"
            logger.info(success_msg)
            return success_msg
        except Exception as e:
            error_msg = f"屏幕截图失败: {e}"
            logger.error(error_msg)
            return error_msg