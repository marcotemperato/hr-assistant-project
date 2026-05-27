# document_processor.py
import os
import uuid
import re
from config import Config


class DocumentProcessor:

    @staticmethod
    def process_documents():

        documents = []
        metadatas = []
        ids = []

        for filename in os.listdir(Config.DOCUMENTS_DIR):

            if filename.endswith(".txt"):

                with open(
                    os.path.join(Config.DOCUMENTS_DIR, filename),
                    "r",
                    encoding="utf-8",
                ) as file:

                    chunks = file.read().replace("\n", " ").split("### ")

                    for chunk in chunks:

                        if chunk.strip():

                            documents.append(chunk)

                            metadatas.append({
                                "source": filename
                            })

                            ids.append(str(uuid.uuid4()))

        return documents, metadatas, ids

    @staticmethod
    def read_first_lines(file_path, num_lines=10):

        with open(file_path, "r", encoding="utf-8") as file:

            lines = []

            for i, line in enumerate(file):

                if i < num_lines:
                    lines.append(line.strip())
                else:
                    break

        return lines

    @staticmethod
    def extract_candidate_info(text):

        # ===== NOME =====

        lines = text.split("\n")

        candidate_name = "Nome non trovato"

        for line in lines:

            clean = line.strip()

            if len(clean.split()) >= 2:
                candidate_name = clean.title()
                break

        # ===== EMAIL =====

        email_match = re.search(
            r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
            text
        )

        email = email_match.group(0) if email_match else "Non trovata"

        # ===== TELEFONO =====

        phone_match = re.search(
            r"(\+39\s?\d{2,4}\s?\d{6,10})",
            text
        )

        phone = phone_match.group(0) if phone_match else "Non trovato"

        return {
            "name": candidate_name,
            "email": email,
            "phone": phone
        }