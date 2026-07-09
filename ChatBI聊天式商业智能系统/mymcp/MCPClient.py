from fastmcp import Client
import asyncio

MCP_SERVER = "http://localhost:9000/mcp"

def mcp_callback(tool_name:str,**kwargs):
    async def _call():
        async with Client(MCP_SERVER) as client:
            response = await client.call_tool(tool_name, kwargs)
            return response

    return asyncio.run(_call())


if __name__ == '__main__':
    print(mcp_callback(tool_name='db_query',sql="select * from orders where order_id=1"))