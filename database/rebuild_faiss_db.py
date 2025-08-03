"""
重新构建纯 FAISS 向量数据库
"""
import os
import shutil
import logging
from create_db import DatabaseManager

def rebuild_faiss_database():
    """重新构建 FAISS 向量数据库"""
    print("🔄 开始重新构建 FAISS 向量数据库...")
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # 获取项目根目录（database 的上级目录）
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        vector_db_path = os.path.join(project_root, "vector_db")
        
        print(f"📁 项目根目录: {project_root}")
        print(f"📁 向量数据库路径: {vector_db_path}")
        
        # 删除现有的 vector_db 目录
        if os.path.exists(vector_db_path):
            print("🗑️  删除现有的 vector_db 目录...")
            shutil.rmtree(vector_db_path)
        
        # 创建新的 vector_db 目录
        os.makedirs(vector_db_path, exist_ok=True)
        print("📁 创建新的 vector_db 目录")
        
        # 创建 FAISS 数据库
        print("🔧 创建 FAISS 向量数据库...")
        
        # 修改工作目录到项目根目录
        original_cwd = os.getcwd()
        os.chdir(project_root)
        print(f"📁 切换到项目根目录: {project_root}")
        
        db_manager = DatabaseManager()
        vectordb = db_manager.create_vector_db("m3e")
        
        # 恢复原始工作目录
        os.chdir(original_cwd)
        
        if vectordb:
            print("✅ FAISS 向量数据库创建成功！")
            
            # 检查生成的文件
            faiss_path = os.path.join(vector_db_path, "faiss")
            if os.path.exists(faiss_path):
                files = os.listdir(faiss_path)
                print(f"📦 FAISS 文件: {files}")
            else:
                print("⚠️  FAISS 目录不存在")
                
        else:
            print("❌ FAISS 向量数据库创建失败")
            return False
            
    except Exception as e:
        print(f"❌ 重建失败: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("🎵 (G)I-DLE Universe - FAISS 数据库重建工具")
    print("=" * 50)
    
    success = rebuild_faiss_database()
    
    if success:
        print("\n🎉 FAISS 向量数据库重建完成！")
        print("📋 下一步:")
        print("1. 运行 python deploy.py 重新创建部署包")
        print("2. 推送更新到 GitHub")
        print("3. 等待 Streamlit Cloud 重新部署")
    else:
        print("\n❌ FAISS 向量数据库重建失败")

if __name__ == "__main__":
    main() 