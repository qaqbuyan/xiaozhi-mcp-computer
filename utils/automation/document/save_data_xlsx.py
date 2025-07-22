import os
import logging
import xlsxwriter
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('保存xlsx')

def save_data_to_xlsx(mcp: FastMCP):
    @mcp.tool()
    def save_data_to_xlsx(data: list, file_name: str, save_dir: str) -> str: 
        """将数据存储为 xlsx 文件
        如果保存成功询问用户是否打开文件，如果需要请立刻使用 ’open_file’ 工具来打开
        Args:
            data (list): 数据数组，格式为 [ {"title": "标题", "list": ["行数据1", "行数据2", ...]} ]
            file_name (str): 文件名，无需包含 .xlsx 后缀
            save_dir (str): 存储目录路径
        Returns:
            str: 存储文件的完整路径或错误信息
        """
        try:
            logger.info(f'开始处理数据，文件名为：{file_name}，存储目录为：{save_dir} ...')
            # 检查存储目录是否存在，不存在则创建
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            # 确保文件名包含 .xlsx 后缀
            if not file_name.lower().endswith('.xlsx'):
                file_name += '.xlsx'
            # 拼接完整文件路径
            file_path = os.path.join(save_dir, file_name)
            # 创建 xlsx 文件
            workbook = xlsxwriter.Workbook(file_path)
            # 创建居中对齐的格式
            center_format = workbook.add_format({'align': 'center'})
            worksheet = workbook.add_worksheet()
            # 遍历数据并写入文件
            for index, item in enumerate(data):
                # 写入标题，按空格分割
                title = item.get('title', '')
                title_columns = title.strip().split()
                for col_index, col_data in enumerate(title_columns):
                    worksheet.write(index, col_index, col_data, center_format)
                index += 1
                # 写入列表数据
                for row_data in item.get('list', []):
                    # 按空格分割行数据
                    columns = row_data.strip().split()
                    for col_index, col_data in enumerate(columns):
                        worksheet.write(index, col_index, col_data, center_format)
                    index += 1
            # 关闭工作簿
            workbook.close()
            msg = f'数据处理完成，文件路径为：{file_path}'
            logger.info(msg)
            return msg
        except Exception as e:
            error_msg = f'处理数据时出现错误：{str(e)}'
            logger.error(error_msg)
            return error_msg