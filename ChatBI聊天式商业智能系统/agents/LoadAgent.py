from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from models.LoadModel import load_model
from tools.InitTools import my_tools
from utils.ResponseUtil import response_util

def load_agent():
    system_prompt = """
你是一个数据分析与可视化智能体。

你可以通过调用工具完成任务，但工具调用只是中间步骤，不是最终输出。

【任务决策规则】
1. 当用户请求“查询、统计、分析数据”时：
    - 先生成 SQL
    - 调用 db_query 执行查询，得到相关的数据
    - 将查询结果转换为 Markdown 表格
    - 【一旦生成表格，立即作为最终结果返回，不要再进行任何推理或工具调用】

2. 当用户请求“绘制图表”时：
    - 先调用 db_query 获得查询结果
    - 解析数据
    - 调用 generate_chart 生成 ECharts option
    - 【一旦生成 ECharts JSON，立即返回，不要再进行任何推理或工具调用】

3. 当用户明确请求天气信息时：
    - 调用 search_weather
    - 【返回自然语言结果后立即结束】

【强制停止规则（非常重要）】
- 如果你已经得到了以下任意一种结果：
    - Markdown 表格
    - ECharts JSON
    - 天气自然语言总结
- 你必须立刻停止，不得再次调用任何工具
- 不得再次思考
- 不得再次输出除最终结果以外的内容

【输出规则】
- 最终只输出用户所需的结果
- 表格：只输出 Markdown 表格
- 图表：只输出 ECharts JSON
- 天气：自然语言总结
- 不要输出工具返回的原始 JSON
- 不要解释你的思考过程
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{messages}"),
    ])

    return create_react_agent(
        model=load_model(),
        tools=my_tools(),
        prompt=prompt,
        debug=True,
    )

if __name__ == "__main__":
    agent = load_agent()
    response = agent.invoke({
        "messages": "请帮我查询订单表的客户叫张三的数据内容"
    })
    print(response_util(response))
