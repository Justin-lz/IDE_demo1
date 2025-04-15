import sys
import os
import duckdb
from app import get_db_connection

def add_knowledge(keyword, intro, detail):
    """添加新的知识条目"""
    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT INTO knowledge_base (关键词, 简介, 详解)
            VALUES (?, ?, ?)
        """, (keyword, intro, detail))
        conn.commit()
        print(f"成功添加知识条目：{keyword}")
    except Exception as e:
        print(f"添加失败：{str(e)}")
    finally:
        conn.close()

def update_knowledge(keyword, intro=None, detail=None):
    """更新现有知识条目"""
    conn = get_db_connection()
    try:
        update_parts = []
        params = []
        if intro is not None:
            update_parts.append("简介 = ?")
            params.append(intro)
        if detail is not None:
            update_parts.append("详解 = ?")
            params.append(detail)
        
        if update_parts:
            params.append(keyword)
            sql = f"""
                UPDATE knowledge_base 
                SET {', '.join(update_parts)}
                WHERE 关键词 = ?
            """
            conn.execute(sql, params)
            conn.commit()
            print(f"成功更新知识条目：{keyword}")
        
    except Exception as e:
        print(f"更新失败：{str(e)}")
    finally:
        conn.close()

def delete_knowledge(keyword):
    """删除知识条目"""
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM knowledge_base WHERE 关键词 = ?", (keyword,))
        conn.commit()
        print(f"成功删除知识条目：{keyword}")
    except Exception as e:
        print(f"删除失败：{str(e)}")
    finally:
        conn.close()

def search_knowledge(keyword=None):
    """搜索知识条目"""
    conn = get_db_connection()
    try:
        if keyword:
            sql = "SELECT * FROM knowledge_base WHERE 关键词 LIKE ?"
            results = conn.execute(sql, (f"%{keyword}%",)).fetchall()
            
            # 更新点击量
            if results:
                conn.execute("UPDATE knowledge_base SET click = click + 1 WHERE 关键词 LIKE ?", (f"%{keyword}%",))
                conn.commit()
        else:
            results = conn.execute("SELECT * FROM knowledge_base").fetchall()
        
        for row in results:
            print("\n" + "="*50)
            print(f"关键词：{row[0]}")
            print(f"简介：{row[1]}")
            print(f"详解：{row[2]}")
            
    except Exception as e:
        print(f"查询失败：{str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    while True:
        print("\n=== 知识库管理系统 ===")
        print("1. 添加知识")
        print("2. 更新知识")
        print("3. 删除知识")
        print("4. 搜索知识")
        print("5. 退出")
        
        choice = input("\n请选择操作 (1-5): ")
        
        if choice == "1":
            keyword = input("请输入关键词：")
            intro = input("请输入简介：")
            detail = input("请输入详解：")
            add_knowledge(keyword, intro, detail)
            
        elif choice == "2":
            keyword = input("请输入要更新的关键词：")
            intro = input("请输入新的简介（直接回车保持不变）：")
            detail = input("请输入新的详解（直接回车保持不变）：")
            update_knowledge(keyword, 
                           intro if intro else None, 
                           detail if detail else None)
            
        elif choice == "3":
            keyword = input("请输入要删除的关键词：")
            confirm = input("确认删除？(y/n): ")
            if confirm.lower() == 'y':
                delete_knowledge(keyword)
                
        elif choice == "4":
            keyword = input("请输入搜索关键词（直接回车显示所有）：")
            search_knowledge(keyword if keyword else None)
            
        elif choice == "5":
            print("感谢使用！")
            break