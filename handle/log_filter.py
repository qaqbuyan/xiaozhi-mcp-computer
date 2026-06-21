import logging

class RequestTypeTranslator(logging.Filter):
    """将 MCP 底层库的英文日志翻译为中文"""

    _type_map = {
        'PingRequest': '心跳包',
        'ListToolsRequest': '获取工具列表',
        'CallToolRequest': '调用工具',
        'ListResourcesRequest': '获取资源列表',
        'ReadResourceRequest': '读取资源',
        'ListPromptsRequest': '获取提示列表',
        'GetPromptRequest': '获取提示',
        'InitializeRequest': '初始化',
        'ListResourceTemplatesRequest': '获取资源模板列表',
        'SetLevelRequest': '设置日志级别',
        'CompleteRequest': '自动补全',
    }

    def filter(self, record):
        msg = record.getMessage()
        if msg.startswith('Processing request of type '):
            req_type = msg[len('Processing request of type '):]
            cn_type = self._type_map.get(req_type, req_type)
            record.msg = f'处理 {cn_type} 类型的请求'
            record.args = ()
            record.name = '管道代理'
        return True