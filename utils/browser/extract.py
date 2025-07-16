def extract_bookmarks(node, parent_folder=''):
    """递归提取书签信息
    Args:
        node: 书签节点
        parent_folder: 父文件夹名称
    Returns:
        dict: 包含书签或文件夹信息的字典
    """
    if node['type'] == 'url':
        url = node.get('url', '')
        if url.startswith(('http://', 'https://')):
            return {
                'title': node.get('name', ''),
                'url': url
            }
        return None
    elif node['type'] == 'folder':
        folder = {
            'folder': node.get('name', '未分类'),
            'list': []
        }
        for child in node['children']:
            item = extract_bookmarks(child, node.get('name', ''))
            if item:
                folder['list'].append(item)
        return folder