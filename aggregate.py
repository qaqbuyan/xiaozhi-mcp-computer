import sys
import time
import signal
import logging
from services.register import register
from mcp.server.fastmcp import FastMCP
from handle.version import get_version
from handle.logger import setup_logging
from handle.check import check_packages

def cleanup_on_exit():
    """程序退出时的清理函数"""
    logger.info("程序正在退出，开始清理资源...")
    try:
        from utils.music.play import GlobalProcessManager
        process_manager = GlobalProcessManager()
        process_manager.cleanup_all_processes()
        logger.info("所有进程清理完成")
    except ImportError:
        logger.info("音乐模块未加载，跳过进程清理")
    except Exception as e:
        logger.error(f"清理进程时出错: {str(e)}")

def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"收到信号 {signum}，开始优雅退出...")
    cleanup_on_exit()
    sys.exit(0)

if __name__ == "__main__":
    # 注册信号处理器
    for sig in [signal.SIGINT, signal.SIGTERM]:
        try:
            signal.signal(sig, signal_handler)
        except (OSError, ValueError):
            pass
    
    try:
        logger = setup_logging()
        logger = logging.getLogger('管道服务')
        logger.info("启动环境检查..")
        check_packages()
        logger.info("环境检查完成")
    except Exception as e:
        logger.error(f"环境检查失败：{str(e)}")
        raise
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
    try:
        while True:
            try:
                if mcp.check_initialization():
                    break
            except Exception:
                pass
            logger.info("等待服务端初始化完成...")
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("收到中断信号，开始退出...")
    finally:
        # 程序退出时清理资源
        cleanup_on_exit()