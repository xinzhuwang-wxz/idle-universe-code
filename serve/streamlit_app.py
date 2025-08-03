"""
(G)I-DLE Universe Streamlit 线上部署模块
支持用户输入 API key，保护隐私
"""
import os
import sys
import streamlit as st
import logging
from typing import List, Dict, Any
import time

# 设置 FAISS 安全反序列化环境变量
os.environ['FAISS_ALLOW_DANGEROUS_DESERIALIZATION'] = 'True'

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import config
from qa_chain.lcel_chain import QaChainManager

class StreamlitApp:
    """Streamlit 应用类"""
    
    def __init__(self):
        self.config = config.deploy
        self.app_config = config.app
        self.logger = logging.getLogger(__name__)
        
        # 初始化会话状态
        self._init_session_state()
    
    def _init_session_state(self):
        """初始化会话状态"""
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        if "qa_manager" not in st.session_state:
            st.session_state.qa_manager = None
        
        if "api_configured" not in st.session_state:
            st.session_state.api_configured = False
        
        if "current_model" not in st.session_state:
            st.session_state.current_model = "zhipu"
        
        if "current_embedding" not in st.session_state:
            st.session_state.current_embedding = "m3e"
    
    def create_interface(self):
        """创建 Streamlit 界面"""
        # 页面配置
        st.set_page_config(
            page_title=self.app_config.app_name,
            page_icon="🎵",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # 自定义 CSS
        st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(90deg, #FF6B9D, #FF8EAB);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            text-align: center;
        }
        .api-section {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
        }
        .chat-container {
            background-color: white;
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 主标题
        st.markdown(f"""
        <div class="main-header">
            <h1>{self.app_config.app_name}</h1>
            <p>{self.app_config.app_description}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 侧边栏 - API 配置
        with st.sidebar:
            st.markdown("### 🔧 API 配置")
            
            # 首先尝试自动配置
            if not st.session_state.api_configured:
                if self._auto_configure_api():
                    st.success("✅ 已自动配置 API（使用内置密钥）")
                else:
                    st.warning("⚠️ 未找到内置 API Key，请手动配置")
            
            # 显示当前配置状态
            if st.session_state.api_configured:
                st.success("✅ API 已配置")
                if st.session_state.current_model == "zhipu":
                    st.info("🤖 使用智谱AI (内置密钥)")
                else:
                    st.info("🤖 使用 OpenAI (内置密钥)")
            else:
                st.warning("⚠️ 请配置 API")
            
            # 手动配置选项（折叠）
            with st.expander("🔧 手动配置 API（可选）"):
                # API 提供商选择
                api_provider = st.selectbox(
                    "选择 API 提供商",
                    ["智谱AI (ZhipuAI)", "OpenAI"],
                    help="选择你要使用的 AI 服务提供商"
                )
                
                # API Key 输入
                api_key = st.text_input(
                    "API Key",
                    type="password",
                    help="请输入你的 API Key（不会保存到服务器）"
                )
                
                # 模型选择
                if api_provider == "智谱AI (ZhipuAI)":
                    model_name = st.selectbox(
                        "选择模型",
                        ["chatglm_std", "chatglm_pro", "chatglm_lite"],
                        help="选择智谱AI的模型"
                    )
                    provider = "zhipu"
                else:
                    model_name = st.selectbox(
                        "选择模型",
                        ["gpt-3.5-turbo", "gpt-4"],
                        help="选择OpenAI的模型"
                    )
                    provider = "openai"
                
                # 向量化模型选择
                embedding_type = st.selectbox(
                    "向量化模型",
                    ["m3e", "openai"],
                    help="选择用于文本向量化的模型"
                )
                
                # 配置按钮
                if st.button("🔗 手动配置 API", type="secondary"):
                    if api_key:
                        self._configure_api(provider, model_name, api_key, embedding_type)
                    else:
                        st.error("请输入 API Key")
            
            # 参数设置
            st.markdown("### ⚙️ 参数设置")
            temperature = st.slider(
                "温度 (创造性)",
                min_value=0.0,
                max_value=1.0,
                value=0.1,
                step=0.1,
                help="控制回答的创造性，值越高越有创意"
            )
            
            top_k = st.slider(
                "检索文档数量",
                min_value=1,
                max_value=10,
                value=4,
                step=1,
                help="从知识库中检索的相关文档数量"
            )
            
            # 清除历史按钮
            if st.button("🗑️ 清除对话历史"):
                st.session_state.messages = []
                st.rerun()
        
        # 主界面
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("### 💬 对话界面")
            
            # 聊天容器
            chat_container = st.container()
            
            with chat_container:
                # 显示对话历史
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])
                
                # 用户输入
                if prompt := st.chat_input("请输入你的问题..."):
                    # 检查 API 是否已配置
                    if not st.session_state.api_configured:
                        st.error("请先在侧边栏配置 API")
                        return
                    
                    # 添加用户消息
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    with st.chat_message("user"):
                        st.markdown(prompt)
                    
                    # 生成回答
                    with st.chat_message("assistant"):
                        message_placeholder = st.empty()
                        full_response = ""
                        
                        # 流式生成回答
                        try:
                            chain = st.session_state.qa_manager.get_chain(
                                model_provider=st.session_state.current_model,
                                embedding_type=st.session_state.current_embedding
                            )
                            
                            # 更新参数
                            chain.temperature = temperature
                            chain.top_k = top_k
                            
                            # 流式生成
                            for chunk in chain.answer_stream(prompt, []):
                                full_response += chunk
                                message_placeholder.markdown(full_response + "▌")
                            
                            message_placeholder.markdown(full_response)
                            
                            # 添加助手消息
                            st.session_state.messages.append({"role": "assistant", "content": full_response})
                            
                        except Exception as e:
                            error_msg = f"处理问题时出现错误: {e}"
                            message_placeholder.error(error_msg)
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        with col2:
            st.markdown("### 📊 系统信息")
            
            if st.session_state.api_configured:
                # 显示系统信息
                info_data = {
                    "API 提供商": api_provider,
                    "模型": model_name,
                    "向量化": embedding_type,
                    "温度": temperature,
                    "检索数量": top_k,
                    "对话数量": len(st.session_state.messages)
                }
                
                for key, value in info_data.items():
                    st.metric(key, value)
                
                # 系统状态
                st.success("🟢 系统正常运行")
            else:
                st.error("🔴 系统未配置")
            
            # 使用说明
            st.markdown("### 📖 使用说明")
            st.markdown("""
            1. 在侧边栏配置你的 API Key
            2. 选择适合的模型和参数
            3. 在对话框中输入问题
            4. 系统会基于 (G)I-DLE 知识库回答
            """)
    
    def _configure_api(self, provider: str, model: str, api_key: str, embedding: str):
        """配置 API"""
        try:
            # 设置环境变量（仅当前会话）
            if provider == "zhipu":
                os.environ["ZHIPUAI_API_KEY"] = api_key
            else:
                os.environ["OPENAI_API_KEY"] = api_key
            
            # 创建问答链管理器
            qa_manager = QaChainManager()
            
            # 测试连接
            test_chain = qa_manager.get_chain(
                model_provider=provider,
                model_name=model,
                embedding_type=embedding
            )
            
            # 保存到会话状态
            st.session_state.qa_manager = qa_manager
            st.session_state.current_model = provider
            st.session_state.current_embedding = embedding
            st.session_state.api_configured = True
            
            st.success("API 配置成功！")
            
        except Exception as e:
            st.error(f"API 配置失败: {e}")
            st.session_state.api_configured = False
    
    def _auto_configure_api(self):
        """自动配置 API（使用环境变量）"""
        try:
            # 检查环境变量
            zhipu_key = os.getenv("ZHIPUAI_API_KEY")
            openai_key = os.getenv("OPENAI_API_KEY")
            
            if zhipu_key:
                # 使用智谱AI
                provider = "zhipu"
                model = "chatglm_std"
                embedding = "m3e"
                
                # 创建问答链管理器
                qa_manager = QaChainManager()
                
                # 测试连接（添加更详细的错误处理）
                try:
                    test_chain = qa_manager.get_chain(
                        model_provider=provider,
                        model_name=model,
                        embedding_type=embedding
                    )
                except Exception as chain_error:
                    st.error(f"问答链初始化失败: {chain_error}")
                    return False
                
                # 保存到会话状态
                st.session_state.qa_manager = qa_manager
                st.session_state.current_model = provider
                st.session_state.current_embedding = embedding
                st.session_state.api_configured = True
                
                return True
                
            elif openai_key:
                # 使用 OpenAI
                provider = "openai"
                model = "gpt-3.5-turbo"
                embedding = "openai"
                
                # 创建问答链管理器
                qa_manager = QaChainManager()
                
                # 测试连接（添加更详细的错误处理）
                try:
                    test_chain = qa_manager.get_chain(
                        model_provider=provider,
                        model_name=model,
                        embedding_type=embedding
                    )
                except Exception as chain_error:
                    st.error(f"问答链初始化失败: {chain_error}")
                    return False
                
                # 保存到会话状态
                st.session_state.qa_manager = qa_manager
                st.session_state.current_model = provider
                st.session_state.current_embedding = embedding
                st.session_state.api_configured = True
                
                return True
            
            return False
            
        except Exception as e:
            st.error(f"自动配置失败: {e}")
            return False
    
    def run(self):
        """运行应用"""
        self.create_interface()

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='启动 Streamlit 应用')
    parser.add_argument('--port', type=int, default=8501, help='端口号')
    
    args = parser.parse_args()
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建并运行应用
    app = StreamlitApp()
    app.run()

if __name__ == "__main__":
    main() 