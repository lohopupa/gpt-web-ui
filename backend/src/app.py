import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, File, UploadFile, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from models import add_file
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
    

@app.post("/api/upload_files")
async def upload_files(category: str, files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    save_directory = Path(f"/tmp/{category}")
    save_directory.mkdir(parents=True, exist_ok=True)

    saved_files = []
    for file in files:
        file_path = save_directory / file.filename
        with file_path.open("wb") as f:
            content = await file.read()
            f.write(content)
        saved_files.append(str(file_path))
    return "Done!"
    results = []
    for file in files:
        try:
            result = await add_file(file, category, db)
            results.append(result)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process file {file.filename}: {str(e)}")
    
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
    return [*ollama.USING_MODELS, "openai_chatgpt"] 

@app.get("/api/categories")
async def list_categories(db: Session = Depends(get_db)):
    return [i.category for i in db.query(database.File).distinct(database.File.category).all()]