import logging
from handle.version import get_version
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('版本更新')

def acquire_version(mcp: FastMCP):
    @mcp.tool()
    def acquire_version(version: str) -> str:
        """用于根据传入的版本号查询客户端版本信息，并输出对应版本的链接。
            当需要查询版本链接时，立刻使用该工具。
            如果正常返回了url，直接调用工具 "download_file" 下载对应版本的客户端，参数为返回的那个地址url。
            除非用户询问该链接否则不向用户展示该链接。
        Args:
            version (str): 要查询的版本号。(例如: "0.1.5")
        Returns:
            str: 包含对应版本的链接的字符串。
        """
        logger.info(f"进行版本 {version} 的更新...")
        try:
            data = get_version(True)
            # 检查 data 是否为字典类型
            if not isinstance(data, dict):
                error = f"错误：get_version 返回的数据不是字典类型，而是 {type(data).__name__} 类型。"
                logger.error(error)
                return error
            logger.debug(f"遍历所有消息项，查找版本 {version}")
            # 从 all_updates 中查找版本信息
            for message in data.get('all_updates', []):
                logger.debug(f"当前检查的消息项: {message}")
                item_version_number = message.get('version', '')
                item_version_type = message.get('type', '')
                full_item_version = f"{item_version_number}-{item_version_type.lower()}"
                if full_item_version == version.lower():
                    link = message.get('link', '')
                    from urllib.parse import urlparse
                    parsed = urlparse(link)
                    if all([parsed.scheme, parsed.netloc]):
                        logger.info(f"版本 {version} 的链接获取成功")
                        logger.info(f"返回消息: {link}")
                        return link
                    else:
                        msg = "无法进行更新，该链接不是合法的 URL。"
                        logger.warning(msg)
                        return msg
            error = f"错误：未找到版本 {version}。"
            logger.error(error)
            return error
        except Exception as e:
            error = f"处理版本更新时出错: {e}"
            logger.error(error)
            return error