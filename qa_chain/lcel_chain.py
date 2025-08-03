"""
(G)I-DLE Universe LCEL 问答链模块
使用 LangChain Expression Language 构建问答链
"""
import os
import sys
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# 设置 FAISS 安全反序列化环境变量
os.environ['FAISS_ALLOW_DANGEROUS_DESERIALIZATION'] = 'True'

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import config
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableBranch
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

class LCELQaChain:
    """基于 LCEL 的问答链"""
    
    def __init__(self, 
                 model_provider: str = "zhipu",
                 model_name: str = None,
                 embedding_type: str = "m3e",
                 top_k: int = 4,
                 temperature: float = 0.1):
        
        self.model_provider = model_provider
        self.model_name = model_name or config.llm.default_model
        self.embedding_type = embedding_type
        self.top_k = top_k
        self.temperature = temperature
        
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self._init_llm()
        self._init_embedding()
        self._init_vector_db()
        self._init_prompts()
        self._build_chain()
    
    def _init_llm(self):
        """初始化 LLM"""
        if self.model_provider == "zhipu":
            from llm.zhipu_llm import ZhipuChatModel
            self.llm = ZhipuChatModel(model=self.model_name)
        elif self.model_provider == "openai":
            from llm.openai_llm import OpenAILLM
            self.llm = OpenAILLM(model=self.model_name)
        else:
            raise ValueError(f"不支持的模型提供商: {self.model_provider}")
    
    def _init_embedding(self):
        """初始化向量化模型"""
        if self.embedding_type == "openai":
            self.embedding = OpenAIEmbeddings()
        elif self.embedding_type == "m3e":
            from database.create_db import M3EEmbeddings
            self.embedding = M3EEmbeddings('moka-ai/m3e-base')
        else:
            raise ValueError(f"不支持的向量化类型: {self.embedding_type}")
    
    def _init_vector_db(self):
        """初始化向量数据库"""
        try:
            # 设置 FAISS 安全反序列化
            import faiss
            if hasattr(faiss, 'set_allow_dangerous_deserialization'):
                faiss.set_allow_dangerous_deserialization(True)
            
            # 直接使用 FAISS（避免 SQLite 兼容性问题）
            faiss_path = config.database.vector_db_path.replace("chroma", "faiss")
            
            if os.path.exists(faiss_path):
                # 加载现有的 FAISS 数据库
                self.vectordb = FAISS.load_local(faiss_path, self.embedding, allow_dangerous_deserialization=True)
                self.logger.info("成功加载 FAISS 向量数据库")
            else:
                # 创建新的 FAISS 数据库
                self.logger.info("创建新的 FAISS 向量数据库")
                self.vectordb = self._create_faiss_vector_db()
            
            # 创建检索器
            self.retriever = self.vectordb.as_retriever(
                search_type="similarity",
                search_kwargs={'k': self.top_k}
            )
            
        except Exception as e:
            self.logger.error(f"向量数据库初始化失败: {e}")
            raise
    
    def _init_prompts(self):
        """初始化提示模板"""
        # 问题重写提示 (用于对话历史)
        self.condense_question_prompt = ChatPromptTemplate.from_template(
            """基于以下对话历史和当前问题，重写当前问题以使其独立。
            如果对话历史为空，则直接返回当前问题。
            
            对话历史:
            {chat_history}
            
            当前问题: {question}
            
            重写后的问题:"""
        )
        
        # 问答提示
        self.qa_prompt = ChatPromptTemplate.from_template(
            config.qa_chain.default_template
        )
    
    def _build_chain(self):
        """构建 LCEL 链"""
        # 文档组合函数
        def combine_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        # 构建完整的问答链
        self.qa_chain = (
            RunnablePassthrough().assign(
                context=self.retriever | combine_docs
            )
            .assign(
                answer=self.qa_prompt | self.llm | StrOutputParser()
            )
        )
    
    def answer(self, question: str, chat_history: List = None) -> Dict[str, Any]:
        """回答问题"""
        if not question or len(question.strip()) == 0:
            return {"answer": "", "context": "", "sources": []}
        
        try:
            # 处理历史记录
            enhanced_question = self._enhance_question_with_history(question, chat_history)
            
            # 准备输入
            inputs = {
                "question": enhanced_question
            }
            
            # 调用链
            result = self.qa_chain.invoke(inputs)
            
            # 获取源文档
            docs = self.retriever.get_relevant_documents(enhanced_question)
            sources = [doc.metadata.get('source', 'Unknown') for doc in docs]
            
            return {
                "answer": result.get("answer", ""),
                "context": result.get("context", ""),
                "sources": sources
            }
            
        except Exception as e:
            self.logger.error(f"问答失败: {e}")
            return {
                "answer": f"抱歉，处理您的问题时出现了错误: {e}",
                "context": "",
                "sources": []
            }
    
    def _create_faiss_vector_db(self):
        """直接创建 FAISS 向量数据库"""
        try:
            from database.create_db import DatabaseManager
            db_manager = DatabaseManager()
            
            # 加载文档
            documents = db_manager.load_documents()
            if not documents:
                raise Exception("没有找到任何文档")
            
            # 分割文档
            split_docs = db_manager.split_documents(documents)
            
            # 直接创建 FAISS 数据库
            vectordb = FAISS.from_documents(
                documents=split_docs,
                embedding=self.embedding
            )
            
            # 保存到 FAISS 路径
            faiss_path = config.database.vector_db_path.replace("chroma", "faiss")
            os.makedirs(os.path.dirname(faiss_path), exist_ok=True)
            vectordb.save_local(faiss_path)
            
            self.logger.info(f"FAISS 向量数据库创建完成: {faiss_path}")
            return vectordb
            
        except Exception as e:
            self.logger.error(f"创建 FAISS 向量数据库失败: {e}")
            raise
    
    def _enhance_question_with_history(self, question: str, chat_history: List = None) -> str:
        """使用历史记录增强问题"""
        if not chat_history:
            return question
        
        # 构建历史记录文本
        history_text = ""
        for i, (user_msg, ai_msg) in enumerate(chat_history[-3:], 1):  # 只使用最近3轮对话
            history_text += f"第{i}轮对话:\n用户: {user_msg}\n助手: {ai_msg}\n\n"
        
        # 增强问题
        enhanced_question = f"""基于以下对话历史，请回答当前问题：

{history_text}
当前问题: {question}

请基于历史对话的上下文，准确回答当前问题。"""
        
        return enhanced_question
    
    def answer_stream(self, question: str, chat_history: List = None):
        """流式回答问题"""
        if not question or len(question.strip()) == 0:
            yield ""
            return
        
        try:
            # 处理历史记录
            enhanced_question = self._enhance_question_with_history(question, chat_history)
            
            # 获取相关文档
            docs = self.retriever.get_relevant_documents(enhanced_question)
            context = "\n\n".join(doc.page_content for doc in docs)
            
            # 构建提示
            prompt = self.qa_prompt.format(context=context, question=enhanced_question)
            
            # 使用 LLM 的流式生成
            if hasattr(self.llm, 'zhipu_llm'):
                # 智谱AI 流式生成
                for chunk in self.llm.zhipu_llm.generate_stream(prompt, temperature=self.temperature):
                    yield chunk
            else:
                # 其他模型的流式生成
                for chunk in self.llm.stream(prompt):
                    if hasattr(chunk, 'content'):
                        yield chunk.content
                    else:
                        yield str(chunk)
                    
        except Exception as e:
            self.logger.error(f"流式问答失败: {e}")
            yield f"抱歉，处理您的问题时出现了错误: {e}"
    
    def get_chain_info(self) -> Dict[str, Any]:
        """获取链信息"""
        return {
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "embedding_type": self.embedding_type,
            "top_k": self.top_k,
            "temperature": self.temperature,
            "vector_db_path": config.database.vector_db_path
        }

