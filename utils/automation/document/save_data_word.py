import os
import logging
from docx import Document
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('保存Word')

def save_data_to_word(mcp: FastMCP):
    @mcp.tool()
    def save_content_to_word(content: str, save_dir: str, file_name: str) -> str:
        """将内容保存到指定目录下的 Word 文件
        如果保存成功询问用户是否打开文件，如果需要请立刻使用 ’open_file’ 工具来打开
        Args:
            content (str): 要写入的内容
            save_dir (str): 保存的目录，例如：C:/Users/Administrator/Desktop/
            file_name (str): 保存的文件名
        Returns:
            str: 保存成功的消息
        """
        logger.info(f'开始处理数据，文件名为：{file_name}，存储目录为：{save_dir} ...')
        try:
            # 检查目录是否存在，不存在则创建
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            # 创建 Word 文档对象
            doc = Document()
            doc.add_paragraph(content)
            # 若文件名没有 .docx 后缀，则自动添加
            if not file_name.lower().endswith('.docx'):
                file_name += '.docx'
            # 拼接完整的文件路径
            file_path = os.path.join(save_dir, file_name)
            # 保存文档
            doc.save(file_path)
            msg = f'文件已成功保存到 {file_path}'
            logger.info(msg)
            return msg
        except Exception as e:
            error_msg = f'保存文件 {file_name} 失败，错误信息: {str(e)}'
            logger.error(error_msg)
            return error_msg