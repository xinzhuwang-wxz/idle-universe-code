"""
(G)I-DLE Universe 主程序入口
整合数据采集、翻译、向量化、问答和部署功能
"""
import os
import sys
import logging
import argparse
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.config import config

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('idle_universe.log'),
            logging.StreamHandler()
        ]
    )

def check_data_exists():
    """检查数据是否存在"""
    from database.create_db import DatabaseManager
    
    manager = DatabaseManager()
    info = manager.get_db_info()
    
    # 检查知识库文件
    knowledge_files = info.get('knowledge_db_files', [])
    has_knowledge_data = len(knowledge_files) > 0
    
    # 检查向量数据库
    has_vector_db = info.get('vector_db_exists', False)
    
    return has_knowledge_data, has_vector_db

def auto_setup_data():
    """自动设置数据"""
    logging.info("检查数据状态...")
    
    has_knowledge_data, has_vector_db = check_data_exists()
    
    if not has_knowledge_data:
        logging.info("未发现知识库数据，开始自动爬取...")
        crawl_data_auto()
    else:
        logging.info("发现知识库数据，跳过爬取步骤")
    
    if not has_vector_db:
        if has_knowledge_data:
            logging.info("发现知识库数据但向量数据库不存在，开始从现有数据构建向量数据库...")
        else:
            logging.info("未发现向量数据库，开始构建...")
        build_database_auto()
    else:
        logging.info("发现向量数据库，跳过构建步骤")

def crawl_data_auto():
    """自动数据采集"""
    from data_collection.crawler import DataCollector
    
    logging.info("开始自动数据采集...")
    
    collector = DataCollector()
    results = collector.crawl_all_sites()
    
    if results:
        filepath = collector.save_results(results)
        logging.info(f"数据采集完成，保存到: {filepath}")
        
        # 自动翻译
        from data_collection.translator import ContentTranslator
        translator = ContentTranslator(model_provider="zhipu")
        translated_results = translator.translate_crawl_results(results)
        translator.save_translated_results(translated_results)
        logging.info("翻译完成")
    else:
        logging.warning("未获取到任何数据")

def build_database_auto():
    """自动构建数据库"""
    from database.create_db import DatabaseManager
    
    logging.info("开始构建向量数据库...")
    
    manager = DatabaseManager()
    vectordb = manager.create_vector_db("m3e")
    
    if vectordb:
        logging.info("向量数据库创建成功")
    else:
        logging.error("向量数据库创建失败")

def crawl_data(args):
    """数据采集功能"""
    from data_collection.crawler import DataCollector
    
    logging.info("开始数据采集...")
    
    collector = DataCollector()
    
    if args.all_sites:
        results = collector.crawl_all_sites()
    elif args.site:
        results = collector.crawl_site(args.site)
    else:
        logging.error("请指定 --all-sites 或 --site 参数")
        return
    
    if results:
        filepath = collector.save_results(results)
        logging.info(f"数据采集完成，保存到: {filepath}")
        
        # 如果指定了翻译，则进行翻译
        if args.translate:
            from data_collection.translator import ContentTranslator
            translator = ContentTranslator(model_provider=args.translate_model)
            translated_results = translator.translate_crawl_results(results)
            translator.save_translated_results(translated_results)
            logging.info("翻译完成")
    else:
        logging.warning("未获取到任何数据")

def build_database(args):
    """构建数据库功能"""
    from database.create_db import DatabaseManager
    
    logging.info("开始构建向量数据库...")
    
    manager = DatabaseManager()
    
    if args.action == "create":
        vectordb = manager.create_vector_db(args.embedding)
        if vectordb:
            logging.info("向量数据库创建成功")
        else:
            logging.error("向量数据库创建失败")
    
    elif args.action == "update":
        manager.update_vector_db(args.embedding)
        logging.info("向量数据库更新完成")
    
    elif args.action == "info":
        info = manager.get_db_info()
        logging.info(f"数据库信息: {info}")

