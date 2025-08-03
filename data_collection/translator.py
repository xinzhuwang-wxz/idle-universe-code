"""
(G)I-DLE Universe 翻译模块
使用 LLM 进行文本翻译
"""
import os
import sys
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
import json

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import config
from llm.zhipu_llm import ZhipuLLM
from llm.openai_llm import OpenAILLM

@dataclass
class TranslationResult:
    """翻译结果数据类"""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence: float = 1.0
    model_used: str = ""

class LLMTranslator:
    """基于 LLM 的翻译器"""
    
    def __init__(self, model_provider: str = "zhipu"):
        self.model_provider = model_provider
        self.logger = logging.getLogger(__name__)
        
        # 初始化 LLM
        if model_provider == "zhipu":
            self.llm = ZhipuLLM()
        elif model_provider == "openai":
            self.llm = OpenAILLM()
        else:
            raise ValueError(f"不支持的模型提供商: {model_provider}")
        
        # 翻译提示模板
        self.translation_prompt = """请将以下英文文本翻译成中文。要求：
1. 保持原文的意思和语气
2. 翻译要自然流畅
3. 保留专有名词的英文原名
4. 如果是关于 (G)I-DLE 的内容，请确保翻译准确

英文文本：
{text}

中文翻译："""
    
    def translate_text(self, text: str, source_lang: str = "en", target_lang: str = "zh") -> Optional[TranslationResult]:
        """翻译单个文本"""
        try:
            # 构建提示
            prompt = self.translation_prompt.format(text=text)
            
            # 调用 LLM 翻译
            response = self.llm.generate(prompt)
            
            if response:
                return TranslationResult(
                    original_text=text,
                    translated_text=response,
                    source_language=source_lang,
                    target_language=target_lang,
                    model_used=self.model_provider
                )
            else:
                self.logger.error("翻译失败：LLM 返回空响应")
                return None
                
        except Exception as e:
            self.logger.error(f"翻译失败: {e}")
            return None
    
    def translate_batch(self, texts: List[str], source_lang: str = "en", target_lang: str = "zh") -> List[TranslationResult]:
        """批量翻译文本"""
        results = []
        
        for i, text in enumerate(texts):
            self.logger.info(f"翻译进度: {i+1}/{len(texts)}")
            result = self.translate_text(text, source_lang, target_lang)
            if result:
                results.append(result)
            else:
                # 如果翻译失败，保留原文
                results.append(TranslationResult(
                    original_text=text,
                    translated_text=text,
                    source_language=source_lang,
                    target_language=target_lang,
                    confidence=0.0,
                    model_used=self.model_provider
                ))
        
        return results

class ContentTranslator:
    """内容翻译管理器"""
    
    def __init__(self, model_provider: str = "zhipu"):
        self.translator = LLMTranslator(model_provider)
        self.logger = logging.getLogger(__name__)
    
    def translate_crawl_results(self, results: List) -> List:
        """翻译爬取结果"""
        translated_results = []
        
        for result in results:
            self.logger.info(f"翻译内容: {result.title}")
            
            # 翻译标题
            title_translation = self.translator.translate_text(result.title)
            if title_translation:
                result.title = title_translation.translated_text
            
            # 翻译内容
            content_translation = self.translator.translate_text(result.content)
            if content_translation:
                result.content = content_translation.translated_text
                result.translated = True
                result.language = "zh"
            
            translated_results.append(result)
        
        return translated_results
    
    def save_translated_results(self, results: List, filename: str = None):
        """保存翻译结果"""
        if not filename:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"translated_results_{timestamp}.json"
        
        filepath = os.path.join(config.crawler.processed_data_dir, filename)
        
        # 转换为可序列化的格式
        serializable_results = []
        for result in results:
            serializable_results.append({
                'url': result.url,
                'title': result.title,
                'content': result.content,
                'timestamp': result.timestamp.isoformat(),
                'source': result.source,
                'language': result.language,
                'translated': result.translated
            })
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"保存了 {len(results)} 条翻译结果到 {filepath}")
        return filepath

def main():
    """测试翻译功能"""
    import argparse
    
    parser = argparse.ArgumentParser(description='翻译 (G)I-DLE 相关内容')
    parser.add_argument('--input-file', type=str, help='输入文件路径')
    parser.add_argument('--output-file', type=str, help='输出文件路径')
    parser.add_argument('--model', type=str, default='zhipu', choices=['zhipu', 'openai'], help='使用的模型')
    
    args = parser.parse_args()
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建翻译器
    translator = ContentTranslator(args.model)
    
    if args.input_file:
        # 从文件加载数据
        from data_collection.crawler import DataCollector
        collector = DataCollector()
        results = collector.load_results(args.input_file)
        
        # 翻译数据
        translated_results = translator.translate_crawl_results(results)
        
        # 保存结果
        output_file = args.output_file or f"translated_{os.path.basename(args.input_file)}"
        translator.save_translated_results(translated_results, output_file)
        
        print(f"翻译完成，共处理 {len(translated_results)} 条数据")
    else:
        # 测试翻译
        test_texts = [
            "(G)I-DLE is a South Korean girl group formed by Cube Entertainment.",
            "The group consists of five members: Soyeon, Minnie, Miyeon, Yuqi, and Shuhua.",
            "They debuted on May 2, 2018, with the single 'Latata'."
        ]
        
        results = translator.translator.translate_batch(test_texts)
        
        for i, result in enumerate(results):
            print(f"原文 {i+1}: {result.original_text}")
            print(f"翻译 {i+1}: {result.translated_text}")
            print()

if __name__ == "__main__":
    main() 