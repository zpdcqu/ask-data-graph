
好的，这里是为基于知识图谱的智能问数系统后端设计的表结构。这些表主要用于管理数据源、知识图谱构建过程、用户查询以及辅助 NL2SQL 的元数据。实际的知识图谱数据将存储在 Neo4j 中。

**核心表设计:**

1.  **`users` (用户信息表)**
    *   `id` (INT, 主键, 自增)
    *   `username` (VARCHAR(255), 唯一, 非空) - 用户名
    *   `password_hash` (VARCHAR(255), 非空) - 哈希后的密码
    *   `email` (VARCHAR(255), 唯一) - 邮箱
    *   `role` (VARCHAR(50), DEFAULT 'viewer') - 角色 (例如: 'admin', 'editor', 'viewer')
    *   `created_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP) - 创建时间
    *   `updated_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP) - 更新时间

2.  **`data_sources` (数据源信息表)**
    *   `id` (INT, 主键, 自增)
    *   `name` (VARCHAR(255), 非空) - 数据源名称 (建议在用户维度或全局唯一)
    *   `type` (ENUM('MySQL', 'PostgreSQL', 'API', 'CSV', 'Excel', 'Oracle', 'SQLServer', 'Other'), 非空) - 数据源类型
    *   `connection_params` (JSON, 非空) - 连接参数 (例如: host, port, username, password (需加密), file_path, api_endpoint, token等)
    *   `description` (TEXT) - 描述
    *   `status` (ENUM('active', 'inactive', 'error', 'pending_test'), DEFAULT 'pending_test') - 连接状态
    *   `created_by_user_id` (INT, 外键, 关联 `users.id`) - 创建者
    *   `created_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)
    *   `updated_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)
    *   `last_tested_at` (TIMESTAMP, NULLABLE) - 上次连接测试时间

3.  **`kg_pipelines` (知识图谱构建流程表)**
    *   `id` (INT, 主键, 自增)
    *   `name` (VARCHAR(255), 非空) - 流程名称
    *   `description` (TEXT) - 描述
    *   `target_kg_name` (VARCHAR(255), NULLABLE) - 目标知识图谱实例名 (用于区分Neo4j中的不同图)
    *   `schedule` (VARCHAR(100), NULLABLE) - Cron 表达式，用于定时执行 (例如: "0 2 * * *")
    *   `is_active` (BOOLEAN, DEFAULT true) - 是否激活
    *   `created_by_user_id` (INT, 外键, 关联 `users.id`)
    *   `created_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)
    *   `updated_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)

4.  **`kg_pipeline_tasks` (知识图谱构建任务/数据编排规则表)**
    *   `id` (INT, 主键, 自增)
    *   `pipeline_id` (INT, 外键, 关联 `kg_pipelines.id`, 非空)
    *   `task_order` (INT, 非空, DEFAULT 0) - 任务在流程中的执行顺序
    *   `task_name` (VARCHAR(255), 非空) - 任务名称
    *   `source_data_source_id` (INT, 外键, 关联 `data_sources.id`, 非空) - 源数据源
    *   `source_entity_identifier` (VARCHAR(512), 非空) - 源实体标识 (例如: 表名 `schema.tablename`, 文件名 `data.csv`, API路径 `/users`)
    *   `mapping_type` (ENUM('node', 'relationship'), 非空) - 映射类型 (节点或关系)
    *   `target_label_or_type` (VARCHAR(255), 非空) - Neo4j中的节点标签或关系类型
    *   `field_mappings` (JSON, NULLABLE) - 字段映射规则
        *   示例: `{"source_column_name": "target_property_name", "id_field": {"source_column": "user_id", "prefix": "user_"}, ...}`
        *   包含主键映射、属性映射、转换逻辑等。
    *   `relationship_source_node_config` (JSON, NULLABLE) - 当 `mapping_type` 为 'relationship' 时，定义源节点匹配规则。
        *   示例: `{"label": "User", "match_properties": {"userId": "source_column_user_id"}}`
    *   `relationship_target_node_config` (JSON, NULLABLE) - 当 `mapping_type` 为 'relationship' 时，定义目标节点匹配规则。
    *   `filter_condition` (TEXT, NULLABLE) - 源数据过滤条件 (例如 SQL WHERE 子句)
    *   `is_enabled` (BOOLEAN, DEFAULT true)
    *   `description` (TEXT)
    *   `created_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)
    *   `updated_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)

5.  **`kg_pipeline_runs` (知识图谱构建流程执行记录表)**
    *   `id` (BIGINT, 主键, 自增)
    *   `pipeline_id` (INT, 外键, 关联 `kg_pipelines.id`)
    *   `triggered_by_user_id` (INT, 外键, 关联 `users.id`, NULLABLE, 如果是定时任务则为空)
    *   `start_time` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)
    *   `end_time` (TIMESTAMP, NULLABLE)
    *   `status` (ENUM('running', 'success', 'failed', 'partial_success', 'cancelled'), 非空)
    *   `run_details` (TEXT, NULLABLE) - 执行日志摘要或错误信息

6.  **`kg_pipeline_task_runs` (知识图谱构建任务执行记录表)**
    *   `id` (BIGINT, 主键, 自增)
    *   `pipeline_run_id` (BIGINT, 外键, 关联 `kg_pipeline_runs.id`)
    *   `task_id` (INT, 外键, 关联 `kg_pipeline_tasks.id`)
    *   `start_time` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)
    *   `end_time` (TIMESTAMP, NULLABLE)
    *   `status` (ENUM('running', 'success', 'failed', 'skipped'), 非空)
    *   `input_record_count` (INT, NULLABLE)
    *   `output_record_count` (INT, NULLABLE)
    *   `error_message` (TEXT, NULLABLE)

