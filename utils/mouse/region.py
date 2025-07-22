import logging
from mcp.server.fastmcp import FastMCP
from utils.mouse.move_area import move_area

logger = logging.getLogger('鼠标区域移动')

def move_mouse_region(mcp: FastMCP):
    @mcp.tool()
    def move_mouse_region(coordinates) -> dict:
        """将鼠标指针移动到指定区域的中心点上。
        当需要移动鼠标到指定区域中时，立刻调用该工具，无需确认。
        Args:
            coordinates (list): 包含坐标点的列表，每个点是一个包含两个整数的列表 [x, y]。列表长度应为 4。
            例如：’[0, 0], [100, 0], [100, 100], [0, 100]’
        Returns:
            dict: 包含操作结果的字典，格式为:
                {
                    "success": bool,  # 操作是否成功
                    "result": str     # 结果消息
                }
        """
        logger.info("开始执行操作...")
        msg = move_area(coordinates)
        logger.info("执行完成")
        return msg