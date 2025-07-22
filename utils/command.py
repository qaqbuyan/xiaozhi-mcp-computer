import re
import logging
import subprocess
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('执行命令')

def run_computer_command(mcp: FastMCP):
    @mcp.tool()
    def run_computer_command(command_str: str) -> str:
        """在电脑终端（Windows）运行传入的命令，并打印命令的状态和结果。
        Args:
            command_str (str): （必填）要运行的命令，字符串类型，例如：'ping qaqbuyan.com'
        Returns:
            str: 命令执行结果，字符串类型
        """
        logger.info(f"执行命令: {command_str} ...")
        if not isinstance(command_str, str):
            msg = "传入的参数必须是字符串类型"
            logger.error(msg)
            return msg
        try:
            result = subprocess.run(command_str, shell=True, check=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            cleaned_stdout = re.sub(r'\s+', ' ', result.stdout.strip())
            msg = f"命令执行成功，退出状态码: {result.returncode}，标准输出: {cleaned_stdout}"
            logger.info(msg)
            return msg
        except subprocess.CalledProcessError as e:
            cleaned_stderr = re.sub(r'\s+', ' ', e.stderr.strip())
            msg = f"命令执行失败，退出状态码: {e.returncode}，标准错误: {cleaned_stderr}"
            logger.error(msg)
            return msg