def test_qa(args):
    """测试问答功能"""
    from qa_chain.lcel_chain import QaChainManager
    
    logging.info("开始测试问答功能...")
    
    manager = QaChainManager()
    chain = manager.get_chain(
        model_provider=args.model,
        embedding_type=args.embedding
    )
    
    # 测试问题
    test_questions = [
        "什么是(G)I-DLE?",
        "介绍一下(G)I-DLE的成员",
        "她们的代表作有哪些?"
    ]
    
    for question in test_questions:
        logging.info(f"测试问题: {question}")
        result = chain.answer(question)
        logging.info(f"回答: {result['answer']}")
        logging.info(f"来源: {result['sources']}")
        print("-" * 50)

def deploy_app(args):
    """部署应用功能"""
    if args.deploy == "local":
        # 本地部署 - 自动检查数据
        auto_setup_data()
        
        # 启动 Gradio 应用
        from serve.gradio_app import GradioApp
        app = GradioApp()
        app.launch(share=args.share, port=args.port)
    
    elif args.deploy == "gradio":
        from serve.gradio_app import GradioApp
        app = GradioApp()
        app.launch(share=args.share, port=args.port)
    
    elif args.deploy == "streamlit":
        import subprocess
        cmd = f"streamlit run serve/streamlit_app.py --server.port {args.port}"
        subprocess.run(cmd, shell=True)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='(G)I-DLE Universe 智能问答系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 爬取所有网站数据
  python main.py --crawl --all-sites --translate
  
  # 构建向量数据库
  python main.py --build-db --action create
  
  # 测试问答功能
  python main.py --test-qa --model zhipu
  
  # 启动本地部署（自动检查数据）
  python main.py --deploy local --port 7860
  
  # 启动 Gradio 应用
  python main.py --deploy gradio --port 7860
  
  # 启动 Streamlit 应用
  python main.py --deploy streamlit --port 8501
        """
    )
    
    # 数据采集参数
    parser.add_argument('--crawl', action='store_true', help='执行数据采集')
    parser.add_argument('--all-sites', action='store_true', help='爬取所有网站')
    parser.add_argument('--site', type=str, help='指定爬取的网站')
    parser.add_argument('--translate', action='store_true', help='翻译采集的数据')
    parser.add_argument('--translate-model', type=str, default='zhipu', 
                       choices=['zhipu', 'openai'], help='翻译使用的模型')
    
    # 数据库构建参数
    parser.add_argument('--build-db', action='store_true', help='构建向量数据库')
    parser.add_argument('--action', type=str, choices=['create', 'update', 'info'], 
                       default='create', help='数据库操作类型')
    parser.add_argument('--embedding', type=str, default='m3e', 
                       choices=['m3e', 'openai'], help='向量化模型')
    
    # 测试参数
    parser.add_argument('--test-qa', action='store_true', help='测试问答功能')
    parser.add_argument('--model', type=str, default='zhipu', 
                       choices=['zhipu', 'openai'], help='测试使用的模型')
    
    # 部署参数
    parser.add_argument('--deploy', type=str, choices=['local', 'gradio', 'streamlit'], 
                       help='部署类型')
    parser.add_argument('--port', type=int, default=12820, help='端口号')
    parser.add_argument('--share', action='store_true', help='是否分享链接')
    
    # 其他参数
    parser.add_argument('--verbose', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        setup_logging()
    
    # 显示欢迎信息
    print("🎵 (G)I-DLE Universe 智能问答系统")
    print("=" * 50)
    
    try:
        # 执行相应功能
        if args.crawl:
            crawl_data(args)
        
        elif args.build_db:
            build_database(args)
        
        elif args.test_qa:
            test_qa(args)
        
        elif args.deploy:
            deploy_app(args)
        
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
    except Exception as e:
        logging.error(f"程序执行出错: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main() 