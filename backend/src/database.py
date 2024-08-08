from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os


db_host = os.getenv('POSTGRES_HOST')
db_port = os.getenv('POSTGRES_PORT')
db_dbname = os.getenv('POSTGRES_DB')
db_username = os.getenv('POSTGRES_USER')
db_password = os.getenv('POSTGRES_PASSWORD')

DATABASE_URL = f"postgresql+psycopg2://{db_username}:{db_password}@{db_host}:{db_port}/{db_dbname}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class File(Base):
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(Text, nullable=False, unique=True)
    category = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    
    embeddings = relationship("Embedding", back_populates="file")

class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer,  ForeignKey("files.id"), nullable=False)
    embedding = Column(LargeBinary, nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_id = Column(Integer, nullable=False)
    
    file = relationship("File", back_populates="embeddings")

def create_embeddings_table():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()