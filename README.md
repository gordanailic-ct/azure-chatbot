Ovaj projekat predstavlja inteligentni chatbot razvijen korišćenjem Azure servisa i RAG (Retrieval-Augmented Generation) pristupa.  
Chatbot omogućava korisnicima da postavljaju pitanja nad skupom dokumenata (PDF fajlova), pri čemu koristi semantičku pretragu i generativni AI za davanje preciznih odgovora.

---

##  Funkcionalnosti

-  Chat interfejs za komunikaciju sa korisnikom
-  Generisanje odgovora pomoću Azure OpenAI (GPT-4o-mini)
-  Semantička pretraga koristeći Azure AI Search (vector search)
-  Automatska obrada PDF dokumenata (ekstrakcija i chunking)
-  Embedding generisanje za vektorsku pretragu
-  Deploy na Azure App Service
-  Logovanje putem Azure Application Insights

---

##  Kako sistem funkcioniše (RAG)

1. PDF dokumenti se učitavaju iz Azure Blob Storage
2. Tekst se ekstraktuje i deli na manje segmente (chunking)
3. Za svaki segment generišu se embedding vektori
4. Podaci se smeštaju u Azure AI Search indeks
5. Kada korisnik postavi pitanje:
   - generiše se embedding pitanja
   - pronalaze se najrelevantniji dokumenti (vector search)
   - kontekst se prosleđuje GPT modelu
   - model generiše finalni odgovor

---

##  Arhitektura

- **Frontend:** Web chat (Direct Line API)
- **Backend:** Python bot (Bot Framework)
- **AI:** Azure OpenAI (GPT + embeddings)
- **Search:** Azure AI Search (vector database)
- **Storage:** Azure Blob Storage
- **Hosting:** Azure App Service
- **Monitoring:** Application Insights

---

##  Tehnologije

- Python
- Azure Bot Framework
- Azure OpenAI
- Azure AI Search
- Azure Blob Storage
- AIOHTTP
- VS Code

---

##  Ključne komponente

### 🔹 `app.py`
- Pokreće web server (aiohttp)
- Integracija sa Bot Framework-om
- Obrada poruka (`/api/messages`)
- Generisanje Direct Line tokena
- Logging putem Application Insights

---

### 🔹 `extract_pdf_text.py`
- Čita PDF fajlove iz Blob Storage
- Ekstraktuje tekst
- Radi chunking (1500 karaktera, overlap 200)
- Generiše embeddinge
- Upisuje podatke u Azure AI Search

---

### 🔹 `rag_query.py`
- Prima korisničko pitanje
- Generiše embedding pitanja
- Radi vector search
- Prosleđuje kontekst GPT modelu
- Vraća finalni odgovor

---

##  Chat interfejs

Aplikacija koristi jednostavan web interfejs baziran na Bot Framework Web Chat biblioteci.

Proces komunikacije:
1. Klijent traži token sa backend-a (`/api/token`)
2. Backend generiše Direct Line token
3. Web Chat se povezuje na bot koristeći token
4. Korisnik komunicira sa chatbot-om u realnom vremenu

## Bezbednost

- Direct Line token se generiše dinamički na backend-u
- API ključevi se čuvaju u environment varijablama
- Osetljivi podaci nisu deo repozitorijuma (.gitignore)