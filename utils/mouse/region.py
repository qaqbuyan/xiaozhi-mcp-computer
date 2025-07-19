import logging
import pyautogui
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('鼠标区域移动')

def move_mouse_region(mcp: FastMCP):
    @mcp.tool()
    def move_mouse_region(coordinates) -> dict:
        """将鼠标指针移动到指定区域的中心点上。
        当需要移动鼠标到指定区域中时，立刻调用该工具，无需确认。
        参数:
            coordinates (list): 包含坐标点的列表，每个点是一个包含两个整数的列表 [x, y]。列表长度应为 4。
        返回:
            dict: 包含操作结果的字典，格式为:
                {
                    "success": bool,  # 操作是否成功
                    "result": str     # 结果消息
                }
        """
        logger.info(f'开始移动鼠标到区域中心点...')
        try:
            # 验证输入格式
            if not isinstance(coordinates, list) or len(coordinates) != 4:
                error_msg = "错误：坐标列表长度必须为 4。"
                logger.error(error_msg)
                return {"success": False, "result": error_msg}

            for point in coordinates:
                if not isinstance(point, list) or len(point) != 2:
                    error_msg = "错误：每个坐标点必须是包含两个整数的列表 [x, y]。"
                    logger.error(error_msg)
                    return {"success": False, "result": error_msg}
                if not all(isinstance(coord, (int, float)) for coord in point):
                    error_msg = "错误：坐标必须是整数或浮点数。"
                    logger.error(error_msg)
                    return {"success": False, "result": error_msg}

            # 获取所有点的 x 坐标
            x_coords = [point[0] for point in coordinates]
            # 计算 x 坐标的最小值和最大值
            min_x = min(x_coords)
            max_x = max(x_coords)
            # 计算 x 坐标的中心点
            center_x = (min_x + max_x) // 2
            # 假设区域内 y 坐标的中心点也需要，这里获取所有 y 坐标
            y_coords = [point[1] for point in coordinates]
            min_y = min(y_coords)
            max_y = max(y_coords)
            center_y = (min_y + max_y) // 2
            pyautogui.moveTo(center_x, center_y)
            success_msg = f"成功移动鼠标到区域中心点: X = {center_x}, Y = {center_y}"
            logger.info(success_msg)
            return {"success": True, "result": success_msg}
        except Exception as e:
            error_msg = f"移动鼠标时出错: {e}"
            logger.error(error_msg)
            return {"success": False, "result": error_msg}