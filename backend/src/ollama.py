import json
from fastapi import HTTPException
import numpy as np
from sqlalchemy.orm import Session
from database import Embedding, File
from files_processing import split_docs
import requests
from helpers import retry
from app_types import *
from sqlalchemy import or_
from sklearn.metrics.pairwise import cosine_similarity


EMBED_MODEL_NAME = "mxbai-embed-large"
#OLLAMA_HOST = "http://ollama:11434/api"
# OLLAMA_HOST = "http://speccy49home.ddns.net:11434/api"
OLLAMA_HOST = "http://192.168.0.11:11434/api"
USING_MODELS = ["llama3.1:8b"]

def upload_file(filename, file_content, category, db: Session) -> str | None:
    if file_exists(filename=filename, db=db):
        return "File already exists"
    file = File(
        filename=filename,
        category=category,
        content=file_content,
    )
    try:
        db.add(file)
        db.commit()
        db.refresh(file)
    except:
        return "File already exists" # ОШИБКА ГОВНО
    chunks = split_docs(document_text=file_content+"", chunk_size=500, chunk_overlap=20)
    for chunk_id, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        embedding_array = np.array(embedding, dtype=np.float32)
        embedding_bytes = embedding_array.tobytes()
        emb = Embedding(
            file_id = file.id,
            embedding = embedding_bytes,
            chunk_text = chunk,
            chunk_id = chunk_id
        )
        db.add(emb)
    db.commit()
    return None

def generate(request: GenerateRequest, db: Session):
    prompt_template = """Используя эту информацию {data}
        Ответь на этот вопрос '{query}'.
        Не придумывай факты, используй только ту информацию, которая тебе дана.
        Если ты не знаешь ответа, так об этом и скажи.
        ОТВЕТ ДОЛЖЕН БЫТЬ ИСКЛЮЧИТЕЛЬНО НА РУССКОМ ЯЗЫКЕ!
    """

    # doc_id = find_document(request.query, request.categories, db)

    # data = db.query(File).filter(File.id == doc_id).first().content
    query_embedding = get_embedding(request.query)
    embeddings = load_embeddings_from_db(request.categories, db)
    file_id, chunk_id = find_best_match_cosine(query_embedding, embeddings)
    delta = request.delta or 50
    embs = db.query(Embedding).filter(Embedding.file_id == file_id).filter(Embedding.chunk_id >= chunk_id - delta).filter(Embedding.chunk_id <= chunk_id + delta).all()
    data = " ".join([e.chunk_text for e in embs])
    prompt = prompt_template.format(data=data, query=request.query)
    filename = db.query(File).filter(File.id == file_id).first().filename
    body = {
        "model": request.model,
        "prompt": prompt.encode().decode("utf-8"),
        "stream": False,
        "options": {
            "num_ctx": request.n_ctx or None
        }
    }
    with open("/tmp/request.json", "w") as f:
        json.dump(body, f)
    resp = requests.post(OLLAMA_HOST + "/generate", json=body)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()["response"] + "\n" + filename

def find_document(query: str, categories: list[str], db: Session):
    query_embedding = get_embedding(query)
    embeddings = load_embeddings_from_db(categories, db)
    bayes_model = create_naive_bayes_model(embeddings)
    return naive_bayes_predict(query_embedding, bayes_model)

    

from sklearn.naive_bayes import GaussianNB

def create_naive_bayes_model(embeddings: list[Embedding]):
    embedding_vectors = np.array(
        [
            np.frombuffer(e.embedding, dtype=np.float32) for e in embeddings
        ], 
        dtype=np.float32)
    labels = np.array([e.file_id for e in embeddings])
    nb_model = GaussianNB()
    nb_model.fit(embedding_vectors, labels)
    return nb_model

def naive_bayes_predict(query_embedding, nb_model):
    query_embedding_array = np.array([query_embedding], dtype=np.float32)
    predicted_label = nb_model.predict(query_embedding_array)[0]
    return int(predicted_label)
    
def find_best_match_cosine(query_embedding, embeddings: list[Embedding]):
    # best_match = None
    # highest_similarity = -1
    
    # query_embedding_array = np.array([query_embedding], dtype=np.float32)
    
    # for e in embeddings:
    #     embedding_array = np.array([np.frombuffer(e.embedding, dtype=np.float32)])
    #     similarity = cosine_similarity(query_embedding_array, embedding_array)[0][0]
    #     if similarity > highest_similarity:
    #         highest_similarity = similarity
    #         best_match = (e.file_id, e.chunk_id)
    
    # return best_match
    list_of_embeddings = [np.frombuffer(e.embedding, dtype=np.float32) for e in embeddings]
    similarities = cosine_similarity([query_embedding], list_of_embeddings)[0]
    
    # Get the indices of the embeddings sorted by similarity (highest first)
    closest_id = np.argsort(similarities)[::-1][0]
    
    # Retrieve the top N closest embeddings
    closest_embedding = embeddings[closest_id]

    return closest_embedding.file_id, closest_embedding.chunk_id
    
def load_embeddings_from_db(categories: list[str], db: Session):
    if len(categories) == 0:
        return db.query(Embedding)
    return db.query(Embedding).filter(or_(Embedding.file.has(File.category == category) for category in categories))

def list_models():
    query_url = OLLAMA_HOST + "/tags"
    response = requests.get(query_url)
    return [m["name"] for m in response.json()["models"]]
    

def load_model(model_name):
    query_url = OLLAMA_HOST + "/pull"
    response = requests.post(query_url, json={"name": model_name})
    if response.status_code == 200:
        print(f"Successfully loaded model: {model_name}")
    else:
        print(f"Failed to load model: {model_name}, Status Code: {response.status_code}, Response: {response.text}")

def load_models():
    installed_models = list_models()
    for model in [*USING_MODELS, EMBED_MODEL_NAME]:
        if model in installed_models:
            print(f"Model {model} already installed!")
        else:
            load_model(model)

def file_exists(filename, db: Session):
    return db.query(File).filter(File.filename == filename).count() > 0

def get_embedding(text):
    resp = embeddings_request(text)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()["embeddings"][0]


@retry()
def embeddings_request(text):
    body = {
        "model": EMBED_MODEL_NAME,
        "input": text
    }
    return requests.post(OLLAMA_HOST + "/embed", json=body)
