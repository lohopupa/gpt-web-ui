from fastapi import FastAPI, HTTPException, Request, File, UploadFile, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from files_processing import exctract_text_from_file
from mdoels import add_file, query_model
from database import create_embeddings_table, get_db
from ollama import load_models
import ollama
import logging
from app_types import *
import database

app = FastAPI()
log = logging.Logger(name="ollama", level=10).info

@app.on_event("startup")
async def startup_event():
    create_embeddings_table()
    load_models()
    

@app.post("/api/upload_file")
async def upload_file(category: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    filename = file.filename
    try:
        text = await exctract_text_from_file(file)
        return add_file(filename, text, category, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate")
async def generate(request: GenerateRequest, db: Session = Depends(get_db)):
    if request.model in ollama.USING_MODELS:
        return ollama.generate(request, db)
    raise HTTPException(status_code=500, detail="NOT IMPLEMENTED")

@app.post("/api/predict_file")
async def generate(request: GenerateRequest, db: Session = Depends(get_db)):
    if request.model in ollama.USING_MODELS:
        doc_id = ollama.find_document(request.query, request.categories, db)
        data = db.query(database.File).filter(database.File.id == doc_id).first()
        return data.filename
    raise HTTPException(status_code=500, detail="NOT IMPLEMENTED")

@app.get("/api/models")
async def list_models():
    return ollama.USING_MODELS # + gpt


@app.get("/api/categories")
async def list_categories():
    pass