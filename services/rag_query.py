from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from config.config import DefaultConfig
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from urllib.parse import urlparse, unquote, quote

CONFIG = DefaultConfig()

openai_client = AzureOpenAI(
    api_key=CONFIG.AZURE_OPENAI_API_KEY,
    api_version="2024-02-15-preview",
    azure_endpoint=CONFIG.AZURE_OPENAI_ENDPOINT
)

search_client = SearchClient(
    endpoint=CONFIG.AZURE_SEARCH_ENDPOINT,
    index_name="chatbot-index-goga",
    credential=AzureKeyCredential(CONFIG.AZURE_SEARCH_API_KEY)
)

def generate_sas_url_from_existing_url(blob_url, page=None):
    parsed = urlparse(blob_url)
    path_parts = parsed.path.lstrip("/").split("/", 1)

    if len(path_parts) < 2:
        return blob_url

    container_name = path_parts[0]
    blob_name = unquote(path_parts[1])

    sas_token = generate_blob_sas(
        account_name=CONFIG.STORAGE_ACCOUNT_NAME,
        container_name=container_name,
        blob_name=blob_name,
        account_key=CONFIG.AZURE_STORAGE_ACCOUNT_KEY,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=1)
    )

    encoded_blob_name = quote(blob_name)

    final_url = (
        f"https://{CONFIG.STORAGE_ACCOUNT_NAME}.blob.core.windows.net/"
        f"{container_name}/{encoded_blob_name}?{sas_token}"
    )

    if page:
        final_url += f"#page={page}"

    return final_url


def rewrite_question_with_history(question, history):
    if not history:
        return question

    messages = [
        {
            "role": "system",
            "content": """Preformuliši trenutno korisničko pitanje tako da bude potpuno samostalno i jasno,
uzimajući u obzir prethodnu istoriju razgovora.

Pravila:
- zadrži isto značenje
- nemoj odgovarati na pitanje
- vrati samo preformulisano pitanje
- ako je pitanje već jasno samo po sebi, vrati ga bez izmene
- odgovori na srpskom jeziku"""
        }
    ]

    for msg in history[-6:]:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    messages.append({
        "role": "user",
        "content": f"Trenutno pitanje: {question}"
    })

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0
    )

    return response.choices[0].message.content.strip()


def ask_question(question, history=None):
    if history is None:
        history = []

    standalone_question = rewrite_question_with_history(question, history)

    print("Original question:", question)
    print("Standalone question:", standalone_question)

    embedding = openai_client.embeddings.create(
        model="text-embedding-3-large",
        input=standalone_question
    )

    vector = embedding.data[0].embedding

    results = list(search_client.search(
        search_text="",
        vector_queries=[
            {
                "kind": "vector",
                "vector": vector,
                "k": 3,
                "fields": "contentVector"
            }
        ],
        select=["content", "source", "page", "url"]
    ))

    context_parts = []
    for r in results:
        context_parts.append(r["content"])

    context = "\n".join(context_parts)

    messages = [
        {
            "role": "system",
            "content": """Ti si interni ITSM support chatbot koji pomaže korisnicima u radu sa tiketing sistemom.

Koristi isključivo informacije iz prosleđene dokumentacije kada odgovaraš na pitanja o ITSM alatu.
Ako odgovor ne postoji u dokumentaciji, nemoj izmišljati.

Istoriju razgovora koristi da razumeš na šta se trenutno pitanje odnosi.
Odgovaraj jasno, kratko i na srpskom jeziku.

Ako pitanje nije vezano za ITSM alat, ljubazno reci da možeš da pomogneš samo oko ITSM alata."""
        }
    ]

    for msg in history[-6:]:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    messages.append({
        "role": "user",
        "content": f"""Dokumentacija:
{context}

Originalno pitanje korisnika:
{question}

Preformulisano pitanje uz kontekst razgovora:
{standalone_question}

Odgovori koristeći samo informacije koje su direktno relevantne za pitanje.
Ne uključuj informacije iz susednih sekcija ako nisu deo direktnog odgovora."""
    })

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0
    )

    answer = response.choices[0].message.content

    refs_text = ""
    if results:
        best = results[0]
        page = best.get("page", "?")
        original_url = best.get("url", "")

        safe_url = generate_sas_url_from_existing_url(original_url, page)

        refs_text = "\n\n📎 Reference:\n"
        refs_text += f"- {best.get('source', 'Nepoznat dokument')} (strana {page})\n  {safe_url}\n"

    return answer + refs_text