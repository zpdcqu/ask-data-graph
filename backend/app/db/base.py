from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Import all models here to ensure they are registered with SQLAlchemy Base
from app.db.models.user_models import User # Example
from app.db.models.data_source_models import DataSource 
from app.db.models.kg_pipeline_models import KGPipeline, KGPipelineTask, KGPipelineRun 