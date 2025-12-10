import os
import logging
import pyautogui

logger = logging.getLogger('屏幕截图')

def save_screenshot(save_dir: str = None) -> dict:
    try:
        logger.info("开始进行屏幕截图...")
        if save_dir is None:
            # 获取当前运行目录
            current_dir = os.getcwd()
            save_dir = os.path.join(current_dir, 'tmp')
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
        return {"success": True, "result": success_msg}
    except Exception as e:
        error_msg = f"屏幕截图失败: {e}"
        logger.error(error_msg)
        return {"success": False, "result": error_msg}