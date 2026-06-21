import re
import time
import logging
import subprocess
from mcp.server.fastmcp import FastMCP
from handle.missing_params import ask_on_missing

logger = logging.getLogger('执行命令')

# GUI 程序名单：启动后进程不会自动退出，应超时后视为成功
_GUI_COMMANDS = [
    'notepad', 'calc', 'mspaint', 'explorer', 'snippingtool',
    'winword', 'excel', 'powerpnt', 'msedge', 'chrome', 'firefox',
]

def _is_gui_command(command_str: str) -> bool:
    """判断是否为 GUI 程序（启动后常驻不退）"""
    cmd_lower = command_str.strip().lower()
    for gui in _GUI_COMMANDS:
        # 匹配 notepad, start notepad, notepad.exe, "notepad" 等
        if gui in cmd_lower.split():
            return True
        if cmd_lower.startswith(gui) or cmd_lower == gui + '.exe':
            return True
    return False


def run_computer_command(mcp: FastMCP):
    @mcp.tool()
    @ask_on_missing('command_str')
    def run_computer_command(command_str: str = None, timeout: int = 5) -> str:
        """在电脑终端（Windows）运行传入的命令，并打印命令的状态和结果。
        Args:
            command_str (str): （必填）要运行的命令，字符串类型，例如：'ping qaqbuyan.com'
            timeout (int): 命令超时时间（秒），超过此时间视为命令已启动成功（可选，默认5秒）
        Returns:
            str: 命令执行结果，字符串类型
        """
        logger.info(f"执行命令: {command_str} ...")
        if not isinstance(command_str, str):
            msg = "传入的参数必须是字符串类型"
            logger.error(msg)
            return msg
        try:
            # GUI 程序非阻塞启动，不等待退出
            if _is_gui_command(command_str):
                subprocess.Popen(command_str, shell=True)
                msg = f"命令已成功启动，GUI 程序已在后台运行"
                logger.info(msg)
                return msg

            result = subprocess.run(command_str, shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                timeout=timeout)
            cleaned_stdout = re.sub(r'\s+', ' ', result.stdout.strip())
            msg = f"命令执行成功，退出状态码: {result.returncode}，标准输出: {cleaned_stdout}"
            logger.info(msg)
            return msg
        except subprocess.TimeoutExpired:
            # 超时可能是因为 GUI 程序常驻不退，视为启动成功
            logger.info(f"命令执行超时（{timeout}秒），可能为 GUI 程序，视为启动成功")
            return f"命令已成功启动，超过 {timeout} 秒未退出，程序可能已在后台运行"
        except subprocess.CalledProcessError as e:
            cleaned_stderr = re.sub(r'\s+', ' ', e.stderr.strip())
            msg = f"命令执行失败，退出状态码: {e.returncode}，标准错误: {cleaned_stderr}"
            logger.error(msg)
            return msg