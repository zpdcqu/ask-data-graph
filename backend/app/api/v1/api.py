from fastapi import APIRouter

from app.api.v1.endpoints import data_sources, db_metadata, er_diagrams

api_router = APIRouter()
api_router.include_router(data_sources.router, prefix="/data-sources", tags=["data-sources"])
api_router.include_router(db_metadata.router, prefix="/db-schema-metadata", tags=["db-schema-metadata"])
api_router.include_router(er_diagrams.router, prefix="/er-diagrams", tags=["er-diagrams"]) 