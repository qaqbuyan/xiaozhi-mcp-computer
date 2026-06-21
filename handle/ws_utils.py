import logging
logger = logging.getLogger('管道代理')

# ---------- 错误检测 ----------
def is_ssl_error(error: Exception) -> bool:
    """判断异常是否为 SSL 证书错误"""
    error_str = str(error).lower()
    ssl_keywords = [
        'certificate verify failed',
        'self-signed certificate',
        'certificate has expired',
        'ssl',
        'sslv3',
        'tls',
    ]
    return any(kw in error_str for kw in ssl_keywords)

def is_self_signed_cert_error(error: Exception) -> bool:
    """判断是否为自签名证书链错误"""
    return 'self-signed certificate in certificate chain' in str(error).lower()

def is_dns_error(error: Exception) -> bool:
    """判断是否为 DNS 解析失败错误"""
    error_str = str(error).lower()
    return ('getaddrinfo failed' in error_str
            or 'name or service not known' in error_str
            or 'temporary failure in name resolution' in error_str)

# ---------- 异常消息翻译 ----------
_WS_ERROR_TRANSLATIONS = {
    'no close frame received or sent': '未收到或发送关闭帧',
    'timed out': '连接超时',
    'during opening handshake': '在建立握手连接时',
    'connection closed': '连接已关闭',
    'connection refused': '连接被拒绝',
    'name or service not known': '无法解析服务器域名',
    'temporary failure in name resolution': 'DNS 临时解析失败',
    'getaddrinfo failed': 'DNS 地址解析失败',
    'certificate verify failed': 'SSL 证书验证失败',
    'self-signed certificate': '使用了自签名证书',
    'ssl': 'SSL 连接异常',
    'broken pipe': '管道连接已断开',
    'connection reset by peer': '连接被远程主机重置',
    'connection aborted': '连接被中止',
    'network is unreachable': '网络不可达',
}

def translate_ws_error(error: Exception) -> str:
    """将 WebSocket 相关的英文异常消息翻译为中文（逐条替换，支持多条匹配）"""
    error_str = str(error)
    for eng, cn in _WS_ERROR_TRANSLATIONS.items():
        if eng in error_str.lower():
            idx = error_str.lower().index(eng)
            error_str = error_str[:idx] + cn + error_str[idx + len(eng):]
    return error_str

# ---------- 引导日志（仅首次输出） ----------
_dns_error_guided = False
_ssl_error_guided = False

def log_dns_guidance():
    """输出 DNS 解析错误的用户引导信息（仅首次输出）"""
    global _dns_error_guided
    if _dns_error_guided:
        return
    _dns_error_guided = True
    guidance = (
        "╔══════════════════════════════════════════════════════════════╗\n"
        "║  DNS 解析失败，无法找到服务器地址                             ║\n"
        "╠══════════════════════════════════════════════════════════════╣\n"
        "║  这是客户端网络环境问题，常见原因及解决方法：                 ║\n"
        "║  1. 网络未连接 → 请检查网络是否正常                          ║\n"
        "║  2. DNS 服务器异常 → 尝试将 DNS 改为 114.114.114.114         ║\n"
        "║     或 8.8.8.8 后重试                                         ║\n"
        "║  3. 域名解析被拦截 → 检查代理/VPN 配置或切换手机热点测试     ║\n"
        "╚══════════════════════════════════════════════════════════════╝"
    )
    logger.warning(f"\n{guidance}")

def log_ssl_guidance():
    """输出 SSL 证书错误的用户引导信息（仅首次输出）"""
    global _ssl_error_guided
    if _ssl_error_guided:
        return
    _ssl_error_guided = True
    guidance = (
        "╔══════════════════════════════════════════════════════════════╗\n"
        "║  SSL 证书验证失败，无法安全连接到服务器                      ║\n"
        "╠══════════════════════════════════════════════════════════════╣\n"
        "║  这是客户端网络环境问题，常见原因及解决方法：                 ║\n"
        "║  1. 系统时间不正确 → 请校准系统时间后再试                    ║\n"
        "║  2. 公司/学校网络开启了 SSL 审查（代理拦截）                  ║\n"
        "║     → 请关闭代理/VPN，或切换到手机热点网络测试               ║\n"
        "║  3. 杀毒软件（如 360、卡巴斯基）启用了 HTTPS 扫描            ║\n"
        "║     → 请在杀毒软件中关闭 HTTPS/SSL 扫描功能                  ║\n"
        "╚══════════════════════════════════════════════════════════════╝"
    )
    logger.warning(f"\n{guidance}")

# ---------- 进程清理 ----------
def cleanup_all_processes():
    """清理所有相关进程的全局函数"""
    logger.info("开始全局进程清理...")
    try:
        from utils.music.play import GlobalProcessManager
        process_manager = GlobalProcessManager()
        process_manager.cleanup_all_processes()
        logger.info("全局进程清理完成")
    except ImportError:
        logger.info("音乐模块未加载，跳过进程清理")
    except Exception as e:
        logger.error(f"全局进程清理出错: {translate_ws_error(e)}")