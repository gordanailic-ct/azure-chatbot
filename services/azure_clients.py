from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from config.config import DefaultConfig

_openai_client = None
_search_client = None

CONFIG = DefaultConfig()

def get_openai_client():
    global _openai_client

    if _openai_client is None:
        _openai_client = AzureOpenAI(
            api_key=CONFIG.AZURE_OPENAI_API_KEY,
            api_version="2024-02-15-preview",
            azure_endpoint=CONFIG.AZURE_OPENAI_ENDPOINT
        )

    return _openai_client


def get_search_client():
    global _search_client

    if _search_client is None:
        _search_client = SearchClient(
            endpoint=CONFIG.AZURE_SEARCH_ENDPOINT,
            index_name="chatbot-index-goga",
            credential=AzureKeyCredential(CONFIG.AZURE_SEARCH_API_KEY)
        )

    return _search_client