import inspect
import logging
import functools
from typing import Any, Callable, Dict, List, Optional

from handle.missing_utils import (
    is_missing,
    type_to_str,
    parse_param_descriptions,
    build_ask_response,
)

logger = logging.getLogger('缺参追问')

def ask_on_missing(*required_params: str):
    """
    装饰器：
    当指定的必填参数缺失时，返回结构化追问响应，主动引导 AI 向用户提问。
    返回格式:
        {
            "need_user_input": true,
            "action": "ask_user",
            "tool": "函数名",
            "missing_params": [...],
            "message": "自然语言追问信息"
        }
    """

    def decorator(func: Callable) -> Callable:
        sig = inspect.signature(func)
        param_descriptions = parse_param_descriptions(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
            except TypeError:
                # 参数绑定失败，直接从 kwargs 判断哪些 required_params 缺失
                missing = []
                for name in required_params:
                    param_obj = sig.parameters.get(name)
                    if not param_obj:
                        continue
                    if name not in kwargs:
                        type_str = type_to_str(param_obj.annotation)
                        missing.append({
                            'name': name,
                            'type': type_str,
                            'description': param_descriptions.get(name, '')
                        })
                        continue
                    value = kwargs[name]
                    if is_missing(value):
                        type_str = type_to_str(param_obj.annotation)
                        missing.append({
                            'name': name,
                            'type': type_str,
                            'description': param_descriptions.get(name, '')
                        })

                if missing:
                    response = build_ask_response(func.__name__, missing)
                    logger.info(f"工具 {func.__name__} 参数绑定失败，缺少参数: {[m['name'] for m in missing]}，返回追问响应")
                    return response

                logger.info(f"工具 {func.__name__} 参数绑定失败（args={args}, kwargs={kwargs}），返回通用追问")
                return {
                    "need_user_input": True,
                    "action": "ask_user",
                    "tool": func.__name__,
                    "missing_params": [],
                    "message": (
                        f"要完成「{func.__name__}」操作，缺少必要参数，请提供相关信息后重新调用。\n"
                        f"期望参数：{', '.join(sig.parameters.keys())}"
                    )
                }

            missing = []
            for name in required_params:
                if name not in bound.arguments:
                    param_obj = sig.parameters.get(name)
                    type_str = type_to_str(param_obj.annotation) if param_obj else "any"
                    missing.append({
                        'name': name,
                        'type': type_str,
                        'description': param_descriptions.get(name, '')
                    })
                    continue

                value = bound.arguments[name]
                if is_missing(value):
                    param_obj = sig.parameters.get(name)
                    type_str = type_to_str(param_obj.annotation) if param_obj else "any"
                    missing.append({
                        'name': name,
                        'type': type_str,
                        'description': param_descriptions.get(name, '')
                    })

            if missing:
                response = build_ask_response(func.__name__, missing)
                logger.info(f"工具 {func.__name__} 缺少参数: {[m['name'] for m in missing]}，返回追问响应")
                return response

            return func(*args, **kwargs)

        return wrapper
    return decorator