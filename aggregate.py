import time
import logging
from services.register import register
from mcp.server.fastmcp import FastMCP
from handle.version import get_version
from handle.logger import setup_logging
from handle.check import check_packages

if __name__ == "__main__":
    check_packages()
    logger = setup_logging()
    logger = logging.getLogger('管道服务')
    # 调用版本检查函数
    get_version(False)
    logger.info("启动注册服务...")
    # 创建MCP服务器
    mcp = FastMCP("管道服务")
    # 注册服务
    register(mcp)
    # 添加初始化完成标志
    mcp._initialized = True
    logger.info("服务注册完成，准备接收请求")
    # 确保服务注册完成后再启动服务器
    try:
        mcp.run(transport="stdio")
    except RuntimeError as e:
        logger.error(f"服务器启动失败: {e}")
    # 等待服务端初始化完成
    while True:
        try:
            if mcp.check_initialization():
                break
        except Exception:
            pass
        logger.info("等待服务端初始化完成...")
        time.sleep(1)