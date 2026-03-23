from pypdf import PdfReader
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient
from config import DefaultConfig
import io
from dotenv import load_dotenv
import re


load_dotenv()

CONFIG = DefaultConfig()

def sanitize_key(text):
    return re.sub(r'[^a-zA-Z0-9_-]', '_', text)

# Azure OpenAI
openai_client = AzureOpenAI(
    api_key=CONFIG.AZURE_OPENAI_API_KEY,
    api_version="2024-02-15-preview",
    azure_endpoint=CONFIG.AZURE_OPENAI_ENDPOINT
)

# Azure AI Search
search_client = SearchClient(
    endpoint=CONFIG.AZURE_SEARCH_ENDPOINT,
    index_name="chatbot-index-goga",
    credential=AzureKeyCredential(CONFIG.AZURE_SEARCH_API_KEY)
)

# Blob Storage
blob_service_client = BlobServiceClient.from_connection_string(
    CONFIG.AZURE_STORAGE_CONNECTION_STRING
)

container_client = blob_service_client.get_container_client(
    CONFIG.CONTAINER_NAME
)

documents = []

# 🔥 prolaz kroz sve PDF fajlove
for blob in container_client.list_blobs():

    if not blob.name.endswith(".pdf"):
        continue

    print(f"Obradjujem: {blob.name}")

    blob_client = container_client.get_blob_client(blob)
    stream = blob_client.download_blob().readall()

    reader = PdfReader(io.BytesIO(stream))

    text = ""

    # 🔹 ekstrakcija teksta
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    # 🔹 chunking
    chunk_size = 1500
    overlap = 200
    start = 0
    chunks = []

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    print(f"{blob.name} → {len(chunks)} chunkova")

    # 🔹 embedding + dokumenti
    for i, chunk in enumerate(chunks):

        embedding = openai_client.embeddings.create(
            model="text-embedding-3-large",
            input=chunk
        )

        vector = embedding.data[0].embedding
        safe_filename = sanitize_key(blob.name)

        doc = {
            "id": f"{safe_filename}-{i}",  # 🔥 bitno da bude unique
            "content": chunk,
            "contentVector": vector
        }

        documents.append(doc)

# 🔹 upload u AI Search
if documents:
    search_client.upload_documents(documents)
    print(f"Ukupno ubaceno {len(documents)} dokumenata!")
else:
    print("Nema dokumenata za upload.")