import ollama
import openai_gpt
from files_processing import exctract_text_from_file

async def add_file(file, category, db):
    print("START")
    text = await exctract_text_from_file(file)
    print("TEXT LOADED")
    ollama_result = ollama.upload_file(file.filename, text, category, db)
    print("OLLAMA DONE")
    openai_result = await openai_gpt.upload_file(file, category)
    print("OPENAI DONE")
    return {
        "ollama_result": ollama_result,
        "openai_result": openai_result,
    }
