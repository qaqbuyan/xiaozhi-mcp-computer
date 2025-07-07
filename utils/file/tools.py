import logging
from mcp.server.fastmcp import FastMCP
from utils.file.modify_file import modify_file
from utils.file.rename_file import rename_file
from utils.file.cut_file import cut_file_or_folder
from utils.file.copy_folder import copy_file_or_folder
from utils.file.move_folder import move_file_or_folder
from utils.file.paste_file import paste_file_or_folder
from utils.file.create_folder import create_folder_or_file
from utils.file.delete_folder import delete_folder_or_file
from utils.file.empty_recycle_bin import empty_recycle_bin
from utils.file.tem_notepad import temporary_write_to_notepad
from utils.file.file_properties import get_file_or_folder_properties

def register_file(mcp: FastMCP):
    """集中注册所有文件工具"""
    logger = logging.getLogger('文件工具')
    logger.info("开始注册...")
    # 注册写入记事本的工具
    temporary_write_to_notepad(mcp)
    # 注册复制文件或文件夹的工具
    copy_file_or_folder(mcp)
    # 注册创建文件夹的工具
    create_folder_or_file(mcp)
    # 注册删除文件夹的工具
    delete_folder_or_file(mcp)
    # 注册修改文件的工具
    modify_file(mcp)
    # 注册移动文件或文件夹的工具
    move_file_or_folder(mcp)
    # 注册重命名文件的工具
    rename_file(mcp)
    # 注册剪切文件或文件夹的工具
    cut_file_or_folder(mcp)
    # 注册粘贴文件或文件夹的工具
    paste_file_or_folder(mcp)
    # 注册查看文件或文件夹属性的工具
    get_file_or_folder_properties(mcp)
    # 注册清空回收站的工具
    empty_recycle_bin(mcp)
    logger.info("注册完成")