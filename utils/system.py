import socket
import psutil
import logging
import platform
from datetime import datetime
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('系统信息')

# 获取系统状态监控信息
def get_system_status(mcp: FastMCP):
    @mcp.tool()
    def get_system_status() -> dict:
        """用于获取电脑状态监控信息，可以查询CPU、内存、磁盘、网络信息。当查询电脑状态或者获取电脑信息时，立刻使用该工具"""
        logger.info("开始获取系统状态信息...")
        # 获取系统信息
        system_info = {
            'os': platform.system(),
            'os_version': platform.version(),
            'hostname': socket.gethostname(),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        # CPU信息
        cpu_info = {
            'percent': psutil.cpu_percent(interval=1),  # 1秒内的CPU使用率
            'count': psutil.cpu_count(logical=True),  # 逻辑CPU核心数
            'freq': psutil.cpu_freq(),  # CPU频率
            'times': psutil.cpu_times_percent()  # CPU时间百分比
        }
        # 内存信息
        memory_info = {
            'total': psutil.virtual_memory().total,  # 总内存
            'available': psutil.virtual_memory().available,  # 可用内存
            'used': psutil.virtual_memory().used,  # 已使用内存
            'percent': psutil.virtual_memory().percent,  # 内存使用率
            'swap_total': psutil.swap_memory().total,  # 总交换空间
            'swap_used': psutil.swap_memory().used,  # 已使用交换空间
            'swap_percent': psutil.swap_memory().percent  # 交换空间使用率
        }
        # 磁盘信息
        disk_info = []
        partitions = psutil.disk_partitions()
        for partition in partitions:
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
                disk_info.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'total': partition_usage.total,
                    'used': partition_usage.used,
                    'free': partition_usage.free,
                    'percent': partition_usage.percent
                })
            except PermissionError:
                # 忽略无法访问的分区
                continue
        # 网络信息
        network_info = {
            'interfaces': {}
        }
        net_io_counters = psutil.net_io_counters(pernic=True)
        for interface, counters in net_io_counters.items():
            network_info['interfaces'][interface] = {
                'bytes_sent': counters.bytes_sent,
                'bytes_recv': counters.bytes_recv,
                'packets_sent': counters.packets_sent,
                'packets_recv': counters.packets_recv
            }
        # 组合所有信息
        system_status = {
            'system': system_info,
            'cpu': cpu_info,
            'memory': memory_info,
            'disk': disk_info,
            'network': network_info
        }
        logger.info("成功获取系统状态信息")
        logger.info(f"返回数据：{system_status}")
        return system_status