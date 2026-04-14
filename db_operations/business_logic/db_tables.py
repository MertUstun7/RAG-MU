from sqlalchemy import Column, Integer, String, LargeBinary, Text
from sqlalchemy.orm import declarative_base

Base=declarative_base()

class Image(Base):
    __tablename__ = "images"
    id=Column(Integer, primary_key=True)
    doc_name=Column(String(255),nullable=False)
    context=Column(Text)
    image=Column(LargeBinary,nullable=False)
    page_number=Column(Integer,nullable=False)

    def __repr__(self):
        return f"<Image id={self.id} doc_name={self.doc_name}>"