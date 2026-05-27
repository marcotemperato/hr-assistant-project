# utils.py
import re
from openai import OpenAI
from config import Config


class LLMHelper:

    client = OpenAI(
        api_key=Config.AI_API_KEY,
        base_url=Config.AI_API_URL,
    )

    @staticmethod
    def extract_candidate_info(text):

        # EMAIL
        email_match = re.search(
            r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
            text
        )

        email = email_match.group(0) if email_match else "Non trovata"

        # TELEFONO
        phone_match = re.search(
            r"(\+39\s?\d{2,4}\s?\d{6,10})",
            text
        )

        phone = phone_match.group(0) if phone_match else "Non trovato"

        # NOME
        lines = text.split("\n")

        candidate_name = "Nome non trovato"

        for line in lines:
            clean_line = line.strip()

            if len(clean_line.split()) >= 2:
                candidate_name = clean_line.title()
                break

        return {
            "name": candidate_name,
            "email": email,
            "phone": phone,
        }

    @staticmethod
    def create_prompt(context, user_question, candidate_info):

        return f"""
        Dato il seguente contesto:

        {context}

        Rispondi alla domanda:
        {user_question}

        Il candidato più adatto è:

        Nome: {candidate_info["name"]}
        Email: {candidate_info["email"]}
        Telefono: {candidate_info["phone"]}

        Motiva la scelta usando il contenuto del CV.

        NON inventare informazioni.
        """

    @staticmethod
    def chat(messages):

        return LLMHelper.client.chat.completions.create(
            model=Config.LLM_MODEL,
            messages=messages,
            stream=True,
        )