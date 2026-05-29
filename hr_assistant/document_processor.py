# document_processor.py
import os
import uuid
import hashlib
from datetime import datetime

from numpy.ma import ids
from config import Config
from semantic_chunking import SemanticChunking


class DocumentProcessor:

    @staticmethod
    def read_first_lines(file_path, n_lines=100):
        with open(file_path, "r") as file:
            return [line.strip() for line, _ in zip(file, range(n_lines))]
        
    @staticmethod
    def extract_candidate_info(text):

        lines = text.split("\n")

        return {
            "name": lines[0] if len(lines) > 0 else "N/A",
            "email": "N/A",
            "phone": "N/A",
        }

    @staticmethod
    def get_file_hash(file_path):
        """Calculate MD5 hash of file content"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @staticmethod
    def get_document_metadata(file_path):
        """Get document metadata including hash and last modified time"""
        return {
            "hash": DocumentProcessor.get_file_hash(file_path),
            "last_modified": os.path.getmtime(file_path),
            "source": os.path.basename(file_path),
        }

    @staticmethod
    def process_single_document(file_path):

        documents = []
        metadatas = []
        ids = []

        with open(file_path, "r", encoding="utf-8") as file:

            text = file.read()

            sc = SemanticChunking()

            chunks = sc.chunk_text(text)

            file_metadata = DocumentProcessor.get_document_metadata(
            file_path
            )

        for chunk in chunks:

                if chunk and not chunk.isspace():

                    documents.append(chunk)

                    metadatas.append(file_metadata)

                    ids.append(str(uuid.uuid4()))

        return documents, metadatas, ids


        
    @staticmethod
    def extract_candidate_info(text):

        lines = text.split("\n")

        candidate = {
            "name": "Non trovato",
            "email": "Non trovata",
            "phone": "Non trovato",
        }

        for line in lines:

            clean_line = line.strip()

            lower = clean_line.lower()

            # Nome
            if (
                lower.startswith("nome:")
                or lower.startswith("name:")
            ):

                candidate["name"] = clean_line.split(
                    ":",
                    1
                )[1].strip()

            # Email
            if "@" in clean_line:

                candidate["email"] = clean_line

            # Telefono
            if (
                "telefono" in lower
                or "phone" in lower
                or "+39" in clean_line
            ):

                candidate["phone"] = clean_line

        return candidate
        
    @staticmethod
    def process_documents(db):
        """Process documents and sync with database"""
        # Get current files in directory
        current_files = {
            f: DocumentProcessor.get_document_metadata(
                os.path.join(Config.DOCUMENTS_DIR, f)
            )
            for f in os.listdir(Config.DOCUMENTS_DIR)
            if f.endswith(".txt")
        }

        # Get existing files from database
        existing_files = db.get_tracked_files()

        # Identify files to add, update, and remove
        files_to_add = set(current_files.keys()) - set(existing_files.keys())
        files_to_remove = set(existing_files.keys()) - set(current_files.keys())

        files_to_update = {
            f
            for f in set(current_files.keys()) & set(existing_files.keys())
            if current_files[f]["hash"] != existing_files[f]["hash"]
        }

        # Process updates
        for action, files in [("add", files_to_add), ("update", files_to_update)]:
            for filename in files:
                file_path = os.path.join(Config.DOCUMENTS_DIR, filename)
                documents, metadatas, ids = DocumentProcessor.process_single_document(
                    file_path
                )

                if action == "update":
                    # Remove old entries first
                    db.remove_document_by_source(filename)

                # Add new entries
                if documents:
                    db.add_documents(documents, metadatas, ids)

        # Remove deleted files from database
        for filename in files_to_remove:
            db.remove_document_by_source(filename)

        return len(files_to_add), len(files_to_update), len(files_to_remove)
    
    
    @staticmethod
    def extract_candidate_info(document):
        lines = document.split("\n")

        candidate_name = "Candidato"

        for line in lines:
            line = line.strip()

            if len(line) > 3 and len(line) < 50:
                if not any(word in line.lower() for word in [
                    "profilo",
                    "esperienza",
                    "competenze",
                    "curriculum",
                    "email",
                    "telefono"
                ]):
                    candidate_name = line
                    break

        return {
            "name": candidate_name
        }
