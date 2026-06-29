# document_processor.py

import os
import re
import uuid
import hashlib
import tempfile
import mimetypes

from markitdown import MarkItDown
from zipfile import ZipFile

from config import Config
from semantic_chunking import SemanticChunking

EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
)
PHONE_PATTERN = re.compile(
    r"(?:\+39[\s.-]?)?(?:3\d{2}[\s.-]?\d{6,7}|0\d{1,4}[\s.-]?\d{6,8})"
)
NAME_SKIP_KEYWORDS = {
    "profilo",
    "esperienza",
    "competenze",
    "curriculum",
    "email",
    "telefono",
    "vitae",
    "resume",
    "cv",
    "indirizzo",
    "address",
}


class DocumentProcessor:

    SUPPORTED_EXTENSIONS = {
        ".txt": "text",
        ".md": "text",
        ".pdf": "document",
        ".doc": "document",
        ".docx": "document",
        ".ppt": "presentation",
        ".pptx": "presentation",
        ".xls": "spreadsheet",
        ".xlsx": "spreadsheet",
        ".html": "web",
        ".htm": "web",
        ".csv": "data",
        ".json": "data",
        ".xml": "data",
        ".zip": "archive",
    }

    @staticmethod
    def get_cv_text(file_path):
        extension = os.path.splitext(file_path)[1].lower()
        file_type = DocumentProcessor.SUPPORTED_EXTENSIONS.get(extension)

        if not file_type:
            return ""

        if file_type == "archive":
            parts = []
            for filename, content in DocumentProcessor._process_zip_file(file_path):
                parts.append(f"File: {filename}\n{content}")
            return "\n\n".join(parts)

        return DocumentProcessor._convert_to_markdown(file_path)

    @staticmethod
    def get_file_hash(file_path):

        hash_md5 = hashlib.md5()

        with open(file_path, "rb") as f:

            for chunk in iter(
                lambda: f.read(4096),
                b""
            ):
                hash_md5.update(chunk)

        return hash_md5.hexdigest()

    @staticmethod
    def get_document_metadata(file_path):

        extension = os.path.splitext(
            file_path
        )[1].lower()

        file_type = (
            DocumentProcessor
            .SUPPORTED_EXTENSIONS
            .get(extension, "unknown")
        )

        return {
            "hash": DocumentProcessor.get_file_hash(
                file_path
            ),
            "last_modified": os.path.getmtime(
                file_path
            ),
            "source": os.path.basename(
                file_path
            ),
            "file_type": file_type,
            "mime_type": mimetypes.guess_type(
                file_path
            )[0],
            "extension": extension,
        }

    @staticmethod
    def _convert_to_markdown(file_path):

        try:

            result = MarkItDown().convert(
                file_path
            )

            return result.text_content

        except Exception:
            return ""

    @staticmethod
    def _process_zip_file(file_path):

        results = []

        with tempfile.TemporaryDirectory() as temp_dir:

            with ZipFile(file_path, "r") as zip_ref:

                zip_ref.extractall(temp_dir)

                for root, _, files in os.walk(
                    temp_dir
                ):

                    for file in files:

                        inner_path = os.path.join(
                            root,
                            file
                        )

                        ext = os.path.splitext(
                            file
                        )[1].lower()

                        if (
                            ext
                            in
                            DocumentProcessor.SUPPORTED_EXTENSIONS
                        ):

                            content = (
                                DocumentProcessor
                                ._convert_to_markdown(
                                    inner_path
                                )
                            )

                            if content:

                                results.append(
                                    (
                                        file,
                                        content
                                    )
                                )

        return results

    @staticmethod
    def process_single_document(file_path):

        documents = []
        metadatas = []
        ids = []

        extension = os.path.splitext(
            file_path
        )[1].lower()

        file_type = (
            DocumentProcessor
            .SUPPORTED_EXTENSIONS
            .get(extension)
        )

        if not file_type:

            return [], [], []

        content = ""

        if file_type == "archive":

            zip_contents = (
                DocumentProcessor
                ._process_zip_file(
                    file_path
                )
            )

            for filename, zip_content in zip_contents:

                content += (
                    f"\n\nFile: {filename}\n"
                    f"{zip_content}"
                )

        else:

            content = (
                DocumentProcessor
                ._convert_to_markdown(
                    file_path
                )
            )

        if not content:

            return [], [], []

        sc = SemanticChunking()

        chunks = sc.chunk_text(content)

        file_metadata = (
            DocumentProcessor
            .get_document_metadata(
                file_path
            )
        )

        for chunk_index, chunk in enumerate(chunks):

            if chunk and not chunk.isspace():

                documents.append(chunk)

                metadata = dict(file_metadata)
                metadata["chunk_index"] = chunk_index

                metadatas.append(metadata)

                ids.append(
                    str(uuid.uuid4())
                )

        return documents, metadatas, ids

    @staticmethod
    def _normalize_phone(raw_phone):
        digits = re.sub(r"\D", "", raw_phone)
        if digits.startswith("39") and len(digits) > 10:
            digits = digits[2:]
        return digits if digits else None

    @staticmethod
    def extract_candidate_info(document):

        email_match = EMAIL_PATTERN.search(document)
        email = email_match.group(0) if email_match else None

        phone_match = PHONE_PATTERN.search(document)
        phone = (
            DocumentProcessor._normalize_phone(phone_match.group(0))
            if phone_match
            else None
        )

        candidate_name = None

        for line in document.split("\n"):
            line = line.strip()
            if not line or len(line) < 3 or len(line) > 60:
                continue
            if EMAIL_PATTERN.search(line) or PHONE_PATTERN.search(line):
                continue
            lower = line.lower()
            if any(keyword in lower for keyword in NAME_SKIP_KEYWORDS):
                continue
            if line.startswith(("#", "-", "*", "|")):
                continue
            candidate_name = line
            break

        if not candidate_name and email:
            local_part = email.split("@")[0].replace(".", " ").replace("_", " ")
            candidate_name = local_part.title()

        return {
            "name": candidate_name or "Candidato",
            "email": email,
            "phone": phone,
        }

    @staticmethod
    def list_cv_filenames():
        if not os.path.isdir(Config.DOCUMENTS_DIR):
            return [], []

        supported = []
        skipped = []

        for filename in sorted(os.listdir(Config.DOCUMENTS_DIR)):
            file_path = os.path.join(Config.DOCUMENTS_DIR, filename)
            if not os.path.isfile(file_path):
                continue

            extension = os.path.splitext(filename)[1].lower()
            if extension in DocumentProcessor.SUPPORTED_EXTENSIONS:
                supported.append(filename)
            else:
                skipped.append(filename)

        return supported, skipped

    @staticmethod
    def process_documents(db):

        if not os.path.isdir(Config.DOCUMENTS_DIR):
            os.makedirs(Config.DOCUMENTS_DIR, exist_ok=True)
            return (0, 0, 0)

        supported_filenames, _ = DocumentProcessor.list_cv_filenames()

        current_files = {
            filename: DocumentProcessor.get_document_metadata(
                os.path.join(Config.DOCUMENTS_DIR, filename)
            )
            for filename in supported_filenames
        }

        existing_files = db.get_tracked_files()

        files_to_add = (
            set(current_files.keys())
            -
            set(existing_files.keys())
        )

        files_to_remove = (
            set(existing_files.keys())
            -
            set(current_files.keys())
        )

        files_to_update = {

            f

            for f in (
                set(current_files.keys())
                &
                set(existing_files.keys())
            )

            if (
                current_files[f]["hash"]
                !=
                existing_files[f]["hash"]
            )
        }

        for action, files in [

            ("add", files_to_add),

            ("update", files_to_update),

        ]:

            for filename in files:

                file_path = os.path.join(
                    Config.DOCUMENTS_DIR,
                    filename
                )

                (
                    documents,
                    metadatas,
                    ids,
                ) = (
                    DocumentProcessor
                    .process_single_document(
                        file_path
                    )
                )

                if action == "update":

                    db.remove_document_by_source(
                        filename
                    )

                if documents:

                    db.add_documents(
                        documents,
                        metadatas,
                        ids
                    )

        for filename in files_to_remove:

            db.remove_document_by_source(
                filename
            )

        return (
            len(files_to_add),
            len(files_to_update),
            len(files_to_remove),
        )
