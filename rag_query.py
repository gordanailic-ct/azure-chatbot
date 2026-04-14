from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from config import DefaultConfig

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

    results = search_client.search(
        search_text="",
        vector_queries=[
            {
                "kind": "vector",
                "vector": vector,
                "k": 3,
                "fields": "contentVector"
            }
        ],
        select=["content"]
    )

    context = ""
    for r in results:
        context += r["content"] + "\n"

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

Odgovori koristeći dokumentaciju samo ako je relevantna."""
    })

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0
    )

    return response.choices[0].message.content