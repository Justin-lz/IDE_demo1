import duckdb
import pandas as pd

# 初始化数据库连接
conn = duckdb.connect(database='knowledge_db.duckdb')

# 读取CSV文件
df = pd.read_csv('./datasets/data1.csv')

# 创建数据表
conn.execute(
    """
    DROP TABLE IF EXISTS knowledge_base;
    CREATE TABLE knowledge_base (
        关键词 VARCHAR PRIMARY KEY,
        简介 VARCHAR,
        详解 VARCHAR,
        click INTEGER DEFAULT 1
    )
    """
)

# 清空旧数据并插入新数据
conn.execute("DELETE FROM knowledge_base")
# 批量插入/更新数据
params = [
    (row['关键词'], row['简介'], row['详解'] if pd.notnull(row['详解']) else None, 1)
    for _, row in df.iterrows()
]
conn.executemany(
    "INSERT OR REPLACE INTO knowledge_base (关键词, 简介, 详解, click) VALUES (?, ?, ?, ?)",
    params
)

# 创建全文搜索索引
conn.execute("DROP INDEX IF EXISTS idx_keywords; CREATE INDEX idx_keywords ON knowledge_base (关键词)")
conn.close()
print('数据库初始化完成！')