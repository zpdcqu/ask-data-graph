这是一份为基于知识图谱的智能问数系统后端设计的 REST API 文档。

**API 版本:** v1
**基础 URL:** `/api/v1`

---

**通用约定:**

*   **认证:** 大部分接口需要通过 JWT (JSON Web Token) 进行认证。Token 在登录后获取，并通过 `Authorization: Bearer <token>` HTTP 头部传递。
*   **请求体格式:** `application/json`
*   **响应体格式:** `application/json`
*   **错误响应:**
    ```json
    {
      "error": {
        "code": "ERROR_CODE_STRING", // 例如: "VALIDATION_ERROR", "RESOURCE_NOT_FOUND"
        "message": "详细的错误描述",
        "details": {} // 可选，更详细的错误信息，例如字段校验错误
      }
    }
    ```
    常见的 HTTP 状态码：
    *   `200 OK`: 请求成功。
    *   `201 Created`: 资源创建成功。
    *   `204 No Content`: 请求成功，但响应体为空 (例如 DELETE 成功)。
    *   `400 Bad Request`: 请求无效 (例如，参数错误，JSON 格式错误)。
    *   `401 Unauthorized`: 未认证或认证失败。
    *   `403 Forbidden`: 已认证，但无权限访问该资源。
    *   `404 Not Found`: 请求的资源不存在。
    *   `409 Conflict`: 资源冲突 (例如，尝试创建已存在的唯一资源)。
    *   `500 Internal Server Error`: 服务器内部错误。
*   **分页:** 对于列表接口，支持分页。
    *   查询参数: `page` (默认为 1), `per_page` (默认为 20)。
    *   响应体:
        ```json
        {
          "items": [ /* 列表数据 */ ],
          "total_items": 100,
          "total_pages": 5,
          "current_page": 1,
          "per_page": 20
        }
        ```

---

**1. 认证 (Auth)**

*   **Endpoint:** `/auth/login`
*   **Method:** `POST`
*   **Description:** 用户登录，获取 JWT。
*   **Request Body:**
    ```json
    {
      "username": "user1",
      "password": "password123"
    }
    ```
*   **Success Response (200 OK):**
    ```json
    {
      "access_token": "your_jwt_token_here",
      "token_type": "bearer",
      "user_info": {
        "id": 1,
        "username": "user1",
        "email": "user1@example.com",
        "role": "admin"
      }
    }
    ```
*   **Error Response:** `400 Bad Request`, `401 Unauthorized`

*   **Endpoint:** `/auth/register`
*   **Method:** `POST`
*   **Description:** 用户注册。
*   **Request Body:**
    ```json
    {
      "username": "newuser",
      "password": "newpassword123",
      "email": "newuser@example.com"
    }
    ```
*   **Success Response (201 Created):**
    ```json
    {
      "id": 2,
      "username": "newuser",
      "email": "newuser@example.com",
      "role": "viewer",
      "message": "User registered successfully"
    }
    ```
*   **Error Response:** `400 Bad Request` (例如，用户名已存在), `409 Conflict`

---

**2. 用户 (Users)**

*   **Endpoint:** `/users/me`
*   **Method:** `GET`
*   **Description:** 获取当前登录用户信息。
*   **Authentication:** Required.
*   **Success Response (200 OK):**
    ```json
    {
      "id": 1,
      "username": "user1",
      "email": "user1@example.com",
      "role": "admin",
      "created_at": "2023-10-27T10:00:00Z"
    }
    ```
*   **Error Response:** `401 Unauthorized`

*   **Endpoint:** `/users/{user_id}` (管理员接口)
*   **Method:** `GET`, `PUT`, `DELETE`
*   **Description:**
    *   `GET`: 获取指定用户信息。
    *   `PUT`: 更新指定用户信息。
    *   `DELETE`: 删除指定用户。
*   **Authentication:** Required. Role: `admin`.
*   **PUT Request Body:**
    ```json
    {
      "email": "updated_email@example.com",
      "role": "editor"
    }
    ```
