# (G)I-DLE Universe - 智能问答系统

## 🎯 项目简介

(G)I-DLE Universe 是一个基于大语言模型的智能问答系统，专门为 (G)I-DLE 粉丝和研究者提供全面的团体信息查询服务。系统通过爬取公开网站信息，构建知识库，并利用先进的 RAG (Retrieval-Augmented Generation) 技术提供准确的问答服务。

## ✨ 主要功能

- **智能问答**: 基于 (G)I-DLE 相关知识库的智能问答
- **多源数据**: 自动爬取 Wikipedia、官方新闻、粉丝网站等信息
- **多语言支持**: 自动翻译并存储中文内容
- **双部署方案**: 支持本地 Gradio 部署和线上 Streamlit 部署
- **模块化设计**: 清晰的代码结构，易于维护和扩展

## 🏗️ 项目结构

```
idle_universe/
├── data_collection/     # 数据采集模块
│   ├── __init__.py
│   ├── crawler.py      # 爬虫核心
│   └── translator.py   # 翻译模块
├── database/           # 数据库管理
│   ├── __init__.py
│   ├── create_db.py   # 数据库创建和管理
│   └── rebuild_faiss_db.py # FAISS数据库重建
├── llm/                # 大语言模型
│   ├── __init__.py
│   ├── zhipu_llm.py   # 智谱AI调用
│   └── openai_llm.py  # OpenAI调用
├── qa_chain/           # 问答链模块
│   ├── __init__.py
│   └── lcel_chain.py  # LCEL问答链
├── serve/              # 部署服务
│   ├── __init__.py
│   ├── gradio_app.py  # 本地Gradio部署
│   └── streamlit_app.py # 线上Streamlit部署
├── utils/              # 通用工具
│   ├── __init__.py
│   ├── config.py      # 配置管理
│   ├── compatibility_check.py # 兼容性检查
│   └── data_sync.py   # 数据同步工具
├
├── knowledge_db/       # 知识库存储
│   ├── raw/           # 原始数据
│   └── processed/     # 处理后数据
├── vector_db/          # 向量数据库存储
│   └── faiss/         # FAISS向量数据库
├── .streamlit/         # Streamlit配置
│   └── config.toml
├── deploy_temp/        # 部署包（自动生成）
├── main.py            # 主程序入口
├── deploy.py          # 部署工具
├── requirements.txt    # 依赖包
└── README.md          # 项目说明
```

## 🚀 快速开始

### 环境要求

- Python >= 3.9
- 内存 >= 4GB
- 网络连接（用于爬取数据）

### 安装依赖

```bash
# 克隆项目
git clone <your-repo-url>
cd idle_universe

# 创建虚拟环境
conda create -n idle_universe python=3.9
conda activate idle_universe

# 安装依赖
pip install -r requirements.txt
```

### 一键启动

```bash
# 体验网站：问主包要

# 方式2：完整流程本地部署（推荐）
python main.py --deploy local

# 方式3：自定义线上部署 （见下文）
```


### 数据采集

```bash
# 爬取所有配置的网站
python data_collection/crawler.py --all

# 爬取特定网站
python data_collection/crawler.py --site wikipedia
```

### 构建知识库

```bash
# 创建向量数据库
python database/create_db.py

# 重建FAISS数据库
python database/rebuild_faiss_db.py
```

### 自定义线上部署
```bash
python main.py --deploy local  # 先本地
python deploy.py

# 将 deploy_temp 目录推送到自定义GitHub
```

## 🔧 配置说明

### API 配置

创建 `.env` 文件或在 Streamlit Cloud 中设置环境变量：

```env
# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# 智谱AI API
ZHIPUAI_API_KEY=your_zhipuai_api_key
```

### 部署配置

- **本地部署**: 使用 Gradio 界面，适合个人使用
- **线上部署**: 使用 Streamlit 界面，支持多人访问，自动配置API密钥

## 📊 功能特性

### 智能问答
- 支持连续对话
- 基于历史记录优化检索
- 提供准确的中文回答
- 流式回答支持

### 数据管理
- 自动数据爬取和更新
- 智能数据清理和去重
- 多语言内容翻译
- FAISS向量数据库

### 部署方案
- **本地部署**: Gradio 界面，适合个人使用
- **线上部署**: Streamlit 界面，支持多人访问，自动API配置

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 发起 Pull Request

## 📝 许可证

本项目采用 MIT 许可证。

## 🙏 致谢

感谢 (G)I-DLE 和所有粉丝社区提供的丰富信息源。

---

**注意**: 本项目仅用于学习和研究目的，请遵守相关网站的使用条款和版权规定。
