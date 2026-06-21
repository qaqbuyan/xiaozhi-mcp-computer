import os
import psutil
import logging
from mcp.server.fastmcp import FastMCP
from handle.missing_params import ask_on_missing

logger = logging.getLogger('关闭程序')

# 程序自身进程名前缀（禁止关闭）
_PROTECTED_PROCESS_PREFIX = "小智控制电脑"


def close_application(mcp: FastMCP):
    @mcp.tool()
    @ask_on_missing('process_name')
    def close_application(process_name: str = None) -> dict:
        """关闭指定名称的程序，若程序未响应则尝试强制终止。
        当需要关闭某个程序时，立刻使用该工具。
        注意：如果用户要关闭的是**指定窗口**（而非按程序名终止进程），请使用 close_top_window 工具。
        Args:
            process_name (str): 要关闭的程序名称，例如 'notepad'
        Returns:
            dict: 包含操作结果的字典，格式为:
                {
                    "success": bool,  # 是否成功
                    "result": str   # 结果消息
                }
        """
        logger.info(f"尝试关闭程序: {process_name} ...")
        # 拼接 .exe 扩展名
        full_process_name = f"{process_name}.exe"
        success_count = 0
        failed_count = 0
        total_processes = 0
        current_pid = os.getpid()

        # 检查是否试图关闭程序自身
        if process_name and _PROTECTED_PROCESS_PREFIX in process_name:
            msg = f"禁止关闭程序自身！无法执行关闭操作"
            logger.warning(msg)
            return {"success": False, "result": msg}

        try:
            for proc in psutil.process_iter(['name', 'pid']):
                proc_name = proc.info['name']
                if proc_name is None:
                    continue
                proc_name_lower = proc_name.lower()
                full_name_lower = full_process_name.lower()
                # 跳过程序自身进程
                if proc.info['pid'] == current_pid:
                    continue
                # 跳过程序自身相关的所有进程（基于进程名前缀匹配）
                if proc_name_lower.startswith(_PROTECTED_PROCESS_PREFIX.lower()):
                    continue
                if proc_name_lower == full_name_lower:
                    total_processes += 1
            for proc in psutil.process_iter(['name', 'pid']):
                proc_name = proc.info['name']
                if proc_name is None:
                    continue
                proc_name_lower = proc_name.lower()
                full_name_lower = full_process_name.lower()
                # 跳过程序自身进程
                if proc.info['pid'] == current_pid:
                    continue
                # 跳过程序自身相关的所有进程（基于进程名前缀匹配）
                if proc_name_lower.startswith(_PROTECTED_PROCESS_PREFIX.lower()):
                    continue
                if proc_name_lower == full_name_lower:
                    try:
                        proc.terminate()
                        _, still_alive = psutil.wait_procs([proc], timeout=5)
                        if still_alive:
                            proc.kill()
                            _, still_alive_after_kill = psutil.wait_procs([proc], timeout=5)
                            if still_alive_after_kill:
                                failed_count += 1
                            else:
                                success_count += 1
                        else:
                            success_count += 1
                    except psutil.NoSuchProcess:
                        success_count += 1
                    except psutil.AccessDenied:
                        failed_count += 1
            if success_count > 0 and failed_count == 0:
                msg = f"{process_name} 共 {total_processes} 个进程，成功关闭 {success_count} 个进程"
                logger.info(msg)
                return {"success": True, "result": msg}
            elif success_count == 0 and failed_count > 0:
                msg = f"{process_name} 共 {total_processes} 个进程，关闭失败，共 {failed_count} 个进程未关闭"
                logger.error(msg)
                return {"success": False, "result": msg}
            elif success_count > 0 and failed_count > 0:
                msg = f"{process_name} 共 {total_processes} 个进程，部分关闭成功，成功关闭 {success_count} 个，失败 {failed_count} 个"
                logger.warning(msg)
                return {"success": False, "result": msg}
            else:
                msg = f"未找到名为 {process_name} 的进程"
                logger.info(msg)
                return {"success": False, "result": msg}
        except Exception as e:
            msg = f"操作失败: {process_name} - {str(e)}"
            logger.error(msg)
            return {"success": False, "result": msg}