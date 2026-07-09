from typing import Dict,Any
from mymcp.MCPClient import mcp_callback
from langchain_core.tools import Tool


def search_weather(city: str) ->Dict[str,any]:

    """
    :param city:城市名
    :return:该城市天气实况结果
    """
    return mcp_callback(tool_name="search_weather",city=city)

#数据库查询工具
def db_query(sql:str=None,params:list = None,**kwargs) ->Dict[str,any]:
    """
    :params sql:执行查询的命令
    :params params:执行查询的命令中的参数
    :return:查询结果，字典格式
    """
    return mcp_callback(tool_name="db_query",sql=sql,params=params or [])

#图表生成工具
def generate_chart(chart_name:str) ->Dict[str,any]:
    """
    :params params: json字符串或者字典，绘制图标的参数
    :return:图标的结果
    """
    return mcp_callback(tool_name="generate_chart",chart_name=chart_name)

#注册工具
def my_tools():
    return [
        Tool(
            name="search_weather",
            func=search_weather,
            description="""
            根据用户输入的城市名，查询该城市的天气情况，以字符串形似返回结果
            """,
        ),
        Tool(
            name="db_query",
            func=db_query,
            description="""
                查询数据库中的数据
                数据库包含一张表：orders（订单表），字段如下：
                    - id：订单ID
                    - order_no：订单编号
                    - customer_name：客户名称
                    - product_name：商品名称
                    - quantity：商品数量
                    - order_amount：订单金额
                    - order_date：下单日期（格式：YYYY-MM-DD）
                    - status：支付状态（如“已支付”、“未支付”）
                    - city：客户所在城市
                    - 支持参数化查询，如：`SELECT * FROM orders WHERE city=%s AND order_amount > %s`
            """
        ),
        Tool(
            name="generate_chart",
            func=generate_chart,
            description="""
                绘制图表：
                   - 只返回 ECharts 配置 JSON 对象的内部内容（即 `{{ ... }}`）。
                   - 不要输出 `var option =` 或任何额外的 JavaScript 代码。
                   - 不要输出额外的文字内容。
                   - 输出必须合法 JSON，可直接用 `JSON.parse()` 解析。
                   - 根据查询结果自动生成图表的标题、坐标轴、图例、系列数据、不同的数据内容图例中用不同颜色。
            """
        ),

    ]