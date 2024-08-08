import ollama
import openai

def add_file(filename, text, category, db):
    ollama_result = ollama.upload_file(filename, text, category, db)
    openai_result = openai.upload_file(filename, text, category)
    return {
        "ollama_result": ollama_result,
        "openai_result": openai_result,
    }

def query_model():
    pass