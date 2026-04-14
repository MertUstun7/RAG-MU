from typing import List
from fastapi import APIRouter

from db_operations.business_logic.db import Session
from db_operations.business_logic.image_files_storage import ImageRepository

image_caption_router=APIRouter()


@image_caption_router.post("/image-db")

async def image_add_db(image_paths:List[str]):
    res=ImageRepository(Session).add_image_to_db(image_paths)
    return res

