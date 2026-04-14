from typing import List

from fastapi import APIRouter

from vector_database.business_logic.vector_database_operations import VectorDb

vector_db_router=APIRouter()
@vector_db_router.post("/ingestion")
async def ingestion(collection_name:str,documents:List[dict]):
    return VectorDb(collection_name).add_documents(documents)
