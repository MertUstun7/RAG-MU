from typing import List

from docling.document_converter import DocumentConverter
from docling.document_extractor import DocumentExtractor
from fastapi.routing import APIRouter

from document_parser.business_logic.document_extractor import PageBasedExtractor
from rag_engine.business_logic.models import ModelCollection
from rag_engine.business_logic.semantic_answer import SemanticAnswer

llm_router=APIRouter()

@llm_router.post("/llm-result")
async def generate_llm_result(query: str,collection_name:str="",model:str="llama3.1:8b"):
    llm_res = SemanticAnswer(collection_name=collection_name,model=model)

    response = llm_res.rag_llm_results(query)

    return response

@llm_router.get("/llm-models")
async def pull_llm_models():

    models=ModelCollection.get_local_models()
    return models