import pymysql
if __name__ == '__main__':
    conn = pymysql.connect(
        host="localhost",
        port=3306,
        user="root",
        passwd="janjohn",
        database='chatbi_agent',
        charset='utf8mb4',
    )
print(conn)
cur = conn.cursor()
sql = "select * from orders"
cur.execute(sql,[])
data = cur.fetchall()
description = cur.description
cur.close()
conn.close()
result = []
description = [item[0] for item in description]
result = [dict(zip(description, item)) for item in data]
print(result)
