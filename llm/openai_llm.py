"""
OpenAI LLM 调用模块
"""
import os
import sys
import logging
from typing import Optional, Dict, Any
import openai
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import config

class OpenAILLM:
    """OpenAI LLM 调用类"""
    
    def __init__(self, model: str = "gpt-3.5-turbo", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or config.llm.openai_api_key
        
        if not self.api_key:
            raise ValueError("未设置 OpenAI API Key")
        
        # 设置 OpenAI API Key
        openai.api_key = self.api_key
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
            
            # 调用 OpenAI API
            response = openai.ChatCompletion.create(
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
                self.logger.error("OpenAI 返回空响应")
                return None
                
        except Exception as e:
            self.logger.error(f"OpenAI 调用失败: {e}")
            return None
    
    def generate_stream(self, prompt: str, temperature: Optional[float] = None, max_tokens: Optional[int] = None):
        """流式生成文本"""
        try:
            temp = temperature if temperature is not None else self.temperature
            tokens = max_tokens if max_tokens is not None else self.max_tokens
            
            # 流式调用
            response = openai.ChatCompletion.create(
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
            self.logger.error(f"OpenAI 流式调用失败: {e}")
            yield f"错误: {e}"
    
    def get_available_models(self) -> list:
        """获取可用的模型列表"""
        return config.llm.supported_models["openai"]
    
    def set_model(self, model: str):
        """设置模型"""
        if model in self.get_available_models():
            self.model = model
            self.logger.info(f"模型已切换到: {model}")
        else:
            raise ValueError(f"不支持的模型: {model}")

def main():
    """测试 OpenAI LLM"""
    import argparse
    
    parser = argparse.ArgumentParser(description='测试 OpenAI LLM')
    parser.add_argument('--model', type=str, default='gpt-3.5-turbo', help='使用的模型')
    parser.add_argument('--prompt', type=str, default='Hello, please introduce (G)I-DLE', help='测试提示')
    
    args = parser.parse_args()
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # 创建 LLM 实例
        llm = OpenAILLM(model=args.model)
        
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