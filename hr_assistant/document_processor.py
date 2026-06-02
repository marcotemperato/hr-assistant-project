# document_processor.py

import os
import uuid
import hashlib
import tempfile
import mimetypes

from markitdown import MarkItDown
from zipfile import ZipFile

from config import Config
from semantic_chunking import SemanticChunking


class DocumentProcessor:

    SUPPORTED_EXTENSIONS = {
        ".txt": "text",
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
    def read_first_lines(file_path, n_lines=100):

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as file:

                return [
                    line.strip()
                    for line, _ in zip(file, range(n_lines))
                ]

        except Exception:

            return []

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

        except Exception as e:

            print(
                f"Errore conversione {file_path}: {e}"
            )

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

        for chunk in chunks:

            if chunk and not chunk.isspace():

                documents.append(chunk)

                metadatas.append(
                    file_metadata
                )

                ids.append(
                    str(uuid.uuid4())
                )

        return documents, metadatas, ids

    @staticmethod
    def extract_candidate_info(document):

        lines = document.split("\n")

        candidate_name = "Candidato"

        for line in lines:

            line = line.strip()

            if len(line) > 3 and len(line) < 50:

                if not any(
                    word in line.lower()
                    for word in [
                        "profilo",
                        "esperienza",
                        "competenze",
                        "curriculum",
                        "email",
                        "telefono",
                    ]
                ):

                    candidate_name = line

                    break

        return {
            "name": candidate_name
        }

    @staticmethod
    def process_documents(db):

        current_files = {

            f: DocumentProcessor.get_document_metadata(
                os.path.join(
                    Config.DOCUMENTS_DIR,
                    f
                )
            )

            for f in os.listdir(
                Config.DOCUMENTS_DIR
            )

            if (
                os.path.splitext(f)[1].lower()
                in
                DocumentProcessor.SUPPORTED_EXTENSIONS
            )
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