from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from config import DefaultConfig


CONFIG = DefaultConfig()

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


def ask_question(question):

    embedding = openai_client.embeddings.create(
        model="text-embedding-3-large",
        input=question
    )

    vector = embedding.data[0].embedding

    results =  search_client.search(
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

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Ti si asistent koji odgovara na pitanja koristeći korisničko uputstvo."
            },
            {
                "role": "user",
                "content": f"""
Uputstvo:
{context}

Pitanje:
{question}
"""
            }
        ],
        temperature=0
    )
    #print("\nODGOVOR BOTA:\n")
    #print(response.choices[0].message.content)
    return response.choices[0].message.content

    

#for r in results:
 #   print(r["content"])
  #  print("\n-------------------\n")

# if __name__ == "__main__":

#     pitanje = "Kako se aktivira nalog?"

#     odgovor = ask_question(pitanje)

#     print("\nFINALNI ODGOVOR:\n")
#     print(odgovor)