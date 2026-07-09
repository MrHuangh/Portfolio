# 导入加载模型需要的库
import os


from langchain_openai import ChatOpenAI


# 加载模型的函数
def load_model():
    return ChatOpenAI(
        model="qwen2.5-32b-instruct",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        streaming=False,
    )
