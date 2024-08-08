from fastapi import FastAPI, HTTPException, Request, File, UploadFile, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.src.models import add_file, query_model
from database import create_embeddings_table, get_db
from ollama import load_models
import ollama
import openai_gpt
import logging
from app_types import *
import database
from typing import List


app = FastAPI()
log = logging.Logger(name="ollama", level=10).info

@app.on_event("startup")
async def startup_event():
    create_embeddings_table()
    load_models()
    

@app.post("/api/upload_file")
async def upload_file(category: str, files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    results = []
    for file in files:
        filename = file.filename
        try:
            result = add_file(filename, file, category, db)
            results.append(result)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process file {filename}: {str(e)}")
    
    return {"results": results}


@app.post("/api/generate")
async def generate(request: GenerateRequest, db: Session = Depends(get_db)):
    if request.model in ollama.USING_MODELS:
        return ollama.generate(request, db)
    elif request.model == "openai_chatgpt":
        return openai_gpt.generate(request)
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


@app.get("/api/test")
async def test():
    return {"result": "HELLO WORLD"}


@app.get("/api/categories")
async def list_categories():
    pass #SELECT DISTINCT category from embeddings;