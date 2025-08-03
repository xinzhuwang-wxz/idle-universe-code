"""
(G)I-DLE Universe 一键部署脚本
自动处理数据同步和部署配置
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.data_sync import DataSync

def create_deployment_package():
    """创建部署包"""
    print("🚀 开始创建部署包...")
    
    # 创建临时部署目录
    deploy_dir = "deploy_temp"
    if os.path.exists(deploy_dir):
        shutil.rmtree(deploy_dir)
    os.makedirs(deploy_dir)
    
    # 复制必要文件
    files_to_copy = [
        "serve/streamlit_app.py",
        "utils/",
        "llm/",
        "qa_chain/",
        "database/",
        "requirements.txt",
        "README.md",
        ".streamlit/",
        "knowledge_db/",
        "vector_db/"
    ]
    
    for item in files_to_copy:
        src = item
        dst = os.path.join(deploy_dir, item)
        
        if os.path.isfile(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
        elif os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
    
    print("✅ 部署包创建完成")
    return deploy_dir

def sync_data_package():
    """同步数据包"""
    print("📦 开始同步数据包...")
    
    try:
        # 创建数据同步工具实例
        data_sync = DataSync()
        
        # 创建数据包（包含向量数据库）
        package_path = data_sync.create_data_package(include_vector_db=True)
        
        print(f"✅ 数据包同步完成: {package_path}")
        return True
        
    except Exception as e:
        print(f"❌ 数据包同步失败: {e}")
        return False

def create_streamlit_config():
    """创建 Streamlit 配置文件"""
    config_content = """
[global]
developmentMode = false

[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#FF6B9D"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
"""
    
    config_dir = ".streamlit"
    os.makedirs(config_dir, exist_ok=True)
    
    with open(os.path.join(config_dir, "config.toml"), "w") as f:
        f.write(config_content)
    
    print("✅ Streamlit 配置创建完成")

def create_procfile():
    """创建 Procfile (用于 Railway 等平台)"""
    procfile_content = "web: streamlit run serve/streamlit_app.py --server.port $PORT --server.address 0.0.0.0"
    
    with open("Procfile", "w") as f:
        f.write(procfile_content)
    
    print("✅ Procfile 创建完成")

def create_runtime_txt():
    """创建 runtime.txt (指定 Python 版本)"""
    runtime_content = "python-3.9.18"
    
    with open("runtime.txt", "w") as f:
        f.write(runtime_content)
    
    print("✅ runtime.txt 创建完成")

def create_app_json():
    """创建 app.json (用于 Railway)"""
    app_json = {
        "name": "idle-universe",
        "description": "(G)I-DLE Universe 智能问答系统",
        "repository": "https://github.com/your-username/idle-universe",
        "keywords": ["python", "streamlit", "ai", "chatbot", "g-idle"],
        "env": {
            "ZHIPUAI_API_KEY": {
                "description": "智谱AI API Key",
                "required": False
            },
            "OPENAI_API_KEY": {
                "description": "OpenAI API Key",
                "required": False
            }
        },
        "formation": {
            "web": {
                "quantity": 1,
                "size": "basic"
            }
        }
    }
    
    import json
    with open("app.json", "w") as f:
        json.dump(app_json, f, indent=2)
    
    print("✅ app.json 创建完成")

def create_deployment_instructions():
    """创建部署说明"""
    instructions = """
# (G)I-DLE Universe 线上部署说明

## 🚀 快速部署

### 1. Streamlit Cloud (推荐)
1. 访问 https://share.streamlit.io/
2. 连接你的 GitHub 仓库
3. 设置入口文件: `serve/streamlit_app.py`
4. 添加环境变量 (可选):
   - ZHIPUAI_API_KEY
   - OPENAI_API_KEY

### 2. Railway
1. 访问 https://railway.app/
2. 导入 GitHub 仓库
3. 自动部署，无需额外配置

### 3. Render
1. 访问 https://render.com/
2. 创建新的 Web Service
3. 连接 GitHub 仓库
4. 设置构建命令: `pip install -r requirements.txt`
5. 设置启动命令: `streamlit run serve/streamlit_app.py`

## 📦 数据包说明

本项目包含:
- 知识库数据 (knowledge_db/)
- 向量数据库 (vector_db/)
- 完整的应用代码

用户无需配置数据，可直接使用。

## 🔧 环境变量

可选的环境变量:
- ZHIPUAI_API_KEY: 智谱AI API Key
- OPENAI_API_KEY: OpenAI API Key

如果不设置，用户需要在界面中手动输入。

## 📝 注意事项

1. 首次启动可能需要几分钟来加载模型
2. 向量数据库文件较大，确保平台支持
3. 建议使用 Git LFS 管理大文件
4. 定期更新知识库数据

## 🎯 功能特性

- ✅ 智能问答 (G)I-DLE 相关问题
- ✅ 多语言支持
- ✅ 流式回答
- ✅ 对话历史
- ✅ 隐私保护 (用户输入 API Key)
- ✅ 响应式界面
"""
    
    with open("DEPLOYMENT.md", "w", encoding="utf-8") as f:
        f.write(instructions)
    
    print("✅ 部署说明创建完成")

def main():
    """主函数"""
    print("🎵 (G)I-DLE Universe 部署工具")
    print("=" * 50)
    
    try:
        # 同步数据包
        if not sync_data_package():
            print("⚠️  数据包同步失败，继续创建部署包...")
        
        # 创建部署包
        deploy_dir = create_deployment_package()
        
        # 切换到部署目录
        os.chdir(deploy_dir)
        
        # 创建配置文件
        create_streamlit_config()
        create_procfile()
        create_runtime_txt()
        create_app_json()
        create_deployment_instructions()
        
        print("\n🎉 部署包准备完成！")
        print(f"📁 部署目录: {deploy_dir}")
        print("📦 数据包已同步到 data_package/ 目录")
        print("\n📋 下一步:")
        print("1. 将 deploy_temp 目录推送到 GitHub")
        print("2. 在 Streamlit Cloud 等平台连接仓库")
        print("3. 设置环境变量 (可选)")
        print("4. 部署完成！")
        
    except Exception as e:
        print(f"❌ 部署包创建失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main() 