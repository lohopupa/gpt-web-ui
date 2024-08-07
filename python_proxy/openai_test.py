import os
from openai import OpenAI, AssistantEventHandler
from typing_extensions import override
import time

# Установите ваш API ключ
api_key = 'hui'
client = OpenAI(api_key=api_key)

vector_store_name = "Document Store"
files_directory = './new_files_83'




def get_or_create_vector_store():
    vector_stores = client.beta.vector_stores.list()
    for vs in vector_stores.data:
        if vs.name == vector_store_name:
            return vs
    new_vector_store = client.beta.vector_stores.create(name=vector_store_name)
    return new_vector_store

def get_uploaded_file_ids():
    files = client.files.list(purpose="assistants").data
    return {file.filename: file.id for file in files}

def upload_files_to_vector_store(vector_store_id):
    files = [f for f in os.listdir(files_directory) if f.endswith('.pdf') or f.endswith('.doc') or f.endswith('.docx') or f.endswith('.txt')]
    if not files:
        raise Exception(f"В {files_directory} нет файлов для загрузки.")
    
    uploaded_files = get_uploaded_file_ids()
    file_streams = []
    files_to_upload = []
    for pdf_file in files:
        if pdf_file not in uploaded_files:
            files_to_upload.append(pdf_file)
    
    if not files_to_upload:
        print("Все файлы уже загружены.")
        return

    for file_name in files_to_upload:
        file_path = os.path.join(files_directory, file_name)
        file_streams.append(open(file_path, "rb"))

    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store_id, files=file_streams
    )
    print("File batch status:", file_batch.status)
    print("File counts:", file_batch.file_counts)
    
    while file_batch.status == 'in_progress':
        print("Waiting for files to be processed...")
        time.sleep(5)
        file_batch = client.beta.vector_stores.file_batches.retrieve(file_batch.id)
    
    for file_stream in file_streams:
        file_stream.close()
    
    print("All new files processed.")

vector_store = get_or_create_vector_store()

upload_files_to_vector_store(vector_store.id)

def get_assistant_id():
    if len(client.beta.assistants.list().data) == 0:
        assistant = client.beta.assistants.create(
            name="Document Assistant",
            instructions="Вы эксперт-помощник по документам. Используйте свою базу знаний, чтобы отвечать на вопросы на основе загруженных документов.",
            model="gpt-4o-mini",
            tools=[{"type": "file_search"}],
            )
        print("new assistant has been created with id: ", assistant.id) 
    else:
        assistant = client.beta.assistants.list().data[0]

    return assistant.id


def update_assistant(assistant_id):
    try:
        client.beta.assistants.update(
            assistant_id=assistant_id,
            tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
        )
    except Exception as e:
        print(f"Error updating assistant: {e}")


assistant_id = get_assistant_id()
update_assistant(assistant_id)

class EventHandler(AssistantEventHandler):
    @override
    def on_text_created(self, text) -> None:
        print(f"\nassistant > {text}", end="", flush=True)

    @override
    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call.type}\n", flush=True)

    @override
    def on_message_done(self, message) -> None:
        message_content = message.content[0].text
        annotations = message_content.annotations
        citations = []
        for index, annotation in enumerate(annotations):
            message_content.value = message_content.value.replace(
                annotation.text, f"[{index}]"
            )
            if file_citation := getattr(annotation, "file_citation", None):
                cited_file = client.files.retrieve(file_citation.file_id)
                citations.append(f"[{index}] {cited_file.filename}")

        print(message_content.value)
        print("\n".join(citations))


def ask_question(question):
    thread = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": question
            }
        ],
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
    )
    
    try:
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
                print(f"\nОтвет: {message_content.value}")
                print("\nИнформация найдена в следующих файлах:")
                print("\n".join(citations))
                break
  
    except Exception as e:
        print(f"Error during run: {e}")


questions = [
    "Какая погрешность у ДУТ?",
    "Какой протокол используется для быстрой настройки шины CAN?",
    "Какие типы идентификаторов описаны в руководстве?",
    "Какой интернет-браузер рекомендуется использовать для калибровки системы Movon MDSM-7?",
    "Какое значение в столбце 'Байт 1' указывает на фиксацию использования водителем мобильного телефона?",
    "Какие команды необходимо ввести в окне параметров геозоны для события «Контроль скорости»?"
]

for question in questions:
    print(f"\nВопрос: {question}")
    ask_question(question)
while True:
    ask_question(input("> "))