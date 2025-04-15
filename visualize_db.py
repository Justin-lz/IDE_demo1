import os
import duckdb
import pandas as pd
import pygwalker as pyg
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei'] # 设置字体为黑体
plt.rcParams['axes.unicode_minus'] = False # 解决负号显示为方块的问题
from wordcloud import WordCloud
from app import get_db_connection

# 创建报表目录
os.makedirs('reports', exist_ok=True)

# 获取数据库数据
def fetch_data():
    conn = get_db_connection()
    df = conn.execute("SELECT 关键词, 简介, 详解, click FROM knowledge_base").fetchdf()
    conn.close()
    return df

# 生成可视化图表
def generate_visualizations(df):
    # PyGWalker交互式分析
    walker = pyg.walk(df, spec="./chart_config.json", dark="media")
    
    # 关键词分布饼图
    keyword_counts = df['关键词'].value_counts()
    plt.figure(figsize=(10, 8))
    keyword_counts.plot.pie(autopct='%1.1f%%')
    plt.savefig('reports/keyword_distribution.png')
    
    # 数据完整性统计
    completeness = df.notnull().mean()*100
    plt.figure(figsize=(10,6))
    completeness.plot(kind='bar')
    plt.title('数据完整性统计')
    plt.ylabel('完整率 (%)')
    plt.savefig('reports/data_completeness.png')
    
    # 词云生成
    text = ' '.join(df['详解'].dropna())
    wordcloud = WordCloud(font_path='msyh.ttc', width=800, height=400).generate(text)
    plt.figure(figsize=(12,6))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.savefig('reports/word_cloud.png')

# 生成HTML报表
def generate_html_report():
    df = fetch_data()
    walker = pyg.walk(df, spec="../chart_config.json")
    # 使用 pygwalker 的 to_html() 方法生成 HTML
    html = str(walker)
    with open('reports/analysis_report.html', 'w', encoding='utf-8') as f:
        f.write(html)

if __name__ == '__main__':
    df = fetch_data()
    generate_visualizations(df)
    generate_html_report()
    print("可视化报表已生成至reports目录！")