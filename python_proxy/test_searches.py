from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from collections import Counter


def find_best_match_cosine(query_embedding, embeddings):
    best_match = None
    highest_similarity = -1
    
    query_embedding_array = np.array(query_embedding, dtype=np.float32).reshape(1, -1)
    
    for pdf_file, doc_id, embedding in embeddings:
        embedding_array = np.array(embedding, dtype=np.float32).reshape(1, -1)
        similarity = cosine_similarity(query_embedding_array, embedding_array)[0][0]
        if similarity > highest_similarity:
            highest_similarity = similarity
            best_match = (pdf_file, doc_id)
    
    return best_match

################################################################

from sklearn.neighbors import NearestNeighbors

def create_knn_model(embeddings, n_neighbors=1,metric='cosine'):
    embedding_vectors = [embedding for _, _, embedding in embeddings]
    knn_model = NearestNeighbors(n_neighbors=n_neighbors, metric=metric)
    knn_model.fit(embedding_vectors)
    return knn_model

def find_best_match_knn(query_embedding, knn_model, embeddings):
    distances, indices = knn_model.kneighbors([query_embedding])
    nearest_index = indices[0][0]
    return embeddings[nearest_index][0], embeddings[nearest_index][1]

################################################################

import faiss

def create_faiss_index(embeddings):
    embedding_vectors = np.array([embedding for _, _, embedding in embeddings], dtype=np.float32)
    d = embedding_vectors.shape[1]
    index = faiss.IndexFlatL2(d)
    index.add(embedding_vectors)
    return index

def find_best_match_faiss(query_embedding, faiss_index, embeddings):
    query_embedding_array = np.array([query_embedding], dtype=np.float32)
    distances, indices = faiss_index.search(query_embedding_array, 1)
    nearest_index = indices[0][0]
    return embeddings[nearest_index][0], embeddings[nearest_index][1]

################################################################

from sklearn.naive_bayes import GaussianNB

def create_naive_bayes_model(embeddings):
    embedding_vectors = np.array([embedding for _, _, embedding in embeddings], dtype=np.float32)
    labels = np.arange(len(embeddings))
    nb_model = GaussianNB()
    nb_model.fit(embedding_vectors, labels)
    return nb_model

def find_best_match_naive_bayes(query_embedding, nb_model, embeddings):
    query_embedding_array = np.array(query_embedding, dtype=np.float32).reshape(1, -1)
    predicted_label = nb_model.predict(query_embedding_array)[0]
    return embeddings[predicted_label][0], embeddings[predicted_label][1]


################################################################

def ansemble(query_embedding, embeddings):
    results = {}

    # Косинусное сходство
    best_match_cosine = find_best_match_cosine(query_embedding, embeddings)
    results["cosine"] = {"file": best_match_cosine[0], "doc_id": best_match_cosine[1]}

    # # kNN
    # knn_model = create_knn_model(embeddings, metric="cosine")
    # best_match_knn = find_best_match_knn(query_embedding, knn_model, embeddings)
    # results["knn_cosine"] = {"file": best_match_knn[0], "doc_id": best_match_knn[1]}

    # # kNN
    # knn_model = create_knn_model(embeddings, metric="nan_euclidean")
    # best_match_knn = find_best_match_knn(query_embedding, knn_model, embeddings)
    # results["knn_nan_euclidean"] = {"file": best_match_knn[0], "doc_id": best_match_knn[1]}

    # # kNN
    # knn_model = create_knn_model(embeddings, metric="chebyshev")
    # best_match_knn = find_best_match_knn(query_embedding, knn_model, embeddings)
    # results["knn_chebyshev"] = {"file": best_match_knn[0], "doc_id": best_match_knn[1]}
    # # kNN
    # knn_model = create_knn_model(embeddings, metric="euclidean")
    # best_match_knn = find_best_match_knn(query_embedding, knn_model, embeddings)
    # results["knn_euclidean"] = {"file": best_match_knn[0], "doc_id": best_match_knn[1]}

    # FAISS
    faiss_index = create_faiss_index(embeddings)
    best_match_faiss = find_best_match_faiss(query_embedding, faiss_index, embeddings)
    results["faiss"] = {"file": best_match_faiss[0], "doc_id": best_match_faiss[1]}

    # Наивный Байесовский классификатор
    nb_model = create_naive_bayes_model(embeddings)
    best_match_naive_bayes = find_best_match_naive_bayes(query_embedding, nb_model, embeddings)
    results["naive_bayes"] = {"file": best_match_naive_bayes[0], "doc_id": best_match_naive_bayes[1]}
    
    # Подсчет частот встречаемости 'file'
    files = [result["file"] for result in results.values()]
    file_counts = Counter(files)
    
    # Нахождение наиболее частого 'file'
    most_common_file, _ = file_counts.most_common(1)[0]

    # Подсчет частот встречаемости 'doc_id' для наиболее частого 'file'
    doc_ids_for_common_file = [result["doc_id"] for result in results.values() if result["file"] == most_common_file]
    doc_id_counts = Counter(doc_ids_for_common_file)
    
    # Нахождение наиболее частого 'doc_id' для наиболее частого 'file'
    most_common_doc_id, _ = doc_id_counts.most_common(1)[0]

    # Возврат кортежа (наиболее частый 'file', наиболее частый 'doc_id' для этого 'file')
    return (most_common_file, most_common_doc_id)