# 基于知识图谱的智能问数项目

本项目旨在构建一个智能问答系统，允许用户通过自然语言查询存储在关系型数据库中的数据，并支持知识图谱的构建与可视化。

## 主要功能

- 自然语言问答 (NL2SQL)
- 数据源管理
- 数据库元数据管理
- 知识图谱构建与可视化 (后续阶段)
- 用户认证与管理

## 技术栈

### 后端
- Python (FastAPI)
- MySQL (主业务数据库)
- Nebula Graph (图数据库)
- litellm (与 OpenAI GPT 等 LLM 交互)
- SQLAlchemy (ORM)

### 前端
- React (Vite)
- Ant Design (UI 组件库)
- Redux Toolkit (状态管理)
- Axios (HTTP Client)
- AntV G6/G2 或 ECharts (图表与图谱可视化)

## 目录结构 (初步)

\`\`\`
.
├── backend/        # 后端代码 (FastAPI)
├──|app/
├──├── api/ # API定义与实现
├──│ └── v1/
├──│ ├── endpoints/ # API端点实现
├──│ ├── schemas/ # 请求和响应数据模型
├──│ └── init.py
├──├── core/ # 核心功能
├──│ ├── config.py # 配置管理
├──│ ├── deps.py # 依赖注入
├──│ ├── security.py # 安全功能
├──│ └── init.py
├──├── crud/ # 数据库CRUD操作
├──├── db/ # 数据库模型和连接管理
├──├── services/ # 业务逻辑服务层
├──├── main.py # FastAPI应用入口
├──└── init.py
├── frontend/       # 前端代码 (React)
├── doc/            # 项目需求文档
├── docs/           # 开发及部署文档
├── scripts/        # 辅助脚本
├── .gitignore
└── README.md
\`\`\`

## 后端详细结构

`backend/` 目录是基于 FastAPI 的知识图谱智能问答系统后端服务，采用了模块化的组织方式：

### 主要文件
- `run.py`：服务启动脚本，负责初始化和运行 FastAPI 服务
- `requirements.txt`：Python 依赖包列表，包含 FastAPI、数据库驱动、认证和其他功能库
- `service_config.yaml`：服务配置文件，包含服务器设置和其他参数

### app 目录结构

#### API模块详解
`/app/api` 目录是API层，主要包含以下内容：

##### 认证API (`auth_endpoints.py`)
- `/login` - 用户登录，获取JWT令牌
- `/register` - 用户注册
- `/users/me` - 获取当前登录用户信息

##### 知识图谱可视化API (`kg_visualization_endpoints.py`)
- `/neighbors/{node_id}` - 获取知识图谱中指定节点的邻居
- `/search` - 基于关键词搜索知识图谱节点

##### 知识图谱管道API
- `kg_pipeline_endpoints.py` - 知识图谱处理流水线管理
- `kg_pipeline_task_endpoints.py` - 流水线任务管理
- `kg_pipeline_run_endpoints.py` - 流水线运行记录

##### 数据源API (`data_sources.py`)
- 数据源管理相关接口

##### 数据模型 (Schemas)
- `token_schemas.py` - JWT令牌数据结构
- `user_schemas.py` - 用户相关数据模型
- `kg_visualization_schemas.py` - 知识图谱可视化数据结构

## 启动与开发

(后续补充) 