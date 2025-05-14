#!/usr/bin/env python
"""
知识图谱智能问答系统 - 后端服务启动脚本
"""
import uvicorn
import sys
import os
from app.core.config import settings  # 导入配置，这会加载service_config.yaml


def run_server():
    """
    启动FastAPI服务器，使用service_config.yaml中的配置
    """
    print(f"启动服务: 主机={settings.SERVICE_HOST}, 端口={settings.SERVICE_PORT}")
    uvicorn.run(
        "app.main:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        workers=settings.SERVICE_WORKERS,
        log_level=settings.SERVICE_LOG_LEVEL,
        reload=True  # 开发模式下启用自动重载
    )


if __name__ == "__main__":
    # 在启动前确保工作目录设置为backend/
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    
    try:
        print("==============================================")
        print("知识图谱智能问答系统 - 后端服务")
        print("==============================================")
        run_server()
    except KeyboardInterrupt:
        print("\n服务已停止")
        sys.exit(0)
    except Exception as e:
        print(f"启动服务时出错: {e}")
        sys.exit(1) 