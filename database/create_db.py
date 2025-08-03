"""
(G)I-DLE Universe 数据库创建和管理模块
"""
import os
import sys
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime

# 设置 FAISS 安全反序列化环境变量
os.environ['FAISS_ALLOW_DANGEROUS_DESERIALIZATION'] = 'True'

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import config
from langchain.document_loaders import UnstructuredFileLoader, UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from sentence_transformers import SentenceTransformer
from langchain.embeddings.base import Embeddings

class M3EEmbeddings(Embeddings):
    """M3E 嵌入模型包装类"""
    
    def __init__(self, model_name: str = "moka-ai/m3e-base"):
        self.model = SentenceTransformer(model_name)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """嵌入文档列表"""
        return self.model.encode(texts).tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """嵌入查询文本"""
        return self.model.encode([text])[0].tolist()

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.config = config.database
        self.logger = logging.getLogger(__name__)
        
        # 确保目录存在
        os.makedirs(self.config.vector_db_path, exist_ok=True)
        os.makedirs(self.config.knowledge_db_path, exist_ok=True)
    
    def load_documents(self, data_dir: str = None) -> List:
        """加载文档"""
        if data_dir is None:
            data_dir = self.config.knowledge_db_path
        
        documents = []
        
        # 遍历目录中的所有文件
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                file_path = os.path.join(root, file)
                
                # 根据文件类型选择加载器
                if file.endswith('.md'):
                    try:
                        loader = UnstructuredMarkdownLoader(file_path)
                        docs = loader.load()
                        documents.extend(docs)
                        self.logger.info(f"加载 Markdown 文件: {file}")
                    except Exception as e:
                        self.logger.error(f"加载 Markdown 文件失败 {file}: {e}")
                
                elif file.endswith('.txt'):
                    try:
                        loader = UnstructuredFileLoader(file_path)
                        docs = loader.load()
                        documents.extend(docs)
                        self.logger.info(f"加载文本文件: {file}")
                    except Exception as e:
                        self.logger.error(f"加载文本文件失败 {file}: {e}")
                
                elif file.endswith('.json'):
                    try:
                        docs = self._load_json_documents(file_path)
                        documents.extend(docs)
                        self.logger.info(f"加载 JSON 文件: {file}")
                    except Exception as e:
                        self.logger.error(f"加载 JSON 文件失败 {file}: {e}")
        
        self.logger.info(f"总共加载了 {len(documents)} 个文档")
        return documents
    
    def _load_json_documents(self, file_path: str) -> List:
        """加载 JSON 格式的文档"""
        from langchain.schema import Document
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        documents = []
        for item in data:
            # 合并标题和内容
            content = f"标题: {item.get('title', '')}\n\n内容: {item.get('content', '')}"
            
            doc = Document(
                page_content=content,
                metadata={
                    'source': item.get('url', file_path),
                    'title': item.get('title', ''),
                    'timestamp': item.get('timestamp', ''),
                    'language': item.get('language', 'zh')
                }
            )
            documents.append(doc)
        
        return documents
    
    def split_documents(self, documents: List, chunk_size: int = None, chunk_overlap: int = None) -> List:
        """分割文档"""
        chunk_size = chunk_size or config.embedding.chunk_size
        chunk_overlap = chunk_overlap or config.embedding.chunk_overlap
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        
        split_docs = text_splitter.split_documents(documents)
        self.logger.info(f"文档分割完成，共 {len(split_docs)} 个片段")
        
        return split_docs
    
    def create_vector_db(self, embedding_type: str = "m3e", documents: List = None):
        """创建向量数据库"""
        # 初始化向量化模型
        if embedding_type == "openai":
            embedding = OpenAIEmbeddings()
        elif embedding_type == "m3e":
            embedding = M3EEmbeddings('moka-ai/m3e-base')
        else:
            raise ValueError(f"不支持的向量化类型: {embedding_type}")
        
        # 如果没有提供文档，则加载文档
        if documents is None:
            documents = self.load_documents()
        
        if not documents:
            self.logger.warning("没有找到任何文档")
            return None
        
        # 分割文档
        split_docs = self.split_documents(documents)
        
        # 直接使用 FAISS（避免 SQLite 兼容性问题）
        try:
            vectordb = FAISS.from_documents(
                documents=split_docs,
                embedding=embedding
            )
            # 保存 FAISS 索引
            faiss_path = self.config.vector_db_path.replace("chroma", "faiss")
            os.makedirs(os.path.dirname(faiss_path), exist_ok=True)
            vectordb.save_local(faiss_path)
            self.logger.info(f"FAISS 向量数据库创建完成，存储路径: {faiss_path}")
            
        except Exception as e:
            self.logger.error(f"FAISS 创建失败: {e}")
            raise Exception("无法创建向量数据库，请检查环境配置")
        
        return vectordb
    
    def load_vector_db(self, embedding_type: str = "m3e"):
        """加载向量数据库"""
        try:
            # 设置 FAISS 安全反序列化
            import faiss
            if hasattr(faiss, 'set_allow_dangerous_deserialization'):
                faiss.set_allow_dangerous_deserialization(True)
            
            if embedding_type == "openai":
                embedding = OpenAIEmbeddings()
            elif embedding_type == "m3e":
                embedding = M3EEmbeddings('moka-ai/m3e-base')
            else:
                raise ValueError(f"不支持的向量化类型: {embedding_type}")
            
            # 直接加载 FAISS（避免 SQLite 兼容性问题）
            faiss_path = self.config.vector_db_path.replace("chroma", "faiss")
            if os.path.exists(faiss_path):
                vectordb = FAISS.load_local(faiss_path, embedding, allow_dangerous_deserialization=True)
                self.logger.info("FAISS 向量数据库加载成功")
                return vectordb
            else:
                self.logger.warning("未找到 FAISS 向量数据库")
                return None
            
        except Exception as e:
            self.logger.error(f"向量数据库加载失败: {e}")
            return None
    
    def update_vector_db(self, embedding_type: str = "m3e"):
        """更新向量数据库"""
        self.logger.info("开始更新向量数据库")
        
        # 创建新的向量数据库
        vectordb = self.create_vector_db(embedding_type)
        
        if vectordb:
            self.logger.info("向量数据库更新完成")
        else:
            self.logger.error("向量数据库更新失败")
    
    def get_db_info(self) -> Dict:
        """获取数据库信息"""
        # 检查向量数据库是否真正存在（目录存在且不为空）
        vector_db_exists = False
        if os.path.exists(self.config.vector_db_path):
            # 检查目录是否为空
            try:
                files = os.listdir(self.config.vector_db_path)
                vector_db_exists = len(files) > 0
            except:
                vector_db_exists = False
        
        info = {
            "vector_db_path": self.config.vector_db_path,
            "knowledge_db_path": self.config.knowledge_db_path,
            "vector_db_exists": vector_db_exists,
            "knowledge_db_files": []
        }
        
        # 统计知识库文件
        if os.path.exists(self.config.knowledge_db_path):
            for root, dirs, files in os.walk(self.config.knowledge_db_path):
                for file in files:
                    info["knowledge_db_files"].append(os.path.join(root, file))
        
        return info

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='数据库管理工具')
    parser.add_argument('--action', type=str, required=True, 
                       choices=['create', 'load', 'update', 'info'], 
                       help='操作类型')
    parser.add_argument('--embedding', type=str, default='m3e', 
                       choices=['openai', 'm3e'], help='向量化类型')
    parser.add_argument('--data-dir', type=str, help='数据目录路径')
    
    args = parser.parse_args()
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建数据库管理器
    manager = DatabaseManager()
    
    if args.action == 'create':
        print("创建向量数据库...")
        vectordb = manager.create_vector_db(args.embedding)
        if vectordb:
            print("向量数据库创建成功")
        else:
            print("向量数据库创建失败")
    
    elif args.action == 'load':
        print("加载向量数据库...")
        vectordb = manager.load_vector_db(args.embedding)
        if vectordb:
            print("向量数据库加载成功")
        else:
            print("向量数据库加载失败")
    
    elif args.action == 'update':
        print("更新向量数据库...")
        manager.update_vector_db(args.embedding)
    
    elif args.action == 'info':
        print("获取数据库信息...")
        info = manager.get_db_info()
        print(f"向量数据库路径: {info['vector_db_path']}")
        print(f"向量数据库存在: {info['vector_db_exists']}")
        print(f"知识库文件数量: {len(info['knowledge_db_files'])}")
        for file in info['knowledge_db_files'][:5]:  # 只显示前5个文件
            print(f"  - {file}")

if __name__ == "__main__":
    main() 