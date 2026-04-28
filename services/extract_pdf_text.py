from pypdf import PdfReader
from azure.storage.blob import BlobServiceClient
from services.sync_state import load_index_state, save_index_state
from config.config import DefaultConfig
import io
from dotenv import load_dotenv
import re
from services.azure_clients import get_openai_client, get_search_client


load_dotenv()

CONFIG = DefaultConfig()


openai_client = get_openai_client()
search_client = get_search_client()

def sanitize_key(text):
    return re.sub(r'[^a-zA-Z0-9_-]', '_', text)


def chunk_text(text, chunk_size=3000, overlap=500):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


# Blob Storage
blob_service_client = BlobServiceClient.from_connection_string(
    CONFIG.AZURE_STORAGE_CONNECTION_STRING
)

container_client = blob_service_client.get_container_client(
    CONFIG.CONTAINER_NAME
)

def process_blob_pdf(blob):
    documents = []

    print(f"Obradjujem: {blob.name}")

    blob_client = container_client.get_blob_client(blob)
    stream = blob_client.download_blob().readall()
    file_url = blob_client.url

    reader = PdfReader(io.BytesIO(stream))

    total_chunks_for_file = 0
    safe_filename = sanitize_key(blob.name)

    for page_index, page in enumerate(reader.pages):
        page_num = page_index + 1

        page_text = page.extract_text() or ""

        if not page_text.strip():
            continue

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
                "url": file_url,
                "source_file": safe_filename
            }

            documents.append(doc)
            total_chunks_for_file += 1

    if documents:
        search_client.upload_documents(documents)

    print(f"{blob.name} → {total_chunks_for_file} chunkova")

    return total_chunks_for_file

def sync_new_documents():
    state = load_index_state()

    processed_files = []
    skipped_files = []
    deleted_list = []

    current_blobs = {
        blob.name: blob.etag
        for blob in container_client.list_blobs()
        if blob.name.lower().endswith(".pdf")
    }
    deleted_files = set(state.keys()) - set(current_blobs.keys())

    for deleted_file in deleted_files:
        safe_filename = sanitize_key(deleted_file)
        delete_document_chunks(search_client, safe_filename)
        del state[deleted_file]
        deleted_list.append(deleted_file)
        print(f"{deleted_file} uklonjen iz indexa i state fajla")

    for blob in container_client.list_blobs():
        if not blob.name.lower().endswith(".pdf"):
            continue

        current_etag = blob.etag
        saved = state.get(blob.name)

        # već obrađen i nije menjan
        if saved and saved.get("etag") == current_etag:
            skipped_files.append(blob.name)
            continue

        if saved:
            safe_filename = sanitize_key(blob.name)
            delete_document_chunks(search_client, safe_filename)
            
        process_blob_pdf(blob)

        state[blob.name] = {
            "etag": current_etag
        }

        processed_files.append(blob.name)

    save_index_state(state)

    return {
        "processed": processed_files,
        "skipped": skipped_files,
        "deleted": deleted_list
    }

def delete_document_chunks(search_client, safe_filename):
    results = search_client.search(
        search_text="*",
        filter=f"source_file eq '{safe_filename}'",
        select=["id"],
        top=1000
    )

    docs_to_delete = [{"id": doc["id"]} for doc in results]

    if docs_to_delete:
        search_client.delete_documents(documents=docs_to_delete)
        print(f"Obrisano {len(docs_to_delete)} chunkova za {safe_filename}")
    else:
        print(f"Nema chunkova za brisanje za {safe_filename}")

if __name__ == "__main__":
    sync_new_documents()