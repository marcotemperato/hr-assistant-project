import chainlit as cl
import ollama
import chromadb
import os
import uuid
import asyncio

from dotenv import load_dotenv
from chromadb.utils import embedding_functions

# =========================================================
# FASE 1 - LETTURA FILE E CHUNKING
# =========================================================

documents_dir = "resumes"

documents = []
metadatas = []
ids = []

for filename in os.listdir(documents_dir):

    if filename.endswith(".txt"):

        file_path = os.path.join(documents_dir, filename)

        with open(file_path, "r", encoding="utf-8") as file:

            chunks = file.read().replace("\n", ". ").split("### ")

            for chunk in chunks:

                chunk = chunk.strip()

                if chunk != "":

                    documents.append(chunk)

                    metadatas.append({
                        "source": filename
                    })

                    ids.append(str(uuid.uuid4()))

# =========================================================
# FASE 2 - EMBEDDINGS + CHROMADB
# =========================================================

load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=openai_key,
    model_name="text-embedding-3-small"
)

# Persistente -> evita di rigenerare embeddings ogni volta
chroma_client = chromadb.PersistentClient(path="./chroma_db")

collection = chroma_client.get_or_create_collection(
    name="CVs",
    embedding_function=openai_ef
)

# Inserisce i documenti SOLO la prima volta
if collection.count() == 0:

    print("Inserimento CV nel database vettoriale...")

    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

    print("Database popolato.")

else:
    print("Database già popolato.")

# =========================================================
# FUNZIONE LETTURA PRIME RIGHE CV
# =========================================================

def leggi_prime_100_righe(file_path):

    with open(file_path, "r", encoding="utf-8") as file:

        righe = []

        for i, riga in enumerate(file):

            if i < 100:
                righe.append(riga.strip())
            else:
                break

    return " ".join(righe)

# =========================================================
# AVVIO CHAT
# =========================================================

@cl.on_chat_start
async def on_chat_start():

    cl.user_session.set(
        "messages",
        [
            {
                "role": "system",
                "content": """
Sei un assistente HR professionale.

Il tuo compito è individuare il candidato migliore rispetto alla richiesta dell'utente.

Rispondi in modo:
- professionale
- sintetico
- pragmatico

Non inventare informazioni.
"""
            }
        ]
    )

    await cl.Message(
        content="Assistente HR avviato correttamente."
    ).send()

# =========================================================
# GESTIONE MESSAGGI
# =========================================================

@cl.on_message
async def handle_message(message: cl.Message):

    try:

        user_question = message.content

        # =========================================
        # QUERY CHROMADB
        # =========================================

        results = collection.query(
            query_texts=[user_question],
            n_results=1
        )

        best_document = results["documents"][0][0]
        best_metadata = results["metadatas"][0][0]

        filename = best_metadata["source"]

        # =========================================
        # LETTURA NOME CANDIDATO
        # =========================================

        file_path = os.path.join(documents_dir, filename)

        context_nome_candidato = leggi_prime_100_righe(file_path)

        nome_response = await asyncio.to_thread(
            ollama.chat,
            model="llama3.2",
            messages=[
                {
                    "role": "user",
                    "content": f"""
Individua il nome e cognome del candidato presente nel seguente CV.

Rispondi SOLO con nome e cognome.

CV:
{context_nome_candidato}
"""
                }
            ]
        )

        nome = nome_response["message"]["content"].strip()

        # =========================================
        # COSTRUZIONE CONTESTO
        # =========================================

        context = f"""
Nome file: {filename}

Contenuto:
{best_document}
"""

        prompt = f"""
Dato il seguente contesto:

{context}

Domanda utente:
{user_question}

ISTRUZIONI:
- indica il nome del file
- indica il nome del candidato
- spiega perché è adatto
- usa solo informazioni presenti nel CV
- non inventare nulla

Nome candidato:
{nome}
"""

        # =========================================
        # STAMPA DEBUG
        # =========================================

        print("\n" + "=" * 80)
        print("DOMANDA:")
        print(user_question)

        print("\nFILE:")
        print(filename)

        print("\nNOME:")
        print(nome)

        print("\nCONTESTO:")
        print(context)

        print("=" * 80 + "\n")

        # =========================================
        # CHAT HISTORY
        # =========================================

        messages = cl.user_session.get("messages", [])

        messages.append({
            "role": "user",
            "content": prompt
        })

        # =========================================
        # CHIAMATA OLLAMA
        # =========================================

        response = await asyncio.to_thread(
            ollama.chat,
            model="llama3.2",
            messages=messages
        )

        risposta = response["message"]["content"]

        # =========================================
        # INVIO RISPOSTA
        # =========================================

        await cl.Message(
            content=risposta
        ).send()

        # =========================================
        # SALVATAGGIO STORIA
        # =========================================

        messages.append({
            "role": "assistant",
            "content": risposta
        })

        cl.user_session.set("messages", messages)

    except Exception as e:

        errore = f"Errore: {str(e)}"

        print(errore)

        await cl.Message(
            content=errore
        ).send()

# =========================================================
# FINE CHAT
# =========================================================

@cl.on_chat_end
async def on_chat_end():

    await cl.Message(
        content="""
Grazie per aver utilizzato l'assistente HR.
"""
    ).send()