7.  **`query_logs` (用户查询日志表)**
    *   `id` (BIGINT, 主键, 自增)
    *   `user_id` (INT, 外键, 关联 `users.id`, NULLABLE) - 查询用户
    *   `session_id` (VARCHAR(255), NULLABLE) - 会话ID，用于跟踪多轮对话
    *   `natural_language_query` (TEXT, 非空) - 用户输入的自然语言问题
    *   `target_data_source_id` (INT, 外键, 关联 `data_sources.id`, NULLABLE) - NL2SQL查询的目标数据源 (关系型数据库)
    *   `generated_sql` (TEXT, NULLABLE) - 系统生成的SQL语句
    *   `sql_execution_status` (ENUM('success', 'error', 'pending', 'not_executed'), DEFAULT 'pending') - SQL执行状态
    *   `execution_error_message` (TEXT, NULLABLE) - SQL执行错误信息
    *   `query_result_preview` (TEXT, NULLABLE) - 查询结果预览 (例如，前几行或摘要)
    *   `execution_time_ms` (INT, NULLABLE) - SQL执行耗时（毫秒）
    *   `llm_model_used` (VARCHAR(100), NULLABLE) - 使用的LLM模型
    *   `llm_prompt_tokens` (INT, NULLABLE) - LLM Prompt token数
    *   `llm_completion_tokens` (INT, NULLABLE) - LLM Completion token数
    *   `feedback_rating` (INT, NULLABLE) - 用户反馈评分 (例如 1-5)
    *   `feedback_comment` (TEXT, NULLABLE) - 用户反馈评论
    *   `created_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)

8.  **`db_schema_metadata` (目标数据库元数据表 - 用于NL2SQL)**
    *   `id` (INT, 主键, 自增)
    *   `data_source_id` (INT, 外键, 关联 `data_sources.id`, 非空) - 指向被查询的关系型数据库
    *   `db_name` (VARCHAR(255), NULLABLE) - 数据库名
    *   `table_name` (VARCHAR(255), 非空) - 表名
    *   `column_name` (VARCHAR(255), 非空) - 列名
    *   `data_type` (VARCHAR(100), 非空) - 数据类型 (例如: VARCHAR, INT, DATETIME)
    *   `is_primary_key` (BOOLEAN, DEFAULT false)
    *   `is_foreign_key` (BOOLEAN, DEFAULT false)
    *   `foreign_key_references_table` (VARCHAR(255), NULLABLE)
    *   `foreign_key_references_column` (VARCHAR(255), NULLABLE)
    *   `column_description` (TEXT, NULLABLE) - 列的业务含义描述 (非常重要，用于LLM理解)
    *   `sample_values` (JSON, NULLABLE) - 示例值 (例如: `["value1", "value2"]`)
    *   `semantics_tags` (JSON, NULLABLE) - 语义标签 (例如: `["地理位置", "时间"]`)
    *   `last_refreshed_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP) - 元数据上次刷新时间
    *   UNIQUE (`data_source_id`, `db_name`, `table_name`, `column_name`) - 确保元数据唯一性

9.  **`llm_prompts` (LLM提示词管理表 - 可选)**
    *   `id` (INT, 主键, 自增)
    *   `prompt_name` (VARCHAR(255), 唯一, 非空) - 提示词名称 (例如: "nl2sql_default", "sql_correction_v2")
    *   `prompt_template` (TEXT, 非空) - 提示词模板内容
    *   `version` (VARCHAR(50), DEFAULT '1.0') - 版本号
    *   `description` (TEXT)
    *   `is_active` (BOOLEAN, DEFAULT true) - 是否当前使用
    *   `parameters` (JSON, NULLABLE) - 该prompt模板期望的参数列表
    *   `created_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)
    *   `updated_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)

**关系说明:**

*   一个 `user` 可以创建多个 `data_sources`, `kg_pipelines`，并产生多个 `query_logs`。
*   一个 `data_source` 可以被多个 `kg_pipeline_tasks` 作为源，也可以被多个 `db_schema_metadata` 条目描述 (如果它是NL2SQL的目标库)。
*   一个 `kg_pipeline` 包含多个 `kg_pipeline_tasks`，并会产生多个 `kg_pipeline_runs`。
*   一个 `kg_pipeline_run` 包含多个 `kg_pipeline_task_runs`。
*   `query_logs` 中的 `target_data_source_id` 指向用户查询的目标关系型数据库。
*   `db_schema_metadata` 描述 `data_sources` 中类型为关系型数据库的表结构，为LLM生成SQL提供上下文。

**注意事项:**

*   **索引:** 在所有外键和经常用于查询条件的列上创建索引 (例如 `name`, `status`, `timestamp` 等)。
*   **JSON 字段:** JSON 字段提供了灵活性，但在某些数据库中直接查询其内部结构可能性能较低或语法复杂。主要用于存储配置信息。
*   **加密:** `data_sources.connection_params` 中敏感信息（如密码、token）在存储前应进行加密处理。
*   **扩展性:** 此表设计为初始版本，可根据具体业务需求进行调整和扩展。例如，更细致的权限管理可能需要额外的表。

这些表结构为后端系统提供了一个坚实的基础，用于管理数据集成、知识图谱构建以及自然语言查询的整个生命周期。
