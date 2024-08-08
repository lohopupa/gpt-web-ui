from io import BufferedReader
import io
import os
import shutil
import tempfile
from fastapi import UploadFile
from openai import OpenAI
import time

if os.getenv('OPENAI_API_KEY'):
    api_key = os.getenv('OPENAI_API_KEY')
else:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')

client = OpenAI(api_key=api_key, base_url="http://gpt.lhpa.ru/v1")

MAIN_VECTOR_STORE_NAME = "415 Base"

def get_or_create_vector_store(category):
    vector_stores = client.beta.vector_stores.list()
    for vs in vector_stores.data:
        if vs.name == category:
            return vs
    new_vector_store = client.beta.vector_stores.create(name=category)
    return new_vector_store

def get_file_id(filename):
    response = client.files.list(purpose="assistants")
    files = list(response.data)
    for file in files:
        if file.filename == filename:
            return file.id

def get_file_ids(filenames):
    response = client.files.list(purpose="assistants")
    files = list(response.data)
    file_ids = []
    
    for filename in filenames:
        for file in files:
            if file.filename == filename:
                file_ids.append(file.id)
                break
    return file_ids


async def upload_file(file: UploadFile, category) -> str:
    vector_store = get_or_create_vector_store(category)
    main_vector_store = get_or_create_vector_store(MAIN_VECTOR_STORE_NAME)

    try:
        file_content = await file.read()
        buffer = io.BytesIO(file_content)
        buffer.name = file.filename
    
        file_stream = [buffer]

        # Загрузка файла в основной vector_store
        file_batch_main = client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=main_vector_store.id, files=file_stream
        )
        file_id = get_file_id(file.filename)

        if category != MAIN_VECTOR_STORE_NAME:
            # Загрузка файла в категорийный vector_store
            client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store.id, file_ids=[file_id]
        )

        while file_batch_main.status == 'in_progress':
            print("Waiting for files to be processed...")
            time.sleep(5)
            file_batch_main = client.beta.vector_stores.file_batches.retrieve(file_batch_main.id)

        print("Files processed.")
        return None
    except Exception as e:
        return f"Error uploading file: {e}"

def get_assistant_id():
    if len(client.beta.assistants.list().data) == 0:
        assistant = client.beta.assistants.create(
            name="Document Assistant",
            instructions="Вы эксперт-помощник по документам. Используйте свою базу знаний, чтобы отвечать на вопросы на основе загруженных документов.",
            model="gpt-4o-mini",
            tools=[{"type": "file_search"}],
            )
        print("New assistant has been created with id: ", assistant.id)
    else:
        assistant = client.beta.assistants.list().data[0]
    return assistant.id

def generate_answer(question, categories=None):
    assistant_id = get_assistant_id()
    
    # Если категории не указаны, используем основной vector_store
    if not categories:
        main_vector_store = get_or_create_vector_store(MAIN_VECTOR_STORE_NAME)
        return ask_question_for_vector_store(question, main_vector_store.id, assistant_id)
    
    # Иначе выполняем поиск по указанным категориям
    all_results = []
    for category in categories:
        vector_store = get_or_create_vector_store(category)
        result = ask_question_for_vector_store(question, vector_store.id, assistant_id)
        if result:
            all_results.append(result)
    
    # Объединяем результаты и возвращаем
    combined_answer = "\n\n".join(all_results)
    return combined_answer

def ask_question_for_vector_store(question, vector_store_id, assistant_id):
    try:
        thread = client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": question
                }
            ],
            tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
        )
        
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id,
            instructions="При необходимости обращайся к пользователю Станислав."
        )
        
        while True:
            run_result = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run_result.status == 'completed':
                messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))
                message_content = messages[0].content[0].text
                annotations = message_content.annotations
                citations = []
                for index, annotation in enumerate(annotations):
                    message_content.value = message_content.value.replace(annotation.text, f"[{index}]")
                    if file_citation := getattr(annotation, "file_citation", None):
                        cited_file = client.files.retrieve(file_citation.file_id)
                        citations.append(f"[{index}] {cited_file.filename}")
                result = f"\nОтвет: {message_content.value}\nИнформация найдена в следующих файлах:\n" + "\n".join(citations)
                return result

    except Exception as e:
        print(f"Error during run: {e}")
        return None


print(generate_answer("расскажи мне про AutoGRAPH GSMConf 5.0",categories=["test3"]))


# class EventHandler(AssistantEventHandler):
#     @override
#     def on_text_created(self, text) -> None:
#         print(f"\nassistant > {text}", end="", flush=True)

#     @override
#     def on_tool_call_created(self, tool_call):
#         print(f"\nassistant > {tool_call.type}\n", flush=True)

#     @override
#     def on_message_done(self, message) -> None:
#         message_content = message.content[0].text
#         annotations = message_content.annotations
#         citations = []
#         for index, annotation in enumerate(annotations):
#             message_content.value = message_content.value.replace(
#                 annotation.text, f"[{index}]"
#             )
#             if file_citation := getattr(annotation, "file_citation", None):
#                 cited_file = client.files.retrieve(file_citation.file_id)
#                 citations.append(f"[{index}] {cited_file.filename}")

#         print(message_content.value)
#         print("\n".join(citations))