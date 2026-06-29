import asyncio
import os
import shutil

import chainlit as cl

from document_processor import DocumentProcessor
from database import Database
from config import Config
from utils import LLMHelper

db = Database()

_CHAT_ACTIONS = [
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

SYSTEM_PROMPT = """
Sei un assistente HR per la selezione dei candidati.

REGOLE OBBLIGATORIE:
1. Usa SOLO le informazioni presenti nel CV fornito.
2. Non inventare competenze, esperienze, titoli o contatti.
3. Se una informazione richiesta non è nel CV, scrivi esplicitamente che non è indicata.
4. Cita evidenze concrete dal CV (competenze, ruoli, anni, tecnologie).
5. Rispondi sempre in italiano, tono professionale e diretto.

FORMATO RISPOSTA:
**Candidato:** nome
**Contatti:** email e telefono (se presenti nel CV)
**Perché è adatto:** 2-4 punti con evidenze dal CV
**Gap rispetto alla richiesta:** cosa manca o non è chiaro nel CV
"""


def _format_user_prompt(user_question, filename, candidate_info, cv_text):
    return f"""DOMANDA DEL RECRUITER:
{user_question}

FILE CV SELEZIONATO:
{filename}

CONTATTI ESTRATTI DAL CV:
- Nome: {candidate_info.get('name', 'Non trovato')}
- Email: {candidate_info.get('email') or 'Non indicata'}
- Telefono: {candidate_info.get('phone') or 'Non indicato'}

TESTO COMPLETO DEL CV:
{cv_text}
"""


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


async def _await_document_sync():
    sync_task = cl.user_session.get("sync_task")
    if sync_task is not None and not sync_task.done():
        wait_message = cl.Message(content="⏳ Indicizzazione CV in corso, attendo...")
        await wait_message.send()
        await sync_task


@cl.on_chat_start
async def start():

    try:
        Config.validate_api_keys()
    except ValueError as error:
        await cl.Message(content=f"❌ {error}").send()
        return

    cl.user_session.set("messages", [])
    cl.user_session.set("sync_done", False)

    welcome = cl.Message(
        content="✅ HR Assistant avviato. ⏳ Indicizzazione CV in corso...",
        actions=_CHAT_ACTIONS,
    )
    await welcome.send()

    async def complete_sync():
        try:
            added, updated, removed = await asyncio.to_thread(
                DocumentProcessor.process_documents, db
            )
            tracked = db.get_tracked_files()
            supported, skipped = DocumentProcessor.list_cv_filenames()
            not_indexed = sorted(set(supported) - set(tracked.keys()))
            sync_summary = ""
            if any((added, updated, removed)):
                sync_summary = (
                    f"\n\n📁 Sync CV: {added} aggiunti, "
                    f"{updated} aggiornati, {removed} rimossi."
                )
            if not_indexed:
                sync_summary += (
                    f"\n\n⚠️ Non indicizzati (contenuto vuoto o errore): "
                    f"{', '.join(not_indexed)}"
                )
            if skipped:
                sync_summary += (
                    f"\n\n⚠️ File ignorati (formato non supportato): "
                    f"{', '.join(skipped)}"
                )
            welcome.content = (
                f"✅ HR Assistant pronto. {len(tracked)} CV indicizzati."
                f"{sync_summary}"
            )
        except Exception as error:
            welcome.content = (
                "⚠️ HR Assistant avviato, ma indicizzazione fallita: "
                f"{error}"
            )
        finally:
            cl.user_session.set("sync_done", True)
        await welcome.update()

    cl.user_session.set(
        "sync_task",
        asyncio.create_task(complete_sync()),
    )


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

    tracked = db.get_tracked_files()
    supported, skipped = DocumentProcessor.list_cv_filenames()
    not_indexed = sorted(set(supported) - set(tracked.keys()))

    response = (
        f"📊 CV indicizzati nel database: {len(tracked)}\n"
        f"📁 File supportati in cartella: {len(supported)}"
    )
    if not_indexed:
        response += (
            f"\n⚠️ Non indicizzati: {', '.join(not_indexed)}"
        )
    if skipped:
        response += (
            f"\n⚠️ File ignorati: {', '.join(skipped)}"
        )

    await cl.Message(content=response).send()


@cl.action_callback("reset_db")
async def reset_db(action):

    db.reset_database()

    await cl.Message(
        content="✅ Database svuotato correttamente."
    ).send()


@cl.on_message
async def handle_message(message: cl.Message):

    await _await_document_sync()

    if message.elements:

        results = []

        for file in message.elements:

            result = await upload_file(file)

            results.append(result)

        await cl.Message(
            content="\n".join(results)
        ).send()

        return

    user_question = message.content.strip()

    if not user_question:
        await cl.Message(content="Scrivi una domanda sul candidato ideale.").send()
        return

    try:
        match = db.query_best_cv_chunks(user_question)
    except Exception as error:
        error_text = str(error).lower()
        if "authentication" in error_text or "api key" in error_text or "401" in error_text:
            await cl.Message(
                content=(
                    "❌ API key OpenAI non valida. "
                    "Controlla OPENAI_API_KEY in .env."
                )
            ).send()
            return
        await cl.Message(content=f"❌ Errore ricerca CV: {error}").send()
        return

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

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": _format_user_prompt(
                user_question,
                filename,
                candidate_info,
                match["combined_text"],
            ),
        },
    ]

    response_message = cl.Message(content="")

    score_hint = ""
    if match.get("score") is not None:
        score_hint = f" | rilevanza: {match['score']:.3f}"

    response_message.content = (
        f"📄 CV selezionato: {filename} "
        f"({len(match['chunks'])} sezioni{score_hint})\n\n"
    )

    await response_message.send()

    try:

        stream = LLMHelper.chat(messages)

        for chunk in stream:

            token = chunk.choices[0].delta.content

            if token:

                await response_message.stream_token(token)

        await response_message.update()

    except Exception as e:

        error_message = f"❌ Errore generazione risposta: {str(e)}"

        await cl.Message(
            content=error_message
        ).send()
