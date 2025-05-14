from pydantic import validator, AnyHttpUrl
from pydantic_settings import BaseSettings
from typing import List, Optional, Dict, Any
from pydantic import EmailStr
import os
import yaml
import pathlib

# 获取项目根目录
ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# 加载YAML配置文件
yaml_config: Dict[str, Any] = {}
yaml_path = os.path.join(ROOT_DIR, "service_config.yaml")

if os.path.exists(yaml_path):
    try:
        with open(yaml_path, "r", encoding="utf-8") as yaml_file:
            yaml_config = yaml.safe_load(yaml_file)
        print(f"已加载配置文件：{yaml_path}")
    except Exception as e:
        print(f"加载配置文件失败: {e}")
else:
    print(f"配置文件不存在: {yaml_path}")


# 从YAML配置中获取值的辅助函数，支持嵌套键
def get_yaml_value(key_path: str, default: Any = None) -> Any:
    """
    从YAML配置中获取值，支持使用点号分隔的嵌套键
    例如: get_yaml_value('database.host')
    """
    if not yaml_config:
        return default
    
    keys = key_path.split('.')
    value = yaml_config
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    return value


class Settings(BaseSettings):
    PROJECT_NAME: str = get_yaml_value('project.name', "知识图谱智能问答系统")
    API_V1_STR: str = get_yaml_value('project.api_version', "/api/v1")
    
    # Security
    SECRET_KEY: str = get_yaml_value('security.secret_key', "your_super_secret_key_here_please_change_me")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = get_yaml_value('security.access_token_expire_minutes', 60 * 24 * 8) # 8 days
    ALGORITHM: str = get_yaml_value('security.algorithm', "HS256")

    # Database (MySQL)
    DB_HOST: str = get_yaml_value('database.host', "localhost")
    DB_PORT: int = get_yaml_value('database.port', 3306)
    DB_USER: str = get_yaml_value('database.user', "root")
    DB_PASSWORD: str = get_yaml_value('database.password', "password")
    DB_NAME: str = get_yaml_value('database.name', "kg_app_db")
    DATABASE_URL: Optional[str] = get_yaml_value('database.url', None)

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        
        # 优先使用PyMySQL驱动，因为它是纯Python实现，更容易安装
        driver = "mysql+pymysql"  # 默认使用pymysql
        
        # 检查是否安装了pymysql
        try:
            import pymysql
            print("使用PyMySQL作为MySQL驱动")
        except (ImportError, ModuleNotFoundError):
            # 如果没有安装pymysql，尝试使用mysqlclient
            try:
                import MySQLdb
                driver = "mysql+mysqlclient"
                print("使用mysqlclient作为MySQL驱动")
            except (ImportError, ModuleNotFoundError):
                print("警告: 未找到MySQL驱动 (mysqlclient 或 pymysql)，将尝试使用pymysql，请确保已安装")
        
        return f"{driver}://{values.get('DB_USER')}:{values.get('DB_PASSWORD')}@{values.get('DB_HOST')}:{values.get('DB_PORT')}/{values.get('DB_NAME')}"

    # OpenAI API Key
    OPENAI_API_KEY: Optional[str] = get_yaml_value('openai.api_key', None)

    # Nebula Graph
    NEBULA_GRAPH_HOST: str = get_yaml_value('nebula_graph.host', "localhost")
    NEBULA_GRAPH_PORT: int = get_yaml_value('nebula_graph.port', 9669)
    NEBULA_USER: str = get_yaml_value('nebula_graph.user', "root")
    NEBULA_PASSWORD: str = get_yaml_value('nebula_graph.password', "nebula")
    NEBULA_SPACE_NAME: str = get_yaml_value('nebula_graph.space_name', "knowledge_graph")
    NEBULA_VIS_DEFAULT_NEIGHBOR_LIMIT: int = get_yaml_value('nebula_graph.vis_default_neighbor_limit', 25)

    # First Superuser
    FIRST_SUPERUSER_USERNAME: str = get_yaml_value('first_superuser.username', "admin")
    FIRST_SUPERUSER_EMAIL: EmailStr = get_yaml_value('first_superuser.email', "admin@example.com")
    FIRST_SUPERUSER_PASSWORD: str = get_yaml_value('first_superuser.password', "adminpassword")

    # Service settings
    SERVICE_HOST: str = get_yaml_value('service.host', "0.0.0.0")
    SERVICE_PORT: int = get_yaml_value('service.port', 8000)
    SERVICE_WORKERS: int = get_yaml_value('service.workers', 4)
    SERVICE_LOG_LEVEL: str = get_yaml_value('service.log_level', "info")

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# 打印关键配置信息（不包括敏感信息）
print(f"项目名称: {settings.PROJECT_NAME}")
print(f"数据库连接: mysql+mysqlclient://{settings.DB_USER}:***@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
print(f"Nebula图数据库: {settings.NEBULA_GRAPH_HOST}:{settings.NEBULA_GRAPH_PORT}/{settings.NEBULA_SPACE_NAME}") 