import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
load_dotenv()

res=os.getenv("DB_URL")==None
engine=create_engine(os.getenv("DB_URL"))
Session = sessionmaker(bind=engine)

