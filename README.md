# ITSM AI Chatbot

Ovaj projekat predstavlja inteligentni chatbot razvijen korišćenjem Azure servisa i RAG (Retrieval-Augmented Generation) pristupa.

Chatbot omogućava korisnicima da postavljaju pitanja nad skupom ITSM dokumenata u PDF formatu. Sistem koristi semantičku pretragu, Azure AI Search i Azure OpenAI model kako bi generisao odgovore zasnovane na dostupnoj dokumentaciji.

Chatbot odgovara na pitanja vezana za ITSM alat, kao što su kreiranje tiketa, aktivacija naloga, promena statusa tiketa, otkazivanje tiketa, onboarding projekta i druga pitanja iz dokumentacije.

## Link ka aplikaciji

https://chat-bot-web-geeafje7b2e4aehy.westeurope-01.azurewebsites.net/

## Funkcionalnosti

- Chat interfejs za komunikaciju sa korisnikom
- Generisanje odgovora pomoću Azure OpenAI modela
- Semantička pretraga koristeći Azure AI Search
- Automatska obrada PDF dokumenata
- Ekstrakcija teksta iz PDF fajlova
- Chunking dokumenata
- Generisanje embedding vektora
- Pretraga relevantnih delova dokumentacije
- Generisanje odgovora sa referencama
- Podrška za kontekst razgovora
- Deploy na Azure App Service
- Logovanje putem Azure Application Insights

## Kako sistem funkcioniše

1. PDF dokumenti se čuvaju u Azure Blob Storage.
2. Tekst se ekstraktuje iz PDF dokumenata.
3. Ekstraktovani tekst se deli na manje segmente.
4. Za svaki segment generiše se embedding vektor.
5. Segmenti se zajedno sa metapodacima čuvaju u Azure AI Search indeksu.
6. Kada korisnik postavi pitanje, pitanje se pretvara u embedding.
7. Azure AI Search pronalazi najrelevantnije delove dokumentacije.
8. Relevantni chunkovi se prosleđuju Azure OpenAI modelu kao kontekst.
9. Model generiše odgovor na osnovu pronađene dokumentacije.
10. Chatbot korisniku vraća odgovor zajedno sa referencama na dokument i stranu.

## Arhitektura

- Frontend: Web Chat / Widget UI
- Komunikacija: Azure Bot Service i Direct Line
- Backend: Python Bot aplikacija
- Hosting: Azure App Service
- AI model: Azure OpenAI GPT model
- Embeddings: Azure OpenAI embeddings model
- Search: Azure AI Search
- Storage: Azure Blob Storage
- Monitoring: Azure Application Insights

## Tehnologije

- Python
- Azure Bot Framework
- Azure OpenAI
- Azure AI Search
- Azure Blob Storage
- Azure App Service
- Azure Application Insights
- AIOHTTP
- Bot Framework Web Chat
- VS Code

## Ključne komponente

### app.py

- Pokreće web server
- Integriše Bot Framework adapter
- Obrađuje poruke preko `/api/messages`
- Generiše Direct Line token
- Povezuje frontend sa bot aplikacijom
- Omogućava logging putem Application Insights

### extract_pdf_text.py

- Čita PDF fajlove iz Azure Blob Storage
- Ekstraktuje tekst iz dokumenata
- Deli tekst na chunkove
- Dodaje metapodatke kao što su naziv dokumenta, broj strane i URL
- Generiše embeddinge
- Upisuje podatke u Azure AI Search indeks

### rag_query.py

- Prima korisničko pitanje
- Po potrebi koristi istoriju razgovora za formiranje samostalnog pitanja
- Generiše embedding pitanja
- Izvršava vector search nad Azure AI Search indeksom
- Prosleđuje relevantan kontekst GPT modelu
- Vraća finalni odgovor i reference

## Chat interfejs

Aplikacija koristi web interfejs baziran na Bot Framework Web Chat biblioteci.

Proces komunikacije:

1. Klijent traži token sa backend-a preko `/api/token`.
2. Backend generiše Direct Line token.
3. Web Chat se povezuje na bot koristeći token.
4. Korisnik komunicira sa chatbot-om u realnom vremenu.
5. Odgovor se prikazuje u chat interfejsu zajedno sa referencama.

## Data Flow dijagram

Za projekat je izrađen RAG Data Flow dijagram koji prikazuje tok korisničkog pitanja kroz sistem:

- korisnik šalje pitanje kroz Web Chat
- poruka se prosleđuje preko Azure Bot Service / Direct Line kanala
- Python bot aplikacija obrađuje pitanje
- pitanje se pretvara u embedding
- Azure AI Search pronalazi relevantne chunkove
- relevantan kontekst se prosleđuje Azure OpenAI modelu
- model generiše odgovor
- aplikacija dodaje reference
- odgovor se prikazuje korisniku

Dodatno je prikazan i tok indeksiranja dokumenata:

- PDF dokumenti
- Azure Blob Storage
- ekstrakcija teksta
- chunking
- generisanje metapodataka
- upis u Azure AI Search indeks

## Evaluacija sistema

Sistem je testiran kroz skup test scenarija podeljenih u više kategorija:

- funkcionalna pitanja
- operativna pitanja
- onboarding pitanja
- follow-up pitanja
- pitanja van domena

Za svaki test scenario praćeni su:

- očekivani rezultat
- dobijeni rezultat
- status testa
- tačnost odgovora
- ispravnost referenci
- napomena o eventualnim odstupanjima

Ukupno je testirano 25 scenarija. Evaluacija je pokazala da chatbot uspešno odgovara na većinu pitanja iz domena ITSM dokumentacije, dok su manja odstupanja primećena kod follow-up pitanja i preciznosti referenci.

## Bezbednost

- Direct Line token se generiše dinamički na backend-u.
- API ključevi se čuvaju u environment varijablama.
- Osetljivi podaci nisu deo repozitorijuma.
- `.env` fajl je isključen iz verzionisanja pomoću `.gitignore`.

## Zaključak

Projekat demonstrira primenu RAG pristupa u enterprise chatbot rešenju. Sistem omogućava korisnicima da dobiju odgovore zasnovane na internoj dokumentaciji, uz prikaz referenci koje povećavaju proverljivost i pouzdanost odgovora.