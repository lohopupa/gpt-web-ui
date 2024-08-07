import os
import textwrap
import time
import uuid
from pathlib import Path

import langchain
from langchain.schema import Document
# from langchain.chains import RetrievalQA
# from langchain.chat_models import ChatOllama
from langchain.document_loaders import PyMuPDFLoader
# from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS

import fitz  # PyMuPDF


import PyPDF2

def pypdf_read_pdf(file_path):
    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        
        text = ""
        
        for page in reader.pages:
            text += page.extract_text()
    
    return text

def read_pdf_data(file_path):
    pdf_document = fitz.open(file_path)
    document_texts = []
    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        document_texts.append(page.get_text())  # Extract text from page
    return document_texts

# def load_pdf_data(file_path):
#     loader = PyMuPDFLoader(file_path=file_path)
#     docs = loader.load()
#     return docs

# def split_docs(documents, chunk_size=1000, chunk_overlap=20):
#     text_splitter = RecursiveCharacterTextSplitter(
#         chunk_size=chunk_size,
#         chunk_overlap=chunk_overlap
#     )
#     chunks = text_splitter.split_documents(documents=documents)
#     return chunks

def load_pdf_data(file_path):
    pdf_document = fitz.open(file_path)
    document_text = ""
    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        document_texts += " " + page.get_text().replace(".", "").replace("\n", "").replace("\r", "").replace("•", "")
    return document_text


def split_docs(document_text, chunk_size=1000,chunk_overlap=20):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = text_splitter.split_text(document_text)
    return chunks

# def split_string_on_chunks(data, chunk_size=1000, chunks_count=20):
#     chunks = []
#     start = 0
#     data_length = len(data)

#     # Calculate the overlap size
#     total_overlap = chunk_size * chunks_count - data_length
#     if total_overlap > 0:
#         chunks_overlap = total_overlap // (chunks_count - 1)
#     else:
#         chunks_overlap = 0

#     while len(chunks) < chunks_count and start < data_length:
#         end = start + chunk_size
#         chunk = data[start:end]
#         chunks.append(chunk)
#         start += chunk_size - chunks_overlap

#     return chunks



# chunksizes_dict = {
#     "USER_MANUAL_TK-TMP_v.1.0.pdf":                             119,
#     "USER_MANUAL_XGP_v.2.0.pdf":                                312,
#     "APP_NOTE_QUICK_START_AG-X_v.1.0.pdf":                      106,
#     "APP_NOTE_TK-Receiver-Air(TKAM-Air)_v.1.0.pdf":             251,
#     "USER_MANUAL_AG-GSM-INFO5_v.1.0.11.pdf":                   1551,
#     "USER_MANUAL_IBP-AG-3_v.1.1.pdf":                           192,
#     "USER_MANUAL_AutoGRAPH-LX_v.1.8.pdf":                       549,
#     "USER_MANUAL_TK-RPM_v.1.3.pdf":                              96,
#     "USER_MANUAL_AG5_PRO_QUICK_START_231 (1).pdf":              342,
#     "APP_NOTE_GX_Wi-Fi_v.1.0.pdf":                              142,
#     "USER_MANUAL_TKAM_v.1.11.pdf":                              591,
#     "APP_NOTE_TK-Receiver-Air(TKLS-Air)_v.1.0.pdf":             256,
#     "USER_MANUAL_TKAM-Air_v.1.5.pdf":                           348,
#     "USER_MANUAL_AutoGRAPH-SX_v.1.6.pdf":                       649,
#     "USER_MANUAL_AutoGRAPH-GX_v.1.10.pdf":                      818,
#     "USER_MANUAL_AutoGRAPH_ASN_v.1.3.pdf":                     1314,
#     "USER_MANUAL_TKLS-L_v.3.0.pdf":                             543,
#     "USER_MANUAL_TK-CardReader_Plus_v.1.7.pdf":                 517,
#     "USER_MANUAL_AG-HOSTING_BILLING_v.2.0.pdf":                 570,
#     "USER_MANUAL_AutoGRAPH-LogistiX_v.1.2.pdf":                 440,
#     "USER_MANUAL_TK-INFO-Mini_v.1.1.pdf":                       980,
#     "USER_MANUAL_TK-CAN-LOG_v.2.6.pdf":                         285,
#     "APP_NOTE_AGL_v.1.8.pdf":                                   163,
#     "USER_MANUAL_TKLS_EX_2G_v.1.6.pdf":                         546,
#     "USER_MANUAL_TKFC_Plus_v.1.6.pdf":                          951,
#     "SETUP_GUIDE_TKLS-Air_v.1.0.pdf":                           195,
#     "APP_NOTE_MOVON_v.1.1.pdf":                                 137,
#     "USER_MANUAL_TK-Receiver-Air_v.2.0.pdf":                    241,
#     "USER_MANUAL_TK-Reader-M_and_TK-Marker-M_v.1.0.pdf":        372,
#     "USER_MANUAL_TK-CapCAN_v.1.0.pdf":                           63,
#     "USER_MANUAL_TKLS_v.1.24.pdf":                              495,
#     "USER_MANUAL_TKLS-Air_v.1.9.pdf":                           390,
#     "USER_MANUAL_BILLING_v.3.0.pdf":                            647,
#     "APP_NOTE_AG-X_CAN_v.1.0.pdf":                              134,
#     "USER_MANUAL_TK-Marker-CAN_v.1.0.pdf":                       81,
#     "USER_MANUAL_ASN_AutoGRAPH-ASN_v.1.4.pdf":                  741,
#     "USER_MANUAL_AG_5_PRO_231(full)_v.2.0.pdf":                9718,
#     "USER_MANUAL_SMS_INFO5_v.1.1.pdf":                          527,
#     "USER_MANUAL_TK-Marker-Air_v.1.1.pdf":                      185
# }




