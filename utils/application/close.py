import os
import psutil
import logging
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('关闭程序')

def close_application(mcp: FastMCP):
    @mcp.tool()
    def close_application(process_name: str) -> dict:
        """关闭指定名称的程序，若程序未响应则尝试强制终止。
        当需要关闭某个程序时，立刻使用该工具。
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
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'].lower() == full_process_name.lower() and proc.pid != current_pid:
                    total_processes += 1
            for proc in psutil.process_iter(['name']):
                if proc.info['name'].lower() == full_process_name.lower() and proc.pid != current_pid:
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
                return {"success": True, "result": "成功关闭"}
            elif success_count == 0 and failed_count > 0:
                msg = f"{process_name} 共 {total_processes} 个进程，关闭失败，共 {failed_count} 个进程未关闭"
                logger.error(msg)
                return {"success": False, "result": "没有正常关闭完"}
            elif success_count > 0 and failed_count > 0:
                msg = f"{process_name} 共 {total_processes} 个进程，部分关闭成功，成功关闭 {success_count} 个，失败 {failed_count} 个"
                logger.warning(msg)
                return {"success": False, "result": "没有正常关闭完"}
            else:
                msg = f"未找到名为 {process_name} 的进程"
                logger.info(msg)
                return {"success": False, "result": msg}
        except Exception as e:
            msg = f"操作失败: {process_name} - {str(e)}"
            logger.error(msg)
            return {"success": False, "result": msg}