"""
common - 工具函数模块

函数：封装功能上相对独立而且会被重复使用的代码。
装饰器：用一个函数去装饰另外一个函数或类并为其提供额外的能力。

lru - 缓存置换策略 - least recently used - 最近最少使用
cache - 缓存 - 空间换时间 - 优化性能

Author: 骆昊
Version: 0.1
Date: 2025/6/17
"""
import json
from functools import lru_cache


@lru_cache(maxsize=64)
def get_llm_response(client, *, system_prompt='', few_shot_prompt='',
                     user_prompt='', model='gpt-4o-mini', temperature=0.2,
                     top_p=0.1, frequency_penalty=0, presence_penalty=0,
                     max_tokens=1024, stream=False):
    """
    获取大模型响应
    :param client: OpenAI对象
    :param system_prompt: 系统提示词
    :param few_shot_prompt: 小样本提示（JSON字符串）
    :param user_prompt: 用户提示词
    :param model: 模型名称
    :param temperature: 温度参数
    :param top_p: Top-P参数
    :param frequency_penalty: 频率惩罚参数
    :param presence_penalty: 出现惩罚参数
    :param max_tokens: 最大token数量
    :param stream: 是否开启流模型
    :return: 大模型的响应内容或Stream对象
    """
    messages = []

    if system_prompt:
        messages.append({'role': 'system', 'content': system_prompt})
    if few_shot_prompt:
        messages += json.loads(few_shot_prompt)
    if user_prompt:
        messages.append({'role': 'user', 'content': user_prompt})

    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        max_tokens=max_tokens,
        messages=messages,
        stream=stream,
    )
    if not stream:
        return resp.choices[0].message.content
    return resp

def get_llm_response(client, model, user_prompt, stream=False):
    """
    获取大语言模型的响应
    
    Args:
        client: OpenAI客户端
        model: 模型名称
        user_prompt: 用户输入的提示
        stream: 是否使用流式输出
    
    Returns:
        响应对象或流式响应
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": user_prompt}
            ],
            stream=stream,
            temperature=0.7,
            max_tokens=2000
        )
        return response
    except Exception as e:
        print(f"获取LLM响应时出错: {e}")
        raise e