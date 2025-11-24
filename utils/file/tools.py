import logging
from handle.loader import load_config
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
    
    # 加载配置
    config = load_config()
    file_config = config.get('utils', {}).get('file', {})
    
    # 检查是否有任何工具需要注册
    has_tools_to_register = any(file_config.values())
    
    if not has_tools_to_register:
        logger.info("所有文件工具已禁用，跳过注册")
        return
    
    logger.info("开始注册...")
    
    # 根据配置注册对应的工具
    if file_config.get('notepad', False):
        temporary_write_to_notepad(mcp)
    
    if file_config.get('copy_file_or_folder', False):
        copy_file_or_folder(mcp)
    
    if file_config.get('create_folder_or_file', False):
        create_folder_or_file(mcp)
    
    if file_config.get('delete_folder_or_file', False):
        delete_folder_or_file(mcp)
    
    if file_config.get('modify_file_content', False):
        modify_file(mcp)
    
    if file_config.get('move_file_or_folder', False):
        move_file_or_folder(mcp)
    
    if file_config.get('rename_file_or_folder', False):
        rename_file(mcp)
    
    if file_config.get('cut_file_or_folder', False):
        cut_file_or_folder(mcp)
    
    if file_config.get('paste_file_or_folder', False):
        paste_file_or_folder(mcp)
    
    if file_config.get('get_file_or_folder_properties', False):
        get_file_or_folder_properties(mcp)
    
    if file_config.get('empty_recycle_bin', False):
        empty_recycle_bin(mcp)
    
    logger.info("注册完成")