*   **Success Response:** `200 OK` (GET, PUT), `204 No Content` (DELETE)
*   **Error Response:** `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

---

**3. 数据源 (Data Sources)**

*   **Endpoint:** `/data-sources`
*   **Method:** `POST`
*   **Description:** 创建新的数据源连接。
*   **Authentication:** Required. Role: `editor`, `admin`.
*   **Request Body:**
    ```json
    {
      "name": "My Production MySQL",
      "type": "MySQL", // ENUM: 'MySQL', 'PostgreSQL', 'API', 'CSV', 'Excel', ...
      "connection_params": { // 结构因 type 而异
        "host": "localhost",
        "port": 3306,
        "username": "db_user",
        "password": "db_password", // 后端应加密存储
        "database": "prod_db"
      },
      "description": "Production customer database"
    }
    ```
*   **Success Response (201 Created):**
    ```json
    {
      "id": 1,
      "name": "My Production MySQL",
      "type": "MySQL",
      "connection_params": { /* 敏感信息可能被屏蔽 */ },
      "description": "Production customer database",
      "status": "pending_test",
      "created_by_user_id": 1,
      "created_at": "2023-10-27T10:05:00Z"
    }
    ```
*   **Error Response:** `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`

*   **Endpoint:** `/data-sources`
*   **Method:** `GET`
*   **Description:** 获取数据源列表 (支持分页和过滤)。
*   **Authentication:** Required.
*   **Query Parameters:** `page`, `per_page`, `type`, `status`, `name_contains`
*   **Success Response (200 OK):** (分页结构)
    ```json
    {
      "items": [
        {
          "id": 1,
          "name": "My Production MySQL",
          "type": "MySQL",
          "status": "active",
          "last_tested_at": "2023-10-27T10:10:00Z"
        }
      ],
      // ...分页元数据
    }
    ```
*   **Error Response:** `401 Unauthorized`

*   **Endpoint:** `/data-sources/{source_id}`
*   **Method:** `GET`, `PUT`, `DELETE`
*   **Description:**
    *   `GET`: 获取指定数据源详情。
    *   `PUT`: 更新指定数据源信息。
    *   `DELETE`: 删除指定数据源。
*   **Authentication:** Required. Role for PUT/DELETE: `editor`, `admin` (或创建者)。
*   **PUT Request Body:** (同 POST，但只包含要更新的字段)
*   **Success Response:** `200 OK` (GET, PUT), `204 No Content` (DELETE)
*   **Error Response:** `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

*   **Endpoint:** `/data-sources/{source_id}/test-connection`
*   **Method:** `POST`
*   **Description:** 测试数据源连接。
*   **Authentication:** Required.
*   **Success Response (200 OK):**
    ```json
    {
      "status": "success", // "success" or "failed"
      "message": "Connection successful" // or error message
    }
    ```
*   **Error Response:** `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

---

**4. 知识图谱构建流程 (Knowledge Graph Pipelines)**

*   **Endpoint:** `/kg-pipelines`
*   **Method:** `POST`, `GET`
*   **Authentication:** Required.
*   **POST (Create Pipeline):**
    *   Role: `editor`, `admin`.
    *   **Request Body:**
        ```json
        {
          "name": "Customer Data KG Pipeline",
          "description": "Builds KG from customer and order data",
          "target_kg_name": "customer_graph",
          "schedule": "0 1 * * *" // Optional cron schedule
        }
        ```
    *   **Success Response (201 Created):** (返回创建的 pipeline 对象)
*   **GET (List Pipelines):**
    *   **Query Parameters:** `page`, `per_page`, `is_active`
    *   **Success Response (200 OK):** (分页结构)
*   **Error Response:** `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`

*   **Endpoint:** `/kg-pipelines/{pipeline_id}`
*   **Method:** `GET`, `PUT`, `DELETE`
*   **Authentication:** Required. Role for PUT/DELETE: `editor`, `admin` (或创建者).
*   **Success Response:** `200 OK` (GET, PUT), `204 No Content` (DELETE)
*   **Error Response:** `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

*   **Endpoint:** `/kg-pipelines/{pipeline_id}/run`
*   **Method:** `POST`
*   **Description:** 手动触发一次流程执行。
*   **Authentication:** Required. Role: `editor`, `admin`.
*   **Success Response (202 Accepted):** (表示任务已接受处理，不代表立即完成)
    ```json
    {
      "message": "Pipeline run triggered successfully.",
      "run_id": 123 // ID of the kg_pipeline_runs record
    }
    ```
*   **Error Response:** `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict` (如果已有活动运行)

---

**5. 知识图谱构建任务/数据编排规则 (Knowledge Graph Pipeline Tasks)**

