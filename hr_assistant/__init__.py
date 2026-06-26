import os
import shutil
import chainlit as cl

from document_processor import DocumentProcessor
from database import Database
from config import Config
from utils import LLMHelper

db = Database()


async def upload_file(file):

    os.makedirs(
        Config.DOCUMENTS_DIR,
        exist_ok=True
    )

    destination = os.path.join(
        Config.DOCUMENTS_DIR,
        file.name
    )

    shutil.copy(
        file.path,
        destination
    )

    documents, metadatas, ids = (
        DocumentProcessor.process_single_document(
            destination
        )
    )

    if documents:

        db.add_documents(
            documents,
            metadatas,
            ids
        )

        return f"✅ {file.name} indicizzato"

    return f"❌ Errore elaborazione {file.name}"


@cl.on_chat_start
async def start():

    added, updated, removed = DocumentProcessor.process_documents(db)
    sync_summary = ""
    if any((added, updated, removed)):
        sync_summary = (
            f"\n\n📁 Sync CV: {added} aggiunti, "
            f"{updated} aggiornati, {removed} rimossi."
        )

    cl.user_session.set(
        "messages",
        [
            {
                "role": "system",
                "content": """
Sei un assistente HR professionale.
Il tuo compito è trovare il candidato migliore
in base alla richiesta dell'utente.
Rispondi in modo sintetico e professionale.
""",
            }
        ],
    )

    actions = [
        cl.Action(
            name="show_db",
            payload={"action": "show_db"},
            label="📂 Mostra Database",
        ),
        cl.Action(
            name="count_cv",
            payload={"action": "count_cv"},
            label="📊 Conta CV",
        ),
        cl.Action(
            name="reset_db",
            payload={"action": "reset_db"},
            label="🗑️ Svuota Database",
        ),
    ]

    await cl.Message(
        content=f"✅ HR Assistant avviato correttamente.{sync_summary}",
        actions=actions,
    ).send()


@cl.action_callback("show_db")
async def show_db(action):

    results = db.collection.get(
        include=["metadatas"]
    )

    unique_docs = {}

    for metadata in results["metadatas"]:

        source = metadata.get("source")

        extension = metadata.get("extension")

        unique_docs[source] = extension

    response = (
        f"📂 DOCUMENTI NEL DATABASE "
        f"({len(unique_docs)}):\n\n"
    )

    for source, extension in sorted(
        unique_docs.items()
    ):

        response += (
            f"{source} ({extension})\n"
        )

    await cl.Message(
        content=response
    ).send()


@cl.action_callback("count_cv")
async def count_cv(action):

    results = db.collection.get(
        include=["metadatas"]
    )

    unique_documents = {
        metadata["source"]
        for metadata in results["metadatas"]
    }

    await cl.Message(
        content=f"📊 CV presenti nel database: {len(unique_documents)}"
    ).send()


@cl.action_callback("reset_db")
async def reset_db(action):

    db.reset_database()

    await cl.Message(
        content="✅ Database svuotato correttamente."
    ).send()


@cl.on_message
async def handle_message(message: cl.Message):

    if message.elements:

        results = []

        for file in message.elements:

            result = await upload_file(file)

            results.append(result)

        await cl.Message(
            content="\n".join(results)
        ).send()

        return

    user_question = message.content

    match = db.query_best_cv_chunks(user_question)

    if not match["chunks"]:

        await cl.Message(
            content="❌ Nessun candidato trovato."
        ).send()

        return

    filename = match["source"]
    cv_text = DocumentProcessor.get_cv_text(
        os.path.join(Config.DOCUMENTS_DIR, filename)
    )

    candidate_info = DocumentProcessor.extract_candidate_info(
        cv_text or match["combined_text"]
    )

    prompt = f"""
        Sei un recruiter HR esperto.

        IMPORTANTE:
        - Devi SEMPRE indicare il nome del candidato.
        - Se il nome non è disponibile usa il nome file.
        - Devi spiegare perchè è adatto.
        - Includi email e telefono quando disponibili.

        NOME CANDIDATO:
        {candidate_info.get('name', 'Non trovato')}

        EMAIL:
        {candidate_info.get('email') or 'Non trovata'}

        TELEFONO:
        {candidate_info.get('phone') or 'Non trovato'}

        NOME FILE:
        {filename}

        CONTENUTO CV:
        {match['combined_text']}

        RICHIESTA:
        {user_question}
        """

    messages = cl.user_session.get("messages", [])

    messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    response_message = cl.Message(content="")

    response_message.content = (
        f"📄 CV trovato: {filename} "
        f"({len(match['chunks'])} sezioni)\n\n"
    )

    await response_message.send()

    try:

        stream = LLMHelper.chat(messages)

        for chunk in stream:

            token = chunk.choices[0].delta.content

            if token:

                await response_message.stream_token(token)

        messages.append(
            {
                "role": "assistant",
                "content": response_message.content,
            }
        )

        await response_message.update()

    except Exception as e:

        error_message = f"❌ Errore: {str(e)}"

        await cl.Message(
            content=error_message
        ).send()

    cl.user_session.set("messages", messages)
