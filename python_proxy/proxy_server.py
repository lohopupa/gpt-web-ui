import os
import time
import json
import requests
import psycopg2
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from pdf_helper import *
from test_searches import *
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}) 

TARGET_HOST = os.getenv("TARGET_HOST")
EMBED_MODEL_NAME = "mxbai-embed-large" # "llama3.1:8b" #"mxbai-embed-large" #"nomic-embed-text"

# import logging
# logging.basicConfig(level=logging.DEBUG)

MODEL_MAPPING_FILE = "model_mapping.json"
SAVED_DATA_PATH = "./saved_chats"

def get_db_connection():
    while True:
        try:
            connection = psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host="localhost",#os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT")
            )
            #print("Successfully connected to the database")
            return connection
        except psycopg2.OperationalError as e:
            print("Database connection failed. Retrying in 5 seconds...")
            time.sleep(5)

def create_embeddings_table():
    db_connection = get_db_connection()
    cursor = db_connection.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS embeddings (
        id SERIAL PRIMARY KEY,
        pdf_file TEXT NOT NULL,
        category TEXT,
        doc_id INTEGER NOT NULL,
        embedding BYTEA NOT NULL,
        chunk_text TEXT NOT NULL
    );
    """)
    db_connection.commit()
    cursor.close()
    db_connection.close()

def save_embeddings_to_db(embeddings, chunks, pdf_file, category, db_connection):
    cursor = db_connection.cursor()
    for doc_id, embedding in enumerate(embeddings):
        embedding_array = np.array(embedding, dtype=np.float32)
        embedding_bytes = embedding_array.tobytes()
        cursor.execute(
            "INSERT INTO embeddings (pdf_file, category, doc_id, embedding, chunk_text) VALUES (%s, %s, %s, %s, %s)",
            (pdf_file, category, doc_id, embedding_bytes, chunks[doc_id])
        )
    db_connection.commit()

# @app.route("/api/upload", methods=["POST"])
# def upload_file():
#     if 'file' not in request.files:
#         return jsonify({"error": "No file part"}), 400
#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({"error": "No selected file"}), 400
#     if 'category' not in request.form:
#         return jsonify({"error": "No category provided"}), 400
#     if file and file.filename.lower().endswith('.pdf'):
#         file_path = os.path.join('./tmp', file.filename)
#         file.save(file_path)
        
#         # # Загрузка и разбиение PDF
#         # docs = load_pdf_data(file_path=file_path)
#         # chunks = split_docs(documents=docs, chunk_size=8000,chunk_overlap=200)
        
#         data = load_pdf_data(file_path=file_path)
#         chunks = split_docs(document_text=data, chunk_size=500,chunk_overlap=100)

#         # Создание эмбеддингов
#         embeddings = []
#         emb_chunks = []
#         for chunk in chunks:
#             for _ in range(3):
#                 response = requests.post(
#                     f"{TARGET_HOST}/api/embed",
#                     json={"model": EMBED_MODEL_NAME, "input": chunk }#, "options": {"num_ctx": 4096}}
#                 )
#                 if response.status_code == 200:
#                     embeddings.extend(response.json()["embeddings"])
#                     emb_chunks.append(chunk)
#                     break
        
#         db_connection = get_db_connection()
#         save_embeddings_to_db(embeddings, emb_chunks, file_path, request.form['category'], db_connection)
#         db_connection.close()
        
#         return jsonify({"message": "File uploaded and embeddings created successfully"}), 200
#     else:
#         return jsonify({"error": "Invalid file type"}), 400

@app.route("/api/upload", methods=["POST"])
def upload_files():
    if 'files' not in request.files:
        return jsonify({"error": "No file part"}), 400

    files = request.files.getlist('files')
    category = request.form.get('category', None)

    # if not category:
    #     return jsonify({"error": "No category provided"}), 400

    if not files:
        return jsonify({"error": "No selected files"}), 400

    all_embeddings = []
    for file in files:
        if file.filename.lower().endswith('.pdf'):
            file_path = os.path.join('./tmp', file.filename)
            file.save(file_path)

            data = load_pdf_data(file_path=file_path)
            chunks = split_docs(document_text=data, chunk_size=500, chunk_overlap=200)

            embeddings = []
            emb_chunks = []
            for chunk in chunks:
                for _ in range(3):
                    response = requests.post(
                        f"{TARGET_HOST}/api/embed",
                        json={"model": EMBED_MODEL_NAME, "input": chunk}
                    )
                    if response.status_code == 200:
                        embeddings.extend(response.json()["embeddings"])
                        emb_chunks.append(chunk)
                        break
            
            db_connection = get_db_connection()
            save_embeddings_to_db(embeddings, emb_chunks, file_path, category, db_connection)
            db_connection.close()
            
            all_embeddings.append({"file": file.filename, "embeddings": embeddings})
        else:
            return jsonify({"error": f"Invalid file type for file {file.filename}"}), 400

    return jsonify({"message": "Files uploaded and embeddings created successfully", "files": all_embeddings}), 200

def load_chunks_delta(db_connection, chunk_id, filename, delta=10):
    cursor = db_connection.cursor()
    cursor.execute(
        "SELECT chunk_text FROM embeddings WHERE doc_id BETWEEN %s AND %s AND pdf_file = %s;",
        (chunk_id - delta, chunk_id + delta, filename)
    )
    rows = cursor.fetchall()
    combined_text = ' '.join(row[0] for row in rows)
    
    return combined_text


def load_embeddings_from_db(db_connection, categories):
    cursor = db_connection.cursor()
    #idk..
    if not isinstance(categories, list):
        raise ValueError("Categories must be a list")

    if not categories or (len(categories) == 1 and categories[0].lower() == 'any'):
        query = "SELECT pdf_file, doc_id, embedding FROM embeddings"
        params = ()
    else:
        placeholders = ', '.join(['%s'] * len(categories))
        query = f"SELECT pdf_file, doc_id, embedding FROM embeddings WHERE category IN ({placeholders})"
        params = tuple(categories)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    embeddings = []
    for row in rows:
        pdf_file, doc_id, embedding = row
        
        embedding_bytes = bytes(embedding)
        
        element_size = np.dtype(np.float32).itemsize
        num_elements = len(embedding_bytes) // element_size
        
        if len(embedding_bytes) % element_size != 0:
            #logging.error(f"Invalid embedding size: {len(embedding_bytes)} bytes")
            continue
        
        embedding_array = np.frombuffer(embedding_bytes, dtype=np.float32)
        
        if len(embedding_array) != num_elements:
            #logging.error(f"Mismatch in number of elements: expected {num_elements}, got {len(embedding_array)}")
            continue
        
        embeddings.append((pdf_file, doc_id, embedding_array))
    
    return embeddings

#?why do we have it here :D
# def find_best_match(query_embedding, embeddings):
#     best_match = None
#     highest_similarity = -1
    
#     query_embedding_array = np.array(query_embedding, dtype=np.float32).reshape(1, -1)
    
#     for pdf_file, doc_id, embedding in embeddings:
#         embedding_array = np.array(embedding, dtype=np.float32).reshape(1, -1)
#         similarity = cosine_similarity(query_embedding_array, embedding_array)[0][0]
#         if similarity > highest_similarity:
#             highest_similarity = similarity
#             best_match = (pdf_file, doc_id)
    
#     return best_match

@app.route("/api/generate", methods=["POST"])
def generate_response():
    data = request.get_json()
    print(data)
    model = data.get("model")
    query = data.get("prompt")
    categories = data.get("category", ["any"])
    n_ctx = int(data.get("n_ctx",8192))
    delta = int(data.get("delta",30))
    stream = data.get("stream", False)
    if not query or not model:
        return jsonify({"error": "Model and prompt are required"}), 400
    if not isinstance(categories, list):
        return jsonify({"error": "Category must be a list"}), 400

    try:
        response = requests.post(
            f"{TARGET_HOST}/api/embeddings",
            json={"model": EMBED_MODEL_NAME, "prompt": query, "options": {"num_ctx": 8192}}
        )
        if response.status_code == 200:
            query_embedding = response.json().get("embedding")
            if not query_embedding:
                return jsonify({"error": "No embedding returned from embedding API"}), 500
        else:
            return jsonify({"error": "Failed to create query embedding"}), response.status_code

        db_connection = get_db_connection()
        embeddings = load_embeddings_from_db(db_connection, categories)
        db_connection.close()

        best_match = ansemble(query_embedding, embeddings)
        file_path = best_match[0] if best_match else None
        doc_id = best_match[1] if best_match else None
        

        print(file_path)
        if file_path and (not doc_id is None):
            # Загрузка содержимого PDF
            # documents = read_pdf_data(file_path)
            # pdf_content = "\n".join(documents)  
            db_connection = get_db_connection()
            pdf_content = load_chunks_delta(filename=file_path, db_connection=db_connection, chunk_id=doc_id, delta=delta)
            db_connection.close()
            # Отправка запроса на Ollama API
            response = requests.post(
                f"{TARGET_HOST}/api/generate",
                json={
                    "model": model,
                    "prompt": f"Используя следующие данные: {pdf_content}. Ответь на запрос пользователя: {query}; Не придумывай факты, используй только ту информацию, которая тебе дана. Если ты не знаешь ответа, так об этом и скажи. ОТВЕТ ДОЛЖЕН БЫТЬ ИСКЛЮЧИТЕЛЬНО НА РУССКОМ ЯЗЫКЕ!",
                    "stream": stream,
                    "options": {
                        "num_ctx": n_ctx,
                    }
                },
                stream=True
            )

            def generate():
                buffer = ""
                for chunk in response.iter_content(chunk_size=1024):
                    buffer += chunk.decode("utf-8","ignore")
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        yield line + "\n"
                if buffer:
                    yield buffer

            content_type = response.headers.get("Content-Type", "text/plain")
            return Response(generate(), content_type=content_type)
        else:
            return jsonify({"error": "No matching file found"}), 404

    except Exception as e:
        #logging.error(f"Exception in generate_response: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    
@app.route("/api/testsearches", methods=["POST"])
def generate_test_searches():
    data = request.get_json()
    model = data.get("model")
    query = data.get("prompt")
    categories = data.get("category", ["any"])
    if not query or not model:
        return jsonify({"error": "Model and prompt are required"}), 400

    try:
        # Создание эмбеддинга для запроса пользователя
        response = requests.post(
            f"{TARGET_HOST}/api/embeddings",
            json={"model": EMBED_MODEL_NAME, "prompt": query}
        )
        if response.status_code == 200:
            query_embedding = response.json().get("embedding")
            if not query_embedding:
                return jsonify({"error": "No embedding returned from embedding API"}), 500
        else:
            return jsonify({"error": "Failed to create query embedding"}), response.status_code

        # Загрузка эмбеддингов из базы данных
        db_connection = get_db_connection()
        embeddings = load_embeddings_from_db(db_connection, categories)
        db_connection.close()

        results = {}

        # Косинусное сходство
        best_match_cosine = find_best_match_cosine(query_embedding, embeddings)
        results["cosine"] = {"file": best_match_cosine[0], "doc_id": best_match_cosine[1]}

        # kNN
        knn_model = create_knn_model(embeddings, metric="cosine")
        best_match_knn = find_best_match_knn(query_embedding, knn_model, embeddings)
        results["knn_cosine"] = {"file": best_match_knn[0], "doc_id": best_match_knn[1]}

        knn_model = create_knn_model(embeddings, metric="nan_euclidean")
        best_match_knn = find_best_match_knn(query_embedding, knn_model, embeddings)
        results["knn_nan_euclidean"] = {"file": best_match_knn[0], "doc_id": best_match_knn[1]}
        
        # kNN
        knn_model = create_knn_model(embeddings, metric="chebyshev")
        best_match_knn = find_best_match_knn(query_embedding, knn_model, embeddings)
        results["knn_chebyshev"] = {"file": best_match_knn[0], "doc_id": best_match_knn[1]}

        # kNN
        knn_model = create_knn_model(embeddings, metric="euclidean")
        best_match_knn = find_best_match_knn(query_embedding, knn_model, embeddings)
        results["knn_euclidean"] = {"file": best_match_knn[0], "doc_id": best_match_knn[1]}

        # FAISS
        faiss_index = create_faiss_index(embeddings)
        best_match_faiss = find_best_match_faiss(query_embedding, faiss_index, embeddings)
        results["faiss"] = {"file": best_match_faiss[0], "doc_id": best_match_faiss[1]}

        # Наивный Байесовский классификатор
        nb_model = create_naive_bayes_model(embeddings)
        best_match_naive_bayes = find_best_match_naive_bayes(query_embedding, nb_model, embeddings)
        results["naive_bayes"] = {"file": best_match_naive_bayes[0], "doc_id": best_match_naive_bayes[1]}

        return jsonify(results), 200

    except Exception as e:
        #logging.error(f"Exception in generate_response: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def proxy(path):
    method = request.method
    text_data = request.get_data(as_text=True)
    headers = {key: value for key, value in request.headers if key.lower() != "host"}

    #logging.debug(f"Received {method} request with data: {text_data} and headers: {headers}")

    model_mapping = load_model_mapping()

    if request.is_json:
        json_data = request.get_json()
        model_key = json_data.get("model")
        if model_key in model_mapping:
            json_data["model"] = model_mapping[model_key]
            data = json.dumps(json_data)
        #else:
            
            #logging.debug(f"Model key {model_key} not found in MODEL_MAPPING")
        save_chats_data(model_mapping[model_key], data)
        text_data = data

    try:
        response = requests.request(
            method, f"{TARGET_HOST}/{path}", data=text_data, stream=True
        )

        def generate():
            buffer = ""
            for chunk in response.iter_content(chunk_size=1024):
                buffer += chunk.decode("utf-8","ignore")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = remove_model_field_from_json(line)
                    yield line + "\n"
            if buffer:
                yield remove_model_field_from_json(buffer)

        content_type = response.headers.get("Content-Type", "text/plain")
        response_content = Response(generate(), content_type=content_type)

        return response_content
    except Exception as e:
        #logging.error(f"Exception while proxying request: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

@app.route("/api/tags", methods=["GET"])
def sync_models():
    response = requests.get(f"{TARGET_HOST}/api/tags")
    if response.status_code != 200:
        return (
            jsonify({"error": "Failed to retrieve model tags from target host"}),
            response.status_code,
        )

    remote_models = response.json().get("models", [])
    remote_model_names = [model["model"] for model in remote_models]

    updated_mapping = {}
    for i, model_name in enumerate(remote_model_names):
        updated_mapping[f"model{i}"] = model_name

    save_model_mapping(updated_mapping)

    formatted_models = [
        {
            "name": model["model"],
            "model": f"model{i}",
            "modified_at": model.get("modified_at", ""),
            "size": model.get("size", 0),
            "digest": model.get("digest", ""),
            "details": model.get("details", {}),
        }
        for i, model in enumerate(remote_models)
    ]

    return jsonify({"models": formatted_models})

def save_chats_data(model_key, data):
    os.makedirs(SAVED_DATA_PATH, exist_ok=True)
    timestamp = int(time.time() * 1000)
    file_path = os.path.join(SAVED_DATA_PATH, f"{model_key}_{timestamp}.json")
    with open(file_path, "w") as file:
        file.write(data)

def remove_model_field_from_json(json_string):
    try:
        data = json.loads(json_string)
        if "model" in data:
            del data["model"]
        return json.dumps(data)
    except json.JSONDecodeError:
        return json_string

def load_model_mapping():
    if os.path.exists(MODEL_MAPPING_FILE):
        with open(MODEL_MAPPING_FILE, "r") as file:
            return json.load(file)
    return {}

def save_model_mapping(model_mapping):
    with open(MODEL_MAPPING_FILE, "w") as file:
        json.dump(model_mapping, file, indent=2)

if __name__ == "__main__":
    create_embeddings_table()
    app.run(host="0.0.0.0", port=5000, debug=False)
