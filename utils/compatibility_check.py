"""
兼容性检查工具
检测环境并选择合适的向量数据库
"""
import os
import sys
import sqlite3
import logging
from typing import Dict, Any

def check_sqlite_version() -> Dict[str, Any]:
    """检查 SQLite 版本"""
    try:
        version = sqlite3.sqlite_version
        version_tuple = tuple(map(int, version.split('.')))
        required_version = (3, 35, 0)
        
        is_compatible = version_tuple >= required_version
        
        return {
            "version": version,
            "version_tuple": version_tuple,
            "required_version": required_version,
            "is_compatible": is_compatible,
            "can_use_chroma": is_compatible
        }
    except Exception as e:
        return {
            "error": str(e),
            "is_compatible": False,
            "can_use_chroma": False
        }

def check_available_vectorstores() -> Dict[str, bool]:
    """检查可用的向量数据库"""
    results = {}
    
    # Chroma 已移除，不再检查
    results["chroma"] = False
    
    # 检查 FAISS
    try:
        import faiss
        results["faiss"] = True
    except ImportError:
        results["faiss"] = False
    
    # 检查 SQLite 兼容性
    sqlite_info = check_sqlite_version()
    results["sqlite_compatible"] = sqlite_info.get("is_compatible", False)
    
    return results

def get_recommended_vectorstore() -> str:
    """获取推荐的向量数据库"""
    available = check_available_vectorstores()
    sqlite_info = check_sqlite_version()
    
    # 推荐 FAISS（Chroma 已移除）
    if available.get("faiss"):
        return "faiss"
    
    # 都不行的话返回 faiss
    return "faiss"

def main():
    """主函数"""
    print("🔍 环境兼容性检查")
    print("=" * 50)
    
    # 检查 SQLite 版本
    sqlite_info = check_sqlite_version()
    print(f"📊 SQLite 版本: {sqlite_info.get('version', 'Unknown')}")
    print(f"✅ 兼容性: {'是' if sqlite_info.get('is_compatible') else '否'}")
    
    # 检查可用向量数据库
    available = check_available_vectorstores()
    print(f"\n📦 可用向量数据库:")
    print(f"  - FAISS: {'✅' if available.get('faiss') else '❌'}")
    
    # 推荐
    recommended = get_recommended_vectorstore()
    print(f"\n🎯 推荐使用: {recommended.upper()}")
    
    if recommended == "faiss":
        print("💡 提示: 将使用 FAISS 作为主要方案")
    
    return recommended

if __name__ == "__main__":
    main() 