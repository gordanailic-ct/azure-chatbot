from config.config import DefaultConfig
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from urllib.parse import urlparse, unquote, quote
from services.azure_clients import get_openai_client, get_search_client

CONFIG = DefaultConfig()
openai_client = get_openai_client()
search_client = get_search_client()

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

            VAŽNO:
            - Ako je trenutno pitanje kratko, nejasno ili zavisno od prethodnog pitanja, obavezno ubaci temu iz prethodne istorije razgovora.
            - To posebno važi za pitanja kao:
            "Možeš detaljnije?",
            "Objasni mi više",
            "Šta to znači?",
            "Kako to?",
            "A gde se to nalazi?"

            Primer:
            Prethodno pitanje: Šta je radna površina?
            Trenutno pitanje: Jel možeš detaljnije da mi objasniš?
            Preformulisano pitanje: Detaljnije objasni šta je radna površina u ITSM sistemu.
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
    
    #rag retriviel
    results = list(search_client.search(
        search_text=standalone_question,
        vector_queries=[
            {
                "kind": "vector",
                "vector": vector,
                "k": 10,
                "fields": "contentVector"
            }
        ],
        query_type="semantic",
        semantic_configuration_name="default",
        select=["content", "source", "page", "url"],
        top=5
    ))


    def is_table_of_contents(content):
        text = content.lower()

        # direktno ako piše sadržaj
        if "sadržaj" in text or "sadrzaj" in text:
            return True

        # mnogo tačkica kao u sadržaju
        dots_count = content.count("....")
        if dots_count >= 3:
            return True

        # više naziva sekcija + tačkice
        toc_keywords = [
            "pristup aplikaciji",
            "početni ekran",
            "radna površina",
            "opis radne površine",
            "dashboard"
        ]

        keyword_hits = sum(1 for word in toc_keywords if word in text)

        if keyword_hits >= 2 and dots_count >= 1:
            return True

        return False

    filtered_results = []

    for r in results:
        content = r.get("content", "")

        if is_table_of_contents(content):
            print("IZBACUJEM SADRZAJ PAGE:", r.get("page"))
            continue

        filtered_results.append(r)

    if not filtered_results:
        return "Na osnovu trenutno dostupne dokumentacije, nemam informaciju o tome. Pokušajte da pitanje formulišete drugačije ili preciznije."

    print("\n=== SEARCH RESULTS ===")

    for r in results:
        print("SCORE:", r.get("@search.score"))
        print("PAGE:", r.get("page"))
        print("SOURCE:", r.get("source"))
        print("CONTENT:", r.get("content", "")[:700])
        print("-" * 50)

    print("======================\n")

    context_parts = []
    for r in filtered_results:
        context_parts.append(r["content"])

    context = "\n".join(context_parts)

    messages = [
    {
        "role": "system",
        "content": """Ti si interni ITSM support chatbot koji pomaže korisnicima u radu sa ITSM tiketing sistemom.

        Koristi isključivo informacije iz prosleđene dokumentacije.

        PRAVILA:
        - Ne koristi svoje opšte znanje
        - Ne izmišljaj odgovore
        - Odgovaraj jasno, kratko i na srpskom jeziku
        - Ako korisnik pita "kako", "objasni" ili traži detalje, navedi konkretne korake iz dokumentacije
        - Istoriju razgovora koristi samo za razumevanje konteksta pitanja

        VAŽNO:
        - Ako odgovor NE postoji u dokumentaciji:
        napiši TAČNO:
        "Na osnovu trenutno dostupne dokumentacije, nemam informaciju o tome."
        i NE prikazuj nikakve reference

        - Ako dokumentacija nije relevantna za pitanje:
        ignoriši je i odgovori da nema informacije

        - Nikada nemoj prikazivati reference, linkove, stranice ili izvore u odgovoru
        - Reference će sistem automatski dodati nakon odgovora

        - Ako pitanje nije vezano za ITSM alat:
        odgovori:
        "Mogu da pomognem samo u vezi sa ITSM alatom."
        """
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
        Ako dokumentacija sadrži korake, opcije ili polja koja treba popuniti, obavezno ih navedi.
        Ne uključuj informacije iz susednih sekcija ako nisu deo direktnog odgovora."""
    })

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0
    )

    answer = response.choices[0].message.content
    answer = answer.replace("📎 Reference:", "")

    best_score = filtered_results[0].get("@search.score", 0) if filtered_results else 0
    if best_score < 0.025:
        return answer

    if (
        "Na osnovu trenutno dostupne dokumentacije, nemam informaciju o tome" in answer
        or
        "Mogu da pomognem samo u vezi sa ITSM alatom." in answer
):
        return answer

    else:
        refs_text = ""
        if filtered_results:
            refs_text = "\n\n📎 Reference:\n"


        seen_refs = set()
        count = 0
       
        for r in filtered_results:
            if count == 2:
                break

            source = r.get("source", "Nepoznat dokument")
            page = r.get("page", "?")

            key = (source, page)

            if key in seen_refs:
                continue

            seen_refs.add(key)

            original_url = r.get("url", "")
            safe_url = generate_sas_url_from_existing_url(original_url, page)

            refs_text += f"- {source} (strana {page})\n  {safe_url}\n"

            count += 1

        return answer + refs_text