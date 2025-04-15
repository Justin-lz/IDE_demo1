from flask import Flask, render_template, request, jsonify
import duckdb
import os
from dotenv import load_dotenv
import requests
import pandas as pd
from openai import OpenAI

load_dotenv()

app = Flask(__name__)

# 初始化数据库连接
def get_db_connection():
    return duckdb.connect(database='knowledge_db.duckdb')

# 大模型API调用函数
def get_ai_explanation(keyword):
    client = OpenAI(
        api_key=os.getenv('DASHSCOPE_API_KEY'),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    
    try:
        completion = client.chat.completions.create(
            model="qwen-turbo",
            messages=[
                {'role': 'system', 'content': '你是一个对智能数据工程的相关知识了如指掌的教师.'},
                {'role': 'user', 'content': f"请用300字以内的一段文字，简明扼要地解释'{keyword}'在智能数据工程中的技术原理和显著特点,\
                注：请你使用简洁精练的一段文字来回答，不要超过300字。"},
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"API调用失败：{str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    keyword = request.args.get('q', '').strip()
    if not keyword:
        return jsonify([])

    conn = get_db_connection()
    result = conn.execute("""
        SELECT 关键词, 简介, 详解 
        FROM knowledge_base 
        WHERE 关键词 ILIKE ? 
        ORDER BY jaro_winkler_similarity(关键词, ?) DESC 
        LIMIT 1
    """, [f"%{keyword}%", keyword]).fetchdf()
    conn.close()

    if not result.empty:
        record = result.iloc[0]
        # 更新点击量
        conn = get_db_connection()
        conn.execute("UPDATE knowledge_base SET click = click + 1 WHERE 关键词 = ?", [record['关键词']])
        conn.close()
        # print(f"[DEBUG] 从数据库获取的记录: {record.to_dict()}")  # 调试日志
        if pd.isnull(record['详解']) or str(record['详解']).strip() in ('', 'nan', 'None'):
            # 获取AI解释并更新数据库
            ai_explanation = get_ai_explanation(record['关键词'])
            print(f"[DEBUG] AI解释结果: {ai_explanation}")  # 调试日志
            conn = get_db_connection()
            conn.execute(
                "UPDATE knowledge_base SET 详解 = ? WHERE 关键词 = ?",
                [ai_explanation or '暂无技术详解', record['关键词']]
            )
            conn.close()
            record['详解'] = ai_explanation or '等待技术详解生成中...'
        
        return jsonify({
            'keyword': record['关键词'],
            'summary': record['简介'] or '暂无简介',
            'detail': record['详解']
        })
    
    return jsonify({'error': 'not_found'})

@app.route('/suggest')
def suggest_keywords():
    keyword = request.args.get('q', '').strip()
    if not keyword:
        return jsonify([])

    conn = get_db_connection()
    results = conn.execute("""
        SELECT 关键词 
        FROM knowledge_base 
        WHERE 关键词 ILIKE ? 
        ORDER BY jaro_winkler_similarity(关键词, ?) DESC
        LIMIT 5
    """, [f"%{keyword}%", keyword]).fetchdf()
    conn.close()

    return jsonify([row['关键词'] for _, row in results.iterrows()])


@app.route('/wordcloud')
def wordcloud():
    conn = get_db_connection()
    top_keywords = conn.execute("SELECT 关键词, click FROM knowledge_base ORDER BY click DESC LIMIT 7").fetchall()
    conn.close()
    return jsonify([{'name': row[0], 'value': row[1]} for row in top_keywords])

@app.route('/test-api')
def test_api_key():
    api_key = os.getenv('DASHSCOPE_API_KEY')
    if not api_key or 'sk-' not in api_key:
        return jsonify({'status': 'error', 'message': '无效的API密钥格式'})
    
    try:
        test_response = requests.post(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "qwen-turbo",
                "messages": [{"role": "user", "content": "test"}]
            },
            timeout=5
        )
        return jsonify({
            'status': 'success' if test_response.status_code == 200 else 'error',
            'status_code': test_response.status_code
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)


# 在文件顶部添加新的导入
from openai import OpenAI