class QaChainManager:
    """问答链管理器"""
    
    def __init__(self):
        self.chains = {}
        self.logger = logging.getLogger(__name__)
    
    def get_chain(self, 
                  model_provider: str = "zhipu",
                  model_name: str = None,
                  embedding_type: str = "m3e") -> LCELQaChain:
        """获取或创建问答链"""
        key = f"{model_provider}_{model_name}_{embedding_type}"
        
        if key not in self.chains:
            self.logger.info(f"创建新的问答链: {key}")
            self.chains[key] = LCELQaChain(
                model_provider=model_provider,
                model_name=model_name,
                embedding_type=embedding_type
            )
        
        return self.chains[key]
    
    def clear_chains(self):
        """清除所有链"""
        self.chains.clear()
        self.logger.info("已清除所有问答链")

def main():
    """测试问答链"""
    import argparse
    
    parser = argparse.ArgumentParser(description='测试 LCEL 问答链')
    parser.add_argument('--model', type=str, default='zhipu', choices=['zhipu', 'openai'], help='模型提供商')
    parser.add_argument('--question', type=str, default='什么是(G)I-DLE?', help='测试问题')
    
    args = parser.parse_args()
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # 创建问答链管理器
        manager = QaChainManager()
        
        # 获取问答链
        chain = manager.get_chain(model_provider=args.model)
        
        print(f"使用模型: {args.model}")
        print(f"测试问题: {args.question}")
        print("-" * 50)
        
        # 测试问答
        result = chain.answer(args.question)
        print(f"回答: {result['answer']}")
        print(f"来源: {result['sources']}")
        
        print("-" * 50)
        
        # 测试流式问答
        print("流式回答:")
        for chunk in chain.answer_stream(args.question):
            print(chunk, end='', flush=True)
        print()
        
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    main() 