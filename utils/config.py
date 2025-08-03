"""
(G)I-DLE Universe 配置文件
"""
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

@dataclass
class CrawlerConfig:
    """爬虫配置"""
    # 目标网站配置
    websites = {
        "wikipedia": {
            "url": "https://en.wikipedia.org/wiki/I-dle",
            "type": "wikipedia",
            "enabled": True
        },
        "kpop_wiki": {
            "url": "https://kpop.fandom.com/wiki/I-dle",
            "type": "wiki",
            "enabled": True
        },
        "soompi": {
            "url": "https://www.soompi.com/tag/i-dle/",
            "type": "news",
            "enabled": True
        },
        "allkpop": {
            "url": "https://www.allkpop.com/tag/idle",
            "type": "news",
            "enabled": True
        },
        "reddit": {
            "url": "https://www.reddit.com/r/GIDLE/",
            "type": "community",
            "enabled": True
        }
    }
    
    # 爬取设置
    start_year: int = 2022
    end_year: int = 2025
    max_memory: str = "2GB"
    max_pages_per_site: int = 50
    delay_between_requests: float = 1.0
    
    # 数据存储
    data_dir: str = "knowledge_db"
    raw_data_dir: str = "knowledge_db/raw"
    processed_data_dir: str = "knowledge_db/processed"

@dataclass
class LLMConfig:
    """大语言模型配置"""
    # 支持的模型
    supported_models = {
        "zhipu": ["chatglm_pro", "chatglm_std", "chatglm_lite"],
        "openai": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
    }
    
    # 默认模型
    default_model: str = "chatglm_std"
    default_provider: str = "zhipu"
    
    # API 配置
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    zhipuai_api_key: Optional[str] = os.getenv("ZHIPUAI_API_KEY")
    
    # 模型参数
    temperature: float = 0.1
    max_tokens: int = 2048

@dataclass
class EmbeddingConfig:
    """向量化配置"""
    # 支持的 embedding 模型
    supported_embeddings = {
        "openai": "text-embedding-ada-002",
        "zhipuai": "embedding-2",
        "m3e": "moka-ai/m3e-base"
    }
    
    default_embedding: str = "m3e"
    chunk_size: int = 500
    chunk_overlap: int = 150

@dataclass
class DatabaseConfig:
    """数据库配置"""
    vector_db_path: str = "vector_db/faiss"
    knowledge_db_path: str = "knowledge_db"
    persist_directory: str = "vector_db/faiss"

@dataclass
class QaChainConfig:
    """问答链配置"""
    # 检索设置
    top_k: int = 4
    search_type: str = "similarity"
    
    # 提示模板
    default_template = """你是一个专业的 (G)I-DLE 知识助手。请基于以下上下文回答用户的问题。
    
    上下文: {context}
    问题: {question}
    
    请用中文回答，如果不知道答案就说不知道。回答要准确、简洁、友好。
    
    回答:"""
    
    # 对话历史设置
    max_history_length: int = 5

@dataclass
class DeployConfig:
    """部署配置"""
    # Gradio 配置
    gradio_port: int = 7860
    gradio_share: bool = False
    
    # Streamlit 配置
    streamlit_port: int = 8501
    
    # API 保护设置
    session_timeout: int = 3600  # 1小时
    enable_api_input: bool = True

@dataclass
class AppConfig:
    """应用配置"""
    app_name: str = "(G)I-DLE Universe"
    app_description: str = "智能 (G)I-DLE 问答系统"
    app_version: str = "1.0.0"
    
    # 界面设置
    theme_color: str = "#FF6B9D"  # (G)I-DLE 粉色
    avatar_path: str = "assets/avatar.png"
    logo_path: str = "assets/logo.png"

class Config:
    """主配置类"""
    def __init__(self):
        self.crawler = CrawlerConfig()
        self.llm = LLMConfig()
        self.embedding = EmbeddingConfig()
        self.database = DatabaseConfig()
        self.qa_chain = QaChainConfig()
        self.deploy = DeployConfig()
        self.app = AppConfig()
    
    def get_model_config(self, provider: str, model: str) -> Dict:
        """获取模型配置"""
        if provider == "zhipu":
            return {
                "provider": "zhipu",
                "model": model,
                "api_key": self.llm.zhipuai_api_key
            }
        elif provider == "openai":
            return {
                "provider": "openai", 
                "model": model,
                "api_key": self.llm.openai_api_key
            }
        else:
            raise ValueError(f"不支持的模型提供商: {provider}")
    
    def get_embedding_config(self, embedding_type: str) -> Dict:
        """获取向量化配置"""
        return {
            "type": embedding_type,
            "model": self.embedding.supported_embeddings.get(embedding_type),
            "chunk_size": self.embedding.chunk_size,
            "chunk_overlap": self.embedding.chunk_overlap
        }
    
    def validate_config(self) -> bool:
        """验证配置"""
        # 检查必要的 API key
        if not self.llm.zhipuai_api_key and not self.llm.openai_api_key:
            print("警告: 未设置任何 API key")
            return False
        
        # 检查目录是否存在
        required_dirs = [
            self.crawler.data_dir,
            self.database.vector_db_path,
            self.database.knowledge_db_path
        ]
        
        for dir_path in required_dirs:
            os.makedirs(dir_path, exist_ok=True)
        
        return True

# 全局配置实例
config = Config()