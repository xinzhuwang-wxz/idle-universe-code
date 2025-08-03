"""
数据同步工具
用于将本地数据打包并准备上传到线上部署平台
"""
import os
import json
import shutil
import zipfile
from datetime import datetime
from typing import Dict, List

class DataSync:
    """数据同步工具类"""
    
    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.project_root, "data_package")
        
        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)
    
    def create_data_package(self, include_vector_db: bool = True) -> str:
        """创建数据包"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        package_name = f"idle_universe_data_{timestamp}"
        package_path = os.path.join(self.data_dir, package_name)
        
        # 创建包目录
        os.makedirs(package_path, exist_ok=True)
        
        # 复制知识库数据
        self._copy_knowledge_db(package_path)
        
        # 复制向量数据库（可选）
        if include_vector_db:
            self._copy_vector_db(package_path)
        
        # 创建数据包信息
        self._create_package_info(package_path, include_vector_db)
        
        # 创建压缩包
        zip_path = self._create_zip_package(package_path, package_name)
        
        print(f"✅ 数据包创建完成: {zip_path}")
        return zip_path
    
    def _copy_knowledge_db(self, package_path: str):
        """复制知识库数据"""
        source_dir = os.path.join(self.project_root, "knowledge_db")
        target_dir = os.path.join(package_path, "knowledge_db")
        
        if os.path.exists(source_dir):
            shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
            print(f"📁 已复制知识库数据到: {target_dir}")
        else:
            print("⚠️  知识库目录不存在")
    
    def _copy_vector_db(self, package_path: str):
        """复制向量数据库"""
        source_dir = os.path.join(self.project_root, "vector_db")
        target_dir = os.path.join(package_path, "vector_db")
        
        if os.path.exists(source_dir):
            shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
            print(f"📁 已复制向量数据库到: {target_dir}")
        else:
            print("⚠️  向量数据库目录不存在")
    
    def _create_package_info(self, package_path: str, include_vector_db: bool):
        """创建数据包信息文件"""
        info = {
            "package_created": datetime.now().isoformat(),
            "includes_vector_db": include_vector_db,
            "data_sources": {
                "knowledge_db": "processed/translated_results_20250804_001500.json",
                "vector_db": "chroma/" if include_vector_db else None
            },
            "deployment_instructions": [
                "1. 解压数据包到项目根目录",
                "2. 确保 knowledge_db 和 vector_db 目录在正确位置",
                "3. 启动应用即可使用"
            ]
        }
        
        info_path = os.path.join(package_path, "package_info.json")
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        
        print(f"📄 已创建数据包信息: {info_path}")
    
    def _create_zip_package(self, package_path: str, package_name: str) -> str:
        """创建压缩包"""
        zip_path = f"{package_path}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(package_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, package_path)
                    zipf.write(file_path, arcname)
        
        # 清理临时目录
        shutil.rmtree(package_path)
        
        return zip_path
    
    def get_deployment_guide(self) -> str:
        """获取部署指南"""
        guide = """
# (G)I-DLE Universe 线上部署指南

## 1. 平台选择

### Streamlit Cloud (推荐)
- 免费额度：每月 750 小时
- 自动部署：连接 GitHub 仓库
- 支持：Python 3.9+

### Railway
- 免费额度：每月 $5
- 简单部署：上传代码即可
- 支持：多种编程语言

### Render
- 免费额度：每月 750 小时
- 自动部署：连接 Git 仓库
- 支持：Python, Node.js 等

## 2. 数据同步步骤

### 步骤 1: 创建数据包
```bash
python utils/data_sync.py --create-package
```

### 步骤 2: 上传数据包
- 将生成的 zip 文件上传到部署平台
- 或使用 Git LFS 管理大文件

### 步骤 3: 配置环境变量
```env
ZHIPUAI_API_KEY=your_zhipuai_api_key
OPENAI_API_KEY=your_openai_api_key (可选)
```

## 3. 部署配置

### requirements.txt 已包含所有依赖
### 入口文件: serve/streamlit_app.py

## 4. 注意事项
- 向量数据库文件较大，建议使用 Git LFS
- 确保 API 密钥安全存储
- 定期更新知识库数据
        """
        return guide

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='数据同步工具')
    parser.add_argument('--create-package', action='store_true', help='创建数据包')
    parser.add_argument('--include-vector-db', action='store_true', default=True, help='包含向量数据库')
    parser.add_argument('--show-guide', action='store_true', help='显示部署指南')
    
    args = parser.parse_args()
    
    sync = DataSync()
    
    if args.create_package:
        package_path = sync.create_data_package(args.include_vector_db)
        print(f"\n🎉 数据包已创建: {package_path}")
        print("📦 现在可以将此文件上传到部署平台")
    
    if args.show_guide:
        print(sync.get_deployment_guide())

if __name__ == "__main__":
    main() 