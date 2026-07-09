# 导入返回数据用的类
from django.http import JsonResponse
import json
from models.LoadModel import load_model
from agents.LoadAgent import load_agent
from utils.ResponseUtil import response_util
# 用户对话连天的接口
def chat(request):
    # 取出客户端传过来的参数 question
    question = request.GET.get("question")
    #调用智能体 得到返回的结果
    agent = load_agent()
    response = agent.invoke({
        "messages": question
    }, config={
        "recursion_limit": 50
    })

    return JsonResponse({
        "role": "assistant",
        "type": "text",
        "content":response_util(response)

    })