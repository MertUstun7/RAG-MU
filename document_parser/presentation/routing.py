import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import Form, File, UploadFile
from fastapi.routing import APIRouter
import uuid

from document_parser.business_logic.document_extractor import PageBasedExtractor
from config import logger
from vector_database.business_logic.vector_database_operations import VectorDb

UPLOAD_DIR = Path("temp_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
content_extractor=APIRouter()
@content_extractor.post("/content-extractor")
async def file_extractor(collection_name: str = Form(""),
    files: Optional[List[UploadFile]] = File(None),
    urls: List[str]=Form([])
):
    UPLOAD_DIR = Path("temp_uploads")
    UPLOAD_DIR.mkdir(exist_ok=True)
    saved_paths = []
    try:
        if files is not None:
            for file in files:
                ext = Path(file.filename).suffix
                temp_path = UPLOAD_DIR / f"{uuid.uuid4()}{ext}"

                with open(temp_path, "wb") as f:
                    f.write(await file.read())

                saved_paths.append(str(temp_path))
        all_inputs = saved_paths + urls

        extractor = PageBasedExtractor(UPLOAD_DIR)
        rag_data = extractor.process_document(all_inputs)
        VectorDb(collection_name).add_documents(rag_data)

        return {"OK":200, "inputs":all_inputs}

    finally:
            try:
               shutil.rmtree("./temp_uploads",ignore_errors=True)
            except Exception as e:
                logger.error("Error deleting folder->{e}".format(e=e))
