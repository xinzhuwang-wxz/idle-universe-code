"""
智谱AI LLM 调用模块
"""
import os
import sys
import logging
from typing import Optional, Dict, Any, List
import zhipuai
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import config
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration

class ZhipuLLM:
    """智谱AI LLM 调用类"""
    
    def __init__(self, model: str = "chatglm_std", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or config.llm.zhipuai_api_key
        
        if not self.api_key:
            raise ValueError("未设置智谱AI API Key")
        
        # 初始化客户端
        self.client = zhipuai.ZhipuAI(api_key=self.api_key)
        self.logger = logging.getLogger(__name__)
        
        # 默认参数
        self.temperature = config.llm.temperature
        self.max_tokens = config.llm.max_tokens
    
    def generate(self, prompt: str, temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> Optional[str]:
        """生成文本"""
        try:
            # 使用配置的参数
            temp = temperature if temperature is not None else self.temperature
            tokens = max_tokens if max_tokens is not None else self.max_tokens
            
            # 调用智谱AI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temp,
                max_tokens=tokens
            )
            
            # 提取回复内容
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content
            else:
                self.logger.error("智谱AI 返回空响应")
                return None
                
        except Exception as e:
            self.logger.error(f"智谱AI 调用失败: {e}")
            return None
    
    def generate_stream(self, prompt: str, temperature: Optional[float] = None, max_tokens: Optional[int] = None):
        """流式生成文本"""
        try:
            temp = temperature if temperature is not None else self.temperature
            tokens = max_tokens if max_tokens is not None else self.max_tokens
            
            # 流式调用
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temp,
                max_tokens=tokens,
                stream=True
            )
            
            for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content
                        
        except Exception as e:
            self.logger.error(f"智谱AI 流式调用失败: {e}")
            yield f"错误: {e}"
    
    def get_available_models(self) -> list:
        """获取可用的模型列表"""
        return config.llm.supported_models["zhipu"]
    
    def set_model(self, model: str):
        """设置模型"""
        if model in self.get_available_models():
            self.model = model
            self.logger.info(f"模型已切换到: {model}")
        else:
            raise ValueError(f"不支持的模型: {model}")

class ZhipuChatModel(BaseChatModel):
    """智谱AI LangChain 兼容的聊天模型"""
    
    zhipu_llm: ZhipuLLM
    model: str
    temperature: float
    max_tokens: int
    
    def __init__(self, model: str = "chatglm_std", api_key: Optional[str] = None, **kwargs):
        zhipu_llm = ZhipuLLM(model=model, api_key=api_key)
        super().__init__(
            zhipu_llm=zhipu_llm,
            model=model,
            temperature=zhipu_llm.temperature,
            max_tokens=zhipu_llm.max_tokens,
            **kwargs
        )
    
    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs) -> ChatResult:
        """生成回复"""
        # 将消息转换为文本
        prompt = self._messages_to_text(messages)
        
        # 调用智谱AI
        response = self.zhipu_llm.generate(
            prompt=prompt,
            temperature=kwargs.get('temperature', self.temperature),
            max_tokens=kwargs.get('max_tokens', self.max_tokens)
        )
        
        if response is None:
            raise Exception("智谱AI 生成失败")
        
        # 创建回复消息
        ai_message = AIMessage(content=response)
        
        return ChatResult(
            generations=[ChatGeneration(message=ai_message)]
        )
    
    def _messages_to_text(self, messages: List[BaseMessage]) -> str:
        """将消息列表转换为文本"""
        text_parts = []
        for message in messages:
            if isinstance(message, HumanMessage):
                text_parts.append(f"用户: {message.content}")
            elif isinstance(message, AIMessage):
                text_parts.append(f"助手: {message.content}")
            else:
                text_parts.append(f"{message.type}: {message.content}")
        
        return "\n".join(text_parts)
    
    @property
    def _llm_type(self) -> str:
        return "zhipu"

def main():
    """测试智谱AI LLM"""
    import argparse
    
    parser = argparse.ArgumentParser(description='测试智谱AI LLM')
    parser.add_argument('--model', type=str, default='chatglm_std', help='使用的模型')
    parser.add_argument('--prompt', type=str, default='你好，请介绍一下(G)I-DLE', help='测试提示')
    
    args = parser.parse_args()
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # 创建 LLM 实例
        llm = ZhipuLLM(model=args.model)
        
        print(f"使用模型: {args.model}")
        print(f"测试提示: {args.prompt}")
        print("-" * 50)
        
        # 测试生成
        response = llm.generate(args.prompt)
        if response:
            print(f"回复: {response}")
        else:
            print("生成失败")
        
        print("-" * 50)
        
        # 测试流式生成
        print("流式生成:")
        for chunk in llm.generate_stream(args.prompt):
            print(chunk, end='', flush=True)
        print()
        
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    main() 