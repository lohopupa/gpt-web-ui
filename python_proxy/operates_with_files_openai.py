from openai import OpenAI
import datetime
import os
if os.getenv('OPENAI_API_KEY'):
    api_key = os.getenv('OPENAI_API_KEY')
else:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key, base_url="http://gpt.lhpa.ru/v1")

def upload_file():
    filename = input("Enter the filename to upload: ")
    try:
        with open(filename, "rb") as file:
            response = client.files.create(file=file, purpose="assistants")
            print(response)
            print(f"File uploaded successfully: {response.filename} [{response.id}]")
    except FileNotFoundError:
        print("File not found. Please make sure the filename and path are correct.")

def list_files():
    response = client.files.list(purpose="assistants")
    if len(response.data) == 0:
        print("No files found.")
        return
    for file in response.data:
        created_date = datetime.datetime.utcfromtimestamp(file.created_at).strftime('%Y-%m-%d')
        print(f"{file.filename} [{file.id}], Created: {created_date}")

def list_and_delete_file():
    while True:
        response = client.files.list(purpose="assistants")
        files = list(response.data)
        if len(files) == 0:
            print("No files found.")
            return
        for i, file in enumerate(files, start=1):
            created_date = datetime.datetime.utcfromtimestamp(file.created_at).strftime('%Y-%m-%d')
            print(f"[{i}] {file.filename} [{file.id}], Created: {created_date}")
        choice = input("Enter a file number to delete, or any other input to return to menu: ")
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(files):
            return
        selected_file = files[int(choice) - 1]
        client.files.delete(selected_file.id)
        print(f"File deleted: {selected_file.filename}")

def delete_all_files():
    confirmation = input("This will delete all OpenAI files with purpose 'assistants'.\n Type 'YES' to confirm: ")
    if confirmation == "YES":
        response = client.files.list(purpose="assistants")
        for file in response.data:
            client.files.delete(file.id)
        print("All files with purpose 'assistants' have been deleted.")
    else:
        print("Operation cancelled.")

def delete_all_assistants():
    confirmation = input("This will delete all assistants.\n Type 'YES' to confirm: ")
    if confirmation == "YES":
        response = client.beta.assistants.list()
        for asiss in response.data:
            client.beta.assistants.delete(asiss.id)
        print("All assistants have been deleted.")
    else:
        print("Operation cancelled.")

def list_and_delete_vector_stores():
    while True:
        response = client.beta.vector_stores.list()
        files = list(response.data)
        if len(files) == 0:
            print("No files found.")
            return
        for i, file in enumerate(files, start=1):
            created_date = datetime.datetime.utcfromtimestamp(file.created_at).strftime('%Y-%m-%d')
            print(f"[{i}] {file.name} [{file.id}], Created: {created_date}")
        choice = input("Enter a file number to delete, or any other input to return to menu: ")
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(files):
            return
        selected_file = files[int(choice) - 1]
        client.beta.vector_stores.delete(selected_file.id)
        print(f"File deleted: {selected_file.name}")

def main():
    while True:
        print("\n== Assistants file utility ==")
        print("[1] Upload file")
        print("[2] List all files")
        print("[3] List all files and delete one of your choice")
        print("[4] Delete all assistant files (confirmation required)")
        print("[5] Delete all assistants (confirmation required)")
        print("[6] List all vector_stores and delete one of your choice")
        print("[9] Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            upload_file()
        elif choice == "2":
            list_files()
        elif choice == "3":
            list_and_delete_file()
        elif choice == "4":
            delete_all_files()
        elif choice == "5":
            delete_all_assistants()
        elif choice == "6":
            list_and_delete_vector_stores()
        elif choice == "9":
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()