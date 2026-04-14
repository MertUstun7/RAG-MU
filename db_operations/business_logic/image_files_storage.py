import re
from contextlib import contextmanager
from typing import List
from pathlib import Path

from sqlalchemy import or_
from starlette.responses import JSONResponse
from db_operations.business_logic.db_tables import Image
from image_captioning.business_logic.qwen_image_captioning import ImageCaption


class ImageRepository:
    def __init__(self,session_factory):
        self.Session=session_factory

    @contextmanager
    def _get_session(self):
        session=self.Session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()


    def add_image_to_db(self, image_paths:List):
        captioner=ImageCaption()
        with self._get_session() as session:
            try:
                for image_path in image_paths:
                    with open(image_path, 'rb') as image_file:
                        binary_image=image_file.read()
                    context=captioner.get_caption(image_path)
                    image=Image(
                        doc_name=Path(image_path).name,
                        context=context,
                        image=binary_image,
                        page_number=re.search(r"_p(\d+)",Path(image_path).name).group(1)
                    )
                    session.add(image)
                    print("Successful: Image has been added to database")
                return JSONResponse(content={"message":"success"},status_code=200)
            except Exception as e:
                print(f"Error: {e}")

    def get_images_to_db(self, image_names:List[str]):

        with self._get_session() as session:
            rows=session.query(Image).filter(or_(*[Image.doc_name.like(f"{name}%")for name in image_names])).all()

            results=[]
            for row in rows:
                results.append({
                    "image":bytes(row.image) if not isinstance(row.image, bytes) else row.image,
                    "context":row.context,
                })
                print(row.context)

        return results










