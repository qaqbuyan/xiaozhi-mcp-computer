import logging
import inspect
from typing import Any, Dict, List

logger = logging.getLogger('缺参追问')

SENTINEL = object()

def is_missing(value: Any) -> bool:
    """判断参数值是否为"缺失"状态"""
    if value is None:
        return True
    if value is SENTINEL:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, (list, tuple, set)) and len(value) == 0:
        return True
    if isinstance(value, dict) and len(value) == 0:
        return True
    return False

def type_to_str(annotation) -> str:
    """将类型注解转为可读字符串"""
    if annotation is None or annotation is inspect.Parameter.empty:
        return "any"
    if hasattr(annotation, '__name__'):
        return annotation.__name__
    origin = getattr(annotation, '__origin__', None)
    if origin is not None:
        args = getattr(annotation, '__args__', ())
        arg_names = [type_to_str(a) for a in args]
        return f"{origin.__name__}[{', '.join(arg_names)}]"
    return str(annotation)

def parse_param_descriptions(func) -> Dict[str, str]:
    """从函数 docstring 的 Args 段解析参数描述"""
    descriptions = {}
    doc = func.__doc__
    if not doc:
        return descriptions

    in_args = False
    for line in doc.split('\n'):
        stripped = line.strip()

        if stripped.startswith('Args:') or stripped.startswith('Args'):
            in_args = True
            continue
        if in_args and (stripped.startswith('Returns:') or stripped.startswith('Returns') or stripped.startswith('Raises:')):
            break

        if in_args and stripped:
            if '(' in stripped and ':' in stripped:
                parts = stripped.split('(', 1)
                param_name = parts[0].strip()
                desc_part = stripped[len(param_name):].strip()
                if desc_part.startswith('('):
                    close_paren = desc_part.find(')')
                    if close_paren != -1:
                        type_str = desc_part[1:close_paren]
                        remaining = desc_part[close_paren + 1:].strip()
                        if remaining.startswith(':'):
                            remaining = remaining[1:].strip()
                        descriptions[param_name] = remaining
                    else:
                        descriptions[param_name] = desc_part
                else:
                    descriptions[param_name] = desc_part
            elif ':' in stripped:
                parts = stripped.split(':', 1)
                param_name = parts[0].strip()
                descriptions[param_name] = parts[1].strip()

    return descriptions

def generate_question(param_name: str, description: str) -> str:
    """根据参数名和描述生成自然语言追问"""
    if description:
        return f"请提供：{description}"
    return f"请提供参数 '{param_name}' 的值"

def build_ask_response(tool_name: str, missing_params: List[Dict]) -> Dict:
    """构建结构化的追问响应"""
    param_list = []
    questions = []
    for p in missing_params:
        desc = p.get('description', p['name'])
        param_list.append(f"- **{p['name']}** ({p['type']}): {desc}")
        questions.append(generate_question(p['name'], desc))

    message_lines = [
        f"要完成「{tool_name}」操作，还需要以下信息，请向用户询问：",
        "",
    ]
    message_lines.extend(param_list)
    message_lines.append("")
    message_lines.append("请根据以上缺失参数，逐一向用户提问以获取必要信息后，重新调用该工具。")

    return {
        "need_user_input": True,
        "action": "ask_user",
        "tool": tool_name,
        "missing_params": [
            {
                "name": p['name'],
                "type": p['type'],
                "description": p.get('description', ''),
                "question": generate_question(p['name'], p.get('description', ''))
            }
            for p in missing_params
        ],
        "message": "\n".join(message_lines)
    }