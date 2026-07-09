from langchain_core.messages import AIMessage
import json
import re

def response_util(rs):
    # 如果 rs 是元组，提取第一个元素（字典）
    if isinstance(rs, tuple):
        rs = rs[0]
    messages = rs['messages']
    data = []
    for msg in messages:
        if isinstance(msg, AIMessage) and msg.content:
            data.append(msg.content)
    if len(data) == 0:
        return"模型没有输出"
    content = data[-1]
    
    # 如果 content 是字典或列表，转换为 JSON 字符串
    if isinstance(content, (dict, list)):
        return json.dumps(content, ensure_ascii=False)
    
    # 如果 content 是字符串
    if isinstance(content, str):
        # 尝试解析为 JSON（如果已经是 JSON 字符串）
        try:
            parsed = json.loads(content)
            # 如果解析成功，重新序列化以确保格式正确
            return json.dumps(parsed, ensure_ascii=False)
        except (json.JSONDecodeError, ValueError):
            # 如果不是有效的 JSON，尝试从 Markdown 代码块中提取 JSON
            # 查找 ```json 或 ``` 代码块
            code_block_pattern = r'```(?:json)?\s*\n(.*?)```'
            matches = re.finditer(code_block_pattern, content, re.DOTALL)
            for match in matches:
                json_str = match.group(1).strip()
                if json_str:
                    try:
                        parsed = json.loads(json_str)
                        # 如果解析成功，返回格式化的 JSON
                        return json.dumps(parsed, ensure_ascii=False)
                    except (json.JSONDecodeError, ValueError):
                        continue
            # 如果代码块匹配失败，尝试查找整个字符串中的第一个完整 JSON 对象
            # 从第一个 { 开始，找到匹配的 }
            start_idx = content.find('{')
            if start_idx != -1:
                brace_count = 0
                for i in range(start_idx, len(content)):
                    if content[i] == '{':
                        brace_count += 1
                    elif content[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_str = content[start_idx:i+1]
                            try:
                                parsed = json.loads(json_str)
                                # 检查是否是 ECharts 配置（包含常见字段）
                                if isinstance(parsed, dict) and any(key in parsed for key in ['series', 'xAxis', 'yAxis', 'title', 'tooltip']):
                                    return json.dumps(parsed, ensure_ascii=False)
                            except (json.JSONDecodeError, ValueError):
                                break
            # 如果都不行，直接返回原字符串
            return content
    
    # 其他类型，转换为字符串
    return str(content)