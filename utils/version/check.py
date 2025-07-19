import logging
from handle.version import get_version
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('版本检查')

def check_version(mcp: FastMCP):
    @mcp.tool()
    def check_version(all_version: bool = False) -> dict:
        """用于获取当前客户端最新的版本，当需要获取客户端版本信息时，立刻使用该工具。
            该工具会返回一个字符串，包含当前客户端的版本信息。
            可以询问是否需要获取所有版本的更新日志。
        Args:
            all_version (bool): 是否获取所有版本更新日志，默认为 False。
                True: 获取所有版本更新日志。
                False: 获取最新版本更新日志。
        Returns:
            str: 包含当前客户端的版本信息的字符串。
            字典格式：
            "current_version" : 当前版本号,
            "latest_version" : 最新版本号,
                如果发现当前版本号跟新版本不一致，需要告诉用户当前的版本是多少。
                可以询问是否需要更新客户端，需要立刻调用‘ update_client ‘工具，如果是一样的版本就不要进行询问。
            "all_updates" : [
                {
                    "version": 版本号,
                    "content": 更新日志,
                    "time": 更新时间,
                    "size": 更新大小,
                    "hash": 更新文件的SHA256值,
                    "type": 更新类型,
                        "Beta" 公开测试，功能基本完整
                        "Alpha" 早期开发，内部测试
                        "RC" 接近正式版，仅修复少量问题
                        "Stable" 经过全面测试，功能完整且稳定，面向普通用户正式发布
                    "link": 更新链接
                },
                ...
            ]
        """
        logger.info("进行版本查询...")
        msg = get_version(all_version)
        return msg