import logging
from utils.scan.menu import scan_menu
from mcp.server.fastmcp import FastMCP
from utils.scan.desktop import scan_desktop

logger = logging.getLogger('扫描统计')

def scan_statistics(mcp: FastMCP):
    @mcp.tool()
    def scan_statistics(file_or_program: str) -> dict:
        """用于扫描桌面以及菜单的程序跟目录，当需要查询桌面或菜单文件或者程序时，立刻使用该工具。
        一律使用该工具扫描，找不到才使用 'scan_folder_or_file' 工具。
        比如我说扫描桌面某一个文件或文件夹等，就会使用这个工具
        比如我说扫描菜单某一个文件或文件夹等，就会使用这个工具
        Args:
            file_or_program (str): 要扫描的文件或程序名称
        Returns:
            找到了就询问是否打开
            后面的目录信息不要告诉我,或者说出来
            这是需要进行打开程序或者拼接的目录，需要进行拼接
            比如：
            在开始菜单找到目标: hmcl.lnk,目录: C:/Users/Administrator/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/
            拼接后:
            C:/Users/Administrator/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/hmcl.lnk
        """
        try:
            logger.info(f"开始扫描: {file_or_program} ...")
            # 先扫描桌面
            desktop_result = scan_desktop()
            # 安全地格式化输出
            desktop_path = desktop_result.split('桌面路径: ')[1].split('\n')[0] if '桌面路径: ' in desktop_result else '无'
            all_programs = desktop_result.split('桌面上的程序:')[1].split('\n')[0] if '桌面上的程序:' in desktop_result else '无'
            desktop_dirs = desktop_result.split('桌面上的目录:')[1].split('\n')[0] if '桌面上的目录:' in desktop_result else '无'
            
            # 过滤出真正的程序文件
            programs_list = [p for p in all_programs.split(',') 
                        if not p.lower().endswith('.txt.lnk') or 
                        p.lower().endswith(('.exe.lnk', '.EXE.lnk'))]
            desktop_programs = ','.join(programs_list)
            
            logger.info(f"扫描桌面结果:\n路径: {desktop_path}\n程序: {desktop_programs}\n目录: {desktop_dirs}")
            # 直接检查目标是否在桌面程序或目录列表中
            if (file_or_program.lower() in desktop_programs.lower() or 
                file_or_program.lower() in desktop_dirs.lower()):
                logger.info(f"在桌面找到目标: {file_or_program}")
                return {"success": True, "result": f"在桌面找到目标: {file_or_program}，目录: {desktop_path}"}
            # 如果桌面没找到，再扫描菜单
            menu_result = scan_menu()
            # 解析菜单扫描结果
            menu_path = menu_result.split('路径: ')[1].split('\n')[0] if '路径: ' in menu_result else '无'
            menu_programs = menu_result.split('程序:')[1].split('\n')[0] if '程序:' in menu_result else '无'
            menu_dirs = menu_result.split('目录:')[1].split('\n')[0] if '目录:' in menu_result else '无'  # 新增这行
            logger.info(f"扫描菜单结果:\n路径: {menu_path}\n程序:{menu_programs}")
            # 检查是否在菜单中找到目标
            target_lower = file_or_program.lower()
            menu_programs_lower = menu_programs.lower()
            # 检查目标是否在程序或目录列表中（带或不带.lnk后缀）
            if (target_lower in menu_programs_lower or 
                f"{target_lower}.lnk" in menu_programs_lower or
                f"{target_lower}.exe" in menu_programs_lower or
                target_lower in menu_dirs.lower()):
                found_item = next((p for p in menu_programs.split(',') 
                if p.lower() == target_lower or 
                p.lower() == f"{target_lower}.lnk" or
                p.lower() == f"{target_lower}.exe"), None) or target_lower
                logger.info(f"在开始菜单找到目标: {found_item}")
                return {"success": True, "result": f"在开始菜单找到目标: {found_item}，目录: {menu_path}"}
            # 如果都没找到
            error_msg = f"未找到目标: {file_or_program}"
            logger.error(error_msg)
            return {"success": False, "result": error_msg}
        except Exception as e:
            error_msg = f"扫描过程中出错: {e}"
            logger.error(error_msg)
            return {"success": False, "result": error_msg}