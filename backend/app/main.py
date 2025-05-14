from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import engine, get_db # Import get_db
from app.db import base # Import base to create tables
from app.db.nebula_connector import init_nebula_connection_pool, close_nebula_connection_pool # Add these
from app.api.v1.endpoints import ( # Using parenthesis for multi-line import
    auth_endpoints,
    data_source_endpoints,
    kg_pipeline_endpoints,
    kg_pipeline_task_endpoints,
    kg_pipeline_run_endpoints,
    data_sources
)
from app.crud import crud_user
from app.api.v1.schemas import user_schemas

# Import the new router
from app.api.v1.endpoints import kg_visualization_endpoints

# Create DB tables if they don't exist
# This is a simple way for development. For production, use Alembic migrations.
base.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for the Intelligent Q&A System with Knowledge Graph features.",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源（开发环境）
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有头
)

@app.on_event("startup")
async def on_startup():
    # Create a temp DB session for startup tasks
    # This is a simplified way. In a real app, you might use a script or a management command.
    db: Session = next(get_db()) # Get a session
    try:
        # Check if admin user exists
        admin_user = crud_user.get_user_by_username(db, username=settings.FIRST_SUPERUSER_USERNAME if hasattr(settings, 'FIRST_SUPERUSER_USERNAME') else "admin")
        if not admin_user:
            user_in = user_schemas.UserCreate(
                username=settings.FIRST_SUPERUSER_USERNAME if hasattr(settings, 'FIRST_SUPERUSER_USERNAME') else "admin",
                email=settings.FIRST_SUPERUSER_EMAIL if hasattr(settings, 'FIRST_SUPERUSER_EMAIL') else "admin@example.com",
                password=settings.FIRST_SUPERUSER_PASSWORD if hasattr(settings, 'FIRST_SUPERUSER_PASSWORD') else "adminpassword"
            )
            crud_user.create_user(db=db, user=user_in, role="admin")
            print("Admin user created")
        else:
            print("Admin user already exists")
        init_nebula_connection_pool() # Initialize Nebula pool
    finally:
        db.close()

@app.on_event("shutdown")
async def on_shutdown(): # Add shutdown event
    await close_nebula_connection_pool() # Close Nebula pool

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": f"Welcome to the {settings.PROJECT_NAME} API"}

app.include_router(auth_endpoints.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Auth"])
app.include_router(data_sources.router, prefix=f"{settings.API_V1_STR}/data-sources", tags=["Data Sources"])
app.include_router(kg_pipeline_endpoints.router, prefix=f"{settings.API_V1_STR}/kg-pipelines", tags=["KG Pipelines"])
app.include_router(kg_pipeline_task_endpoints.router, prefix=f"{settings.API_V1_STR}/kg-pipeline-tasks", tags=["KG Pipeline Tasks"])
app.include_router(kg_pipeline_run_endpoints.router, prefix=f"{settings.API_V1_STR}/kg-pipeline-runs", tags=["KG Pipeline Runs"])

# Add the new KG Visualization router
app.include_router(
    kg_visualization_endpoints.router, 
    prefix=f"{settings.API_V1_STR}/visualize", 
    tags=["KG Visualization"]
)

# Mount task router under specific pipeline
# Note: This way of including routers for nested paths is a bit verbose.
# For more complex nesting, FastAPI-Utils or other patterns might be cleaner.
# However, for one level of nesting, it's direct.
# The {pipeline_id} path parameter in kg_pipeline_task_endpoints will be captured.
app.include_router(
    kg_pipeline_task_endpoints.router,
    prefix=f"{settings.API_V1_STR}/kg-pipelines/{{pipeline_id}}/tasks",
    tags=["KG Pipeline Tasks"]
)

app.include_router(
    kg_pipeline_run_endpoints.router,
    prefix=f"{settings.API_V1_STR}/kg-pipeline-runs",
    tags=["KG Pipeline Runs"]
)

# TODO: Add other routers (NL2SQL, DB Schema etc.)

# if __name__ == "__main__": # This part is usually not needed when using uvicorn directly from CLI
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000) 