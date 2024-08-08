import ollama
import openai_gpt
from files_processing import exctract_text_from_file

async def add_file(filename, file, category, db):
    text = await exctract_text_from_file(file)
    ollama_result = ollama.upload_file(file.filename, text, category, db)
    openai_result = openai_gpt.upload_file(file.filename, file, category)
    return {
        "ollama_result": ollama_result,
        "openai_result": openai_result,
    }

def query_model():
    pass