*   **Endpoint:** `/kg-pipelines/{pipeline_id}/tasks`
*   **Method:** `POST`, `GET`
*   **Authentication:** Required.
*   **POST (Create Task):**
    *   Role: `editor`, `admin`.
    *   **Request Body:**
        ```json
        {
          "task_order": 1,
          "task_name": "Map Customers to Node",
          "source_data_source_id": 1,
          "source_entity_identifier": "customers_table",
          "mapping_type": "node", // "node" or "relationship"
          "target_label_or_type": "Customer",
          "field_mappings": {
            "customer_id": {"target_property": "id", "is_primary_key": true},
            "name": {"target_property": "name"},
            "email": {"target_property": "email"}
          },
          "is_enabled": true
        }
        ```
    *   **Success Response (201 Created):** (返回创建的 task 对象)
*   **GET (List Tasks for a Pipeline):**
    *   **Success Response (200 OK):** (返回任务列表)
*   **Error Response:** `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found` (pipeline_id)

*   **Endpoint:** `/kg-pipelines/{pipeline_id}/tasks/{task_id}`
*   **Method:** `GET`, `PUT`, `DELETE`
*   **Authentication:** Required. Role for PUT/DELETE: `editor`, `admin`.
*   **Success Response:** `200 OK` (GET, PUT), `204 No Content` (DELETE)
*   **Error Response:** `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

---

**6. 知识图谱构建流程执行记录 (Knowledge Graph Pipeline Runs)**

*   **Endpoint:** `/kg-pipeline-runs`
*   **Method:** `GET`
*   **Description:** 获取所有流程执行记录 (支持过滤)。
*   **Authentication:** Required.
*   **Query Parameters:** `page`, `per_page`, `pipeline_id`, `status`, `triggered_by_user_id`
*   **Success Response (200 OK):** (分页结构)

*   **Endpoint:** `/kg-pipeline-runs/{run_id}`
*   **Method:** `GET`
*   **Description:** 获取特定流程执行记录详情 (包括其下的任务执行记录)。
*   **Authentication:** Required.
*   **Success Response (200 OK):**
    ```json
    {
      "id": 123,
      "pipeline_id": 1,
      "status": "success",
      "start_time": "...",
      "end_time": "...",
      "tasks": [
        {
          "task_id": 1,
          "task_name": "Map Customers to Node",
          "status": "success",
          "input_record_count": 1000,
          "output_record_count": 1000
        }
        // ...
      ]
    }
    ```
*   **Error Response:** `401 Unauthorized`, `404 Not Found`

*   **Endpoint:** `/kg-pipeline-runs/{run_id}/cancel` (可选)
*   **Method:** `POST`
*   **Description:** 尝试取消正在运行的流程。
*   **Authentication:** Required. Role: `editor`, `admin`.
*   **Success Response (200 OK):**
    ```json
    {
      "message": "Cancellation request sent."
    }
    ```
*   **Error Response:** `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict` (如果流程已结束或不可取消)

---

**7. 智能问答与查询日志 (Intelligent Q&A and Query Logs)**

*   **Endpoint:** `/query/nl2sql`
*   **Method:** `POST`
*   **Description:** 提交自然语言问题，获取生成的SQL和/或查询结果。
*   **Authentication:** Required.
*   **Request Body:**
    ```json
    {
      "natural_language_query": "显示北京地区所有销售额大于10000的客户",
      "target_data_source_id": 2, // 目标关系型数据源ID
      "session_id": "optional_session_id_for_context",
      "execute_sql": true // 是否在生成SQL后立即执行并返回结果
    }
    ```
*   **Success Response (200 OK):**
    ```json
    {
      "log_id": 50, // query_logs.id
      "natural_language_query": "显示北京地区所有销售额大于10000的客户",
      "generated_sql": "SELECT name, sales_amount FROM customers WHERE region = '北京' AND sales_amount > 10000;",
      "sql_execution_status": "success", // if execute_sql was true
      "query_result": { // if execute_sql was true and successful
        "columns": ["name", "sales_amount"],
        "rows": [
          ["客户A", 12000],
          ["客户B", 15000]
        ]
      },
      "execution_time_ms": 150 // if execute_sql was true
    }
    ```
*   **Error Response:** `400 Bad Request`, `401 Unauthorized`, `404 Not Found` (target_data_source_id), `500 Internal Server Error` (LLM 或数据库错误)

*   **Endpoint:** `/query-logs`
*   **Method:** `GET`
*   **Description:** 获取用户查询日志 (支持分页和过滤)。
*   **Authentication:** Required. (管理员可查看所有，普通用户仅查看自己的)
*   **Query Parameters:** `page`, `per_page`, `user_id`, `data_source_id`, `start_date`, `end_date`
*   **Success Response (200 OK):** (分页结构)

*   **Endpoint:** `/query-logs/{log_id}`
*   **Method:** `GET`
*   **Description:** 获取特定查询日志详情。
*   **Authentication:** Required.
*   **Success Response (200 OK):** (返回单个日志对象)

*   **Endpoint:** `/query-logs/{log_id}/feedback`
*   **Method:** `POST`
*   **Description:** 用户对某次查询结果提交反馈。
*   **Authentication:** Required.
*   **Request Body:**
    ```json
    {
      "rating": 5, // 1-5
      "comment": "这个结果非常准确！"
    }
    ```
*   **Success Response (200 OK):**
    ```json
    {
      "message": "Feedback submitted successfully."
    }
    ```
*   **Error Response:** `400 Bad Request`, `401 Unauthorized`, `404 Not Found`

---

**8. 数据库元数据 (DB Schema Metadata)**

*   **Endpoint:** `/db-schema-metadata/data-sources/{source_id}/sync`
*   **Method:** `POST`
*   **Description:** 针对指定的关系型数据源，同步（刷新）其表结构元数据。
*   **Authentication:** Required. Role: `editor`, `admin`.
*   **Success Response (202 Accepted):**
    ```json
    {
      "message": "Schema metadata synchronization initiated for data source ID: X"
    }
    ```
*   **Error Response:** `401 Unauthorized`, `403 Forbidden`, `404 Not Found` (source_id), `400 Bad Request` (如果数据源类型不适用)

*   **Endpoint:** `/db-schema-metadata/data-sources/{source_id}`
*   **Method:** `GET`
*   **Description:** 获取指定数据源的表结构元数据。
*   **Authentication:** Required.
*   **Query Parameters:** `table_name`, `column_name` (用于过滤)
*   **Success Response (200 OK):**
    ```json
    {
      "items": [
        {
          "id": 1,
          "data_source_id": 2,
          "db_name": "prod_db",
          "table_name": "customers",
          "column_name": "customer_id",
          "data_type": "INT",
          "is_primary_key": true,
          "column_description": "客户的唯一标识符",
          "sample_values": [101, 102, 103],
          "last_refreshed_at": "..."
        }
        // ... other columns and tables
      ]
      // ...分页元数据 (如果支持分页)
    }
    ```
*   **Error Response:** `401 Unauthorized`, `404 Not Found`

*   **Endpoint:** `/db-schema-metadata/{metadata_id}`
*   **Method:** `PUT`
*   **Description:** 更新单个列的元数据描述 (例如，业务含义、语义标签)。
*   **Authentication:** Required. Role: `editor`, `admin`.
*   **Request Body:**
    ```json
    {
      "column_description": "Updated business meaning for this column.",
      "semantics_tags": ["PII", "Identifier"],
      "sample_values": [1, 2, 3, "N/A"]
    }
    ```
*   **Success Response (200 OK):** (返回更新后的 metadata 对象)
*   **Error Response:** `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

---

**9. LLM 提示词管理 (LLM Prompts - 可选)**

*   **Endpoint:** `/llm-prompts`
*   **Method:** `POST`, `GET`
*   **Authentication:** Required. Role: `admin`.
*   **POST Request Body:**
    ```json
    {
      "prompt_name": "nl2sql_customer_domain_v3",
      "prompt_template": "Translate the following natural language question about customer data into SQL: \nQuestion: {{nl_question}}\nSchema: {{schema_info}}\nSQL:",
      "version": "3.0",
      "description": "Optimized prompt for customer domain queries.",
      "is_active": true
    }
    ```
*   **Success Response:** `201 Created` (POST), `200 OK` (GET with list)

*   **Endpoint:** `/llm-prompts/{prompt_id}`
*   **Method:** `GET`, `PUT`, `DELETE`
*   **Authentication:** Required. Role: `admin`.
*   **Success Response:** `200 OK` (GET, PUT), `204 No Content` (DELETE)

---

这份API设计文档涵盖了核心功能。在实际开发中，可能还需要根据具体需求进行调整和补充，例如更细致的权限控制接口、系统配置接口等。
