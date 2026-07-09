import httpx
import os
from fastmcp import FastMCP
import pymysql
import json
mcp = FastMCP("MCP SERVICE")
#天气实况查询工具
@mcp.tool(
    name="search_weather",
    description="根据用户输入的城市名，查询该城市当前的天气情况，以字符串形似返回结果",
)
async def search_weather(city: str) -> str:
    api_key = os.getenv("XINZHI_API_KEY")
    url = f"https://api.seniverse.com/v3/weather/now.json?key={api_key}&location={city}&language=zh-Hans&unit=c"
    with httpx.Client() as client:
        response = client.get(url)
        data = response.json()
        name = data['results'][0]['location']['name']
        text = data['results'][0]['now']['text']
        temperature = data['results'][0]['now']['temperature']
        last_update = data['results'][0].get('last_update', data['results'][0].get('now', {}).get('last_update', '未知'))
        result = f"{name}的天气{text},温度为{temperature}℃,更新为{last_update}"
        return result
#数据库操作工具
@mcp.tool(
    name="db_query",
    description="查询数据库中的数据",
)
async def db_query(sql: str,params:list=None) -> dict:
        conn = pymysql.connect(
            host="localhost",
            port=3306,
            user="root",
            passwd="janjohn",
            database='chatbi_agent',
            charset='utf8',
        )
        cur = conn.cursor()
        cur.execute(sql,params or ())
        data = cur.fetchall()
        description = cur.description
        cur.close()
        conn.close()
        description = [item[0] for item in description]
        result = [dict(zip(description, item)) for item in data]
        return {"result": result}


#图表 echarts工具
@mcp.tool(
    name="generate_chart",
    description="生成用户需求的饼图、柱状图、折线图的json数据",
)
async def generate_chart(chart_name: str = None, params: dict | str = None) -> dict:
    if chart_name and not params:
        # 如果传入的是 chart_name（字符串），尝试解析为 JSON
        try:
            params = json.loads(chart_name.replace("'",'"'))
        except:
            params = chart_name
    if not params:
        return {"error": "缺少参数", "result": {}}
    if isinstance(params, str):
        params = json.loads(params.replace("'",'"'))
    chart_type = params.get("chart_type","line")
    title = params.get("title","图表")
    if chart_type == "pie":
        data = params.get("data",[])
        option = {
            "title": {
                "text": title,
                "subtext": 'Fake Data',
                "left": 'center',
            },
            "tooltip": {
                "trigger": 'item'
            },
            "legend": {
                "orient": 'vertical',
                "left": 'left',
            },
            "series": [
                {
                    "name": 'Access From',
                    "type": 'pie',
                    "radius": '50%',
                    "data": data,
                    "emphasis": {
                        "itemStyle": {
                            "shadowBlur": 10,
                            "shadowOffsetX": 0,
                            "shadowColor": 'rgba(0, 0, 0, 0.5)',
                        }
                    }
                }
            ]
        }
        return option
    X = params.get("X",[])
    Y = params.get("Y",[])
    option = {
        "title": {
            "text": title,
        },
        "tooltip": {
            "trigger": 'axis',
        },
        "xAxis": {
            "type": 'category',
            "data": X,
        },
        "yAxis": {
            "type": 'value',
        },
        "series": [
            {
                "data": Y,
                "type": chart_type,
            }
        ]
    }
    return option

if __name__ == '__main__':
        mcp.run(
        transport="http",
        host="localhost",
        port=9000,
        show_banner=True,
        )