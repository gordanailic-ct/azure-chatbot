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


def chunk_text(text, chunk_size=1500, overlap=200):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


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

# prolaz kroz sve PDF fajlove
for blob in container_client.list_blobs():

    if not blob.name.endswith(".pdf"):
        continue

    print(f"Obradjujem: {blob.name}")

    blob_client = container_client.get_blob_client(blob)
    stream = blob_client.download_blob().readall()
    file_url = blob_client.url

    reader = PdfReader(io.BytesIO(stream))

    total_chunks_for_file = 0
    safe_filename = sanitize_key(blob.name)

    # ekstrakcija teksta po stranama
    for page_num, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text()

        if not page_text or not page_text.strip():
            continue

        # chunking po jednoj strani
        chunks = chunk_text(page_text)

        for i, chunk in enumerate(chunks):
            embedding = openai_client.embeddings.create(
                model="text-embedding-3-large",
                input=chunk
            )

            vector = embedding.data[0].embedding

            doc = {
                "id": f"{safe_filename}-p{page_num}-{i}",
                "content": chunk,
                "contentVector": vector,
                "source": blob.name,
                "page": page_num,
                "url": file_url
            }

            documents.append(doc)
            total_chunks_for_file += 1

    print(f"{blob.name} → {total_chunks_for_file} chunkova")

# upload u AI Search
if documents:
    search_client.upload_documents(documents)
    print(f"Ukupno ubaceno {len(documents)} dokumenata!")
else:
    print("Nema dokumenata za upload.")