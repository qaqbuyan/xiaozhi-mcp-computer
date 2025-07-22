import logging
from mcp.server.fastmcp import FastMCP
from utils.mouse.move_area import move_area
from utils.screenshot.save import save_screenshot
from utils.image_recognition.identify import identify_image_text_coordinates

logger = logging.getLogger('识别移动')

def log_and_return_error(message: str) -> dict:
    logger.error(message)
    return {"success": False, "result": message}

def identify_move_page_position(mcp: FastMCP):
    @mcp.tool()
    def identify_move_page_position(characters: str) -> dict:
        """将鼠标移动页面(屏幕)上的某个(些)文字的位置
        Use:
            1.用户要求点击(移动)页面(屏幕)上的某个(些)文字时，立刻调用该工具，如果成功了就告诉用户我已经点击(移动)成功了
                如果用户要求点击，请立刻使用 ’mouse_click’ 工具点击，如果用户没有要求点击，必须询问用户需要点击
                需要点击，立刻使用 ’mouse_click’ 工具点击，无需确认，直接调用工具点击即可
            例如：
                用户要求点击页面(屏幕)上的文字比如 '回收站'，立刻调用该工具，因为用户要求点击，如果成功了就
                立刻调用 'mouse_click' 工具执行点击操作
        Args:
            characters (str): 要点击(移动)的文字
        Returns:
            dict: 包含操作结果的字典，格式为:
                {
                    "success": bool,  # 操作是否成功
                    "result": str     # 结果消息
                }
        """
        logger.info(f"移动到文字 {characters} 开始执行操作...")
        screenshot_result = save_screenshot()
        if not screenshot_result.get('success', False):
            return log_and_return_error("截图失败，终止操作: {}".format(screenshot_result.get('result', '')))

        # 获取截图文件路径
        image = screenshot_result.get('result', '').split('屏幕截图已保存到 ')[-1].strip()
        # 调用图像识别函数
        identify_result = identify_image_text_coordinates(image, 15)
        if not identify_result.get('success', False):
            return log_and_return_error("图像识别失败，终止操作: {}".format(identify_result.get('result', '')))

        # 获取识别结果列表
        recognition_results = identify_result.get('result', [])
        # 过滤出匹配 characters 的结果
        matched_results = [item for item in recognition_results if characters in item.get('text', '')]
        if not matched_results:
            return log_and_return_error("未找到匹配文字的坐标")

        # 提取所有匹配结果的 position 坐标
        coordinates_list = [item.get('position', []) for item in matched_results]
        if not coordinates_list:
            return log_and_return_error("未找到匹配文字的坐标")

        # 这里可以根据需求选择处理多个坐标的方式，示例中假设只处理第一个匹配结果
        coordinates = coordinates_list[0]
        return move_area(coordinates)