# def create_embeddings(chunks, embedding_model, storing_path="vectorstore"):
#     vectorstore = FAISS.from_documents(chunks, embedding_model)
#     vectorstore.save_local(storing_path)
#     return vectorstore

# # function for loading the embedding model
# def load_embedding_model(model_name, normalize_embedding=True):
#     print("Loading embedding model...")
#     start_time = time.time()
#     hugging_face_embeddings = HuggingFaceEmbeddings(
#         model_name=model_name,
#         model_kwargs={'device': 'cpu'},  # here we will run the model with CPU only
#         encode_kwargs={
#             'normalize_embeddings': normalize_embedding  # keep True to compute cosine similarity
#         }
#     )
#     end_time = time.time()
#     time_taken = round(end_time - start_time, 2)
#     print(f"Embedding model load time: {time_taken} seconds.\n")
#     return hugging_face_embeddings


# # Function for creating embeddings using FAISS
# def create_embeddings(chunks, embedding_model, storing_path="vectorstore"):
#     print("Creating embeddings...")
#     e_start_time = time.time()

#     # Create the embeddings using FAISS
#     vectorstore = FAISS.from_documents(chunks, embedding_model)

#     e_end_time = time.time()
#     e_time_taken = round(e_end_time - e_start_time, 2)
#     print(f"Embeddings creation time: {e_time_taken} seconds.\n")

#     print("Writing vectorstore..")
#     v_start_time = time.time()

#     # Save the model in a directory
#     vectorstore.save_local(storing_path)

#     v_end_time = time.time()
#     v_time_taken = round(v_end_time - v_start_time, 2)
#     print(f"Vectorstore write time: {v_time_taken} seconds.\n")

#     # return the vectorstore
#     return vectorstore


# # Create the chain for Question Answering
# def load_qa_chain(retriever, llm, prompt):
#     print("Loading QA chain...")
#     start_time = time.time()
#     qa_chain = RetrievalQA.from_chain_type(
#         llm=llm,
#         retriever=retriever,  # here we are using the vectorstore as a retriever
#         chain_type="stuff",
#         return_source_documents=True,  # including source documents in output
#         chain_type_kwargs={'prompt': prompt}  # customizing the prompt
#     )
#     end_time = time.time()
#     time_taken = round(end_time - start_time, 2)
#     print(f"QA chain load time: {time_taken} seconds.\n")
#     return qa_chain


# def get_response(query, chain) -> str:
#     # Get response from chain
#     response = chain({'query': query})
#     res = response['result']
#     # Wrap the text for better output in Jupyter Notebook
#     # wrapped_text = textwrap.fill(res, width=100)
#     return res