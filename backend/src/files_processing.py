from io import BytesIO
import pymupdf
from docx import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

async def exctract_text_from_file(file) -> str:
    ext = file.filename.split(".")[-1]
    match ext:
        case "pdf":
            return await extract_text_from_pdf(file)
        case "docx":
            return await  extract_text_from_docx(file)
        case _:
            raise Exception("Unsupported file type")

def clean_text(text):
    return text.replace(".", "").replace("\n", "").replace("\r", "").replace("•", "").replace("\\", "")

async def extract_text_from_pdf(file) -> str:
    document = pymupdf.open(stream=await file.read(), filetype="pdf")
    text = ""
    for page_num in range(document.page_count):
        page = document.load_page(page_num)
        text += clean_text(page.get_text())
    await file.seek(0)
    return text

async def extract_text_from_docx(file) -> str:
    document = Document(BytesIO(await file.read()))
    text = ""
    for paragraph in document.paragraphs:
        text += clean_text(paragraph.text)
    await file.seek(0)
    return text


def split_docs(document_text, chunk_size=1000,chunk_overlap=20):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = text_splitter.split_text(document_text)
    return chunks