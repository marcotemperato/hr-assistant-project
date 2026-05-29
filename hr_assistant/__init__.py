import os
import chainlit as cl

from document_processor import DocumentProcessor
from database import Database
from config import Config
from utils import LLMHelper

db = Database()

added, updated, removed = DocumentProcessor.process_documents(db)

print(
    f"Document sync complete: "
    f"{added} added, "
    f"{updated} updated, "
    f"{removed} removed"
)


@cl.on_chat_start
async def start():

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
    ]

    await cl.Message(
        content="✅ HR Assistant avviato correttamente.",
        actions=actions,
    ).send()


@cl.action_callback("show_db")
async def show_db(action):

    files = [
        f
        for f in os.listdir(Config.DOCUMENTS_DIR)
        if f.endswith(".txt")
    ]

    if not files:

        await cl.Message(
            content="❌ Nessun CV trovato."
        ).send()

        return

    response = "📂 DOCUMENTI NEL DATABASE:\n\n"

    for index, filename in enumerate(files, start=1):

        file_path = os.path.join(
            Config.DOCUMENTS_DIR,
            filename,
        )

        lines = DocumentProcessor.read_first_lines(
            file_path,
            3,
        )

        preview = " ".join(lines)

        response += f"{index}. {preview}\n\n"

    await cl.Message(content=response).send()


@cl.action_callback("count_cv")
async def count_cv(action):

    files = [
        f
        for f in os.listdir(Config.DOCUMENTS_DIR)
        if f.endswith(".txt")
    ]

    await cl.Message(
        content=f"📊 CV presenti nel database: {len(files)}"
    ).send()


@cl.on_message
async def handle_message(message: cl.Message):

    user_question = message.content

    results = db.query(user_question)

    print("RESULT DB:", results)

    if not results["documents"][0]:

        await cl.Message(
            content="❌ Nessun candidato trovato."
        ).send()

        return

    best_document = results["documents"][0][0]

    metadata = results["metadatas"][0][0]

    filename = metadata["source"]
    
    context_lines = DocumentProcessor.read_first_lines(
    os.path.join(Config.DOCUMENTS_DIR, filename),
    80,
    )

    candidate_info = DocumentProcessor.extract_candidate_info(
        "\n".join(context_lines)
    )

    prompt = f"""
        Sei un recruiter HR esperto.

        IMPORTANTE:
        - Devi SEMPRE indicare il nome del candidato.
        - Se il nome non è disponibile usa il nome file.
        - Devi spiegare perchè è adatto.

        NOME CANDIDATO:
        {candidate_info.get('name', 'Non trovato')}

        EMAIL:
        {candidate_info.get('email', 'Non trovata')}

        TELEFONO:
        {candidate_info.get('phone', 'Non trovato')}

        NOME FILE:
        {filename}

        CONTENUTO CV:
        {best_document}

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
    
    response_message.content = f"📄 CV trovato: {filename}\n\n"
    
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

        print(error_message)

        await cl.Message(
            content=error_message
        ).send()

    cl.user_session.set("messages", messages)