"""
(G)I-DLE Universe Gradio 本地部署模块
"""
import os
import sys
import logging
import gradio as gr
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import config
from qa_chain.lcel_chain import QaChainManager

class GradioApp:
    """Gradio 应用类"""
    
    def __init__(self):
        self.config = config.deploy
        self.app_config = config.app
        self.logger = logging.getLogger(__name__)
        
        # 初始化问答链管理器
        self.qa_manager = QaChainManager()
        
        # 存储聊天历史
        self.chat_history = []
        
        # 当前配置
        self.current_model = "zhipu"
        self.current_embedding = "m3e"
    
    def create_interface(self):
        """创建 Gradio 界面"""
        with gr.Blocks(
            title=self.app_config.app_name,
            theme=gr.themes.Soft(
                primary_hue=gr.themes.Color(
                    c50="#FFE5F0",
                    c100="#FFCCE0",
                    c200="#FF99C2",
                    c300="#FF66A3",
                    c400="#FF3385",
                    c500="#FF0066",
                    c600="#CC0052",
                    c700="#99003D",
                    c800="#660029",
                    c900="#330014",
                    c950="#1A000A",
                )
            )
        ) as demo:
            
            # 标题和描述
            gr.Markdown(f"""
            # {self.app_config.app_name}
            ## {self.app_config.app_description}
            
            欢迎使用 (G)I-DLE 智能问答系统！你可以询问任何关于 (G)I-DLE 的问题。
            """)
            
            with gr.Row():
                with gr.Column(scale=3):
                    # 聊天界面
                    chatbot = gr.Chatbot(
                        label="对话历史",
                        height=500,
                        show_label=True
                    )
                    
                    with gr.Row():
                        msg = gr.Textbox(
                            label="输入问题",
                            placeholder="请输入你的问题...",
                            lines=2
                        )
                        submit_btn = gr.Button("发送", variant="primary")
                    
                    with gr.Row():
                        clear_btn = gr.Button("清除历史")
                        stream_btn = gr.Button("流式回答", variant="secondary")
                
                with gr.Column(scale=1):
                    # 设置面板
                    gr.Markdown("### 设置")
                    
                    model_dropdown = gr.Dropdown(
                        choices=["zhipu", "openai"],
                        value="zhipu",
                        label="模型提供商"
                    )
                    
                    embedding_dropdown = gr.Dropdown(
                        choices=["m3e", "openai"],
                        value="m3e",
                        label="向量化模型"
                    )
                    
                    temperature_slider = gr.Slider(
                        minimum=0.0,
                        maximum=1.0,
                        value=0.1,
                        step=0.1,
                        label="温度 (创造性)"
                    )
                    
                    top_k_slider = gr.Slider(
                        minimum=1,
                        maximum=10,
                        value=4,
                        step=1,
                        label="检索文档数量"
                    )
                    
                    # 系统信息
                    gr.Markdown("### 系统信息")
                    info_text = gr.Textbox(
                        value="系统就绪",
                        label="状态",
                        interactive=False
                    )
            
            # 事件处理
            def respond(message, history, model, embedding, temp, top_k):
                """处理用户输入并生成回答"""
                if not message.strip():
                    return "", history
                
                try:
                    # 获取问答链
                    chain = self.qa_manager.get_chain(
                        model_provider=model,
                        embedding_type=embedding
                    )
                    
                    # 更新链参数
                    chain.temperature = temp
                    chain.top_k = top_k
                    
                    # 生成回答
                    result = chain.answer(message, history)
                    
                    # 更新历史
                    history.append((message, result["answer"]))
                    
                    return "", history
                    
                except Exception as e:
                    error_msg = f"处理问题时出现错误: {e}"
                    history.append((message, error_msg))
                    return "", history
            
            def respond_stream(message, history, model, embedding, temp, top_k):
                """流式回答"""
                if not message.strip():
                    return "", history
                
                try:
                    # 获取问答链
                    chain = self.qa_manager.get_chain(
                        model_provider=model,
                        embedding_type=embedding
                    )
                    
                    # 更新链参数
                    chain.temperature = temp
                    chain.top_k = top_k
                    
                    # 流式生成回答
                    response = ""
                    for chunk in chain.answer_stream(message, history):
                        response += chunk
                        yield "", history + [(message, response)]
                    
                except Exception as e:
                    error_msg = f"处理问题时出现错误: {e}"
                    history.append((message, error_msg))
                    yield "", history
            
            def clear_history():
                """清除聊天历史"""
                return []
            
            def update_info(model, embedding):
                """更新系统信息"""
                try:
                    chain = self.qa_manager.get_chain(model, embedding_type=embedding)
                    info = chain.get_chain_info()
                    return f"模型: {info['model_name']}\n向量化: {info['embedding_type']}\n状态: 正常"
                except Exception as e:
                    return f"状态: 错误 - {e}"
            
            # 绑定事件
            submit_btn.click(
                respond,
                inputs=[msg, chatbot, model_dropdown, embedding_dropdown, temperature_slider, top_k_slider],
                outputs=[msg, chatbot]
            )
            
            stream_btn.click(
                respond_stream,
                inputs=[msg, chatbot, model_dropdown, embedding_dropdown, temperature_slider, top_k_slider],
                outputs=[msg, chatbot]
            )
            
            clear_btn.click(
                clear_history,
                outputs=[chatbot]
            )
            
            # 回车发送
            msg.submit(
                respond,
                inputs=[msg, chatbot, model_dropdown, embedding_dropdown, temperature_slider, top_k_slider],
                outputs=[msg, chatbot]
            )
            
            # 设置变化时更新信息
            model_dropdown.change(
                update_info,
                inputs=[model_dropdown, embedding_dropdown],
                outputs=[info_text]
            )
            
            embedding_dropdown.change(
                update_info,
                inputs=[model_dropdown, embedding_dropdown],
                outputs=[info_text]
            )
        
        return demo
    
    def launch(self, share: bool = None, port: int = None):
        """启动应用"""
        share = share if share is not None else self.config.gradio_share
        port = port if port is not None else self.config.gradio_port
        
        demo = self.create_interface()
        
        self.logger.info(f"启动 Gradio 应用，端口: {port}, 分享: {share}")
        
        demo.launch(
            server_name="0.0.0.0",
            server_port=port,
            share=share,
            show_error=True
        )

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='启动 Gradio 应用')
    parser.add_argument('--port', type=int, default=12820, help='端口号')
    parser.add_argument('--share', action='store_true', help='是否分享链接')
    
    args = parser.parse_args()
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建并启动应用
    app = GradioApp()
    app.launch(share=args.share, port=args.port)

if __name__ == "__main__":
    main() 