import os
from openai import OpenAI


if os.getenv('OPENAI_API_KEY'):
    api_key = os.getenv('OPENAI_API_KEY')
else:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')

client = OpenAI(api_key=api_key)

def upload_file(filename, text, category) -> bool:
    return "NOT IMPLEMENTED"

