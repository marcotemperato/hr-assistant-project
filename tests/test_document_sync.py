from unittest.mock import MagicMock, patch

from document_processor import DocumentProcessor


class FakeDatabase:
    def __init__(self):
        self.documents = []
        self.removed_sources = []

    def get_tracked_files(self):
        return {
            doc["source"]: {"hash": doc["hash"], "source": doc["source"]}
            for doc in self.documents
        }

    def add_documents(self, documents, metadatas, ids):
        for metadata in metadatas:
            self.documents.append(
                {
                    "source": metadata["source"],
                    "hash": metadata["hash"],
                    "chunk_index": metadata.get("chunk_index", 0),
                }
            )

    def remove_document_by_source(self, source):
        self.removed_sources.append(source)
        self.documents = [
            doc for doc in self.documents if doc["source"] != source
        ]


@patch.object(DocumentProcessor, "process_single_document")
def test_process_documents_adds_new_files(mock_process, tmp_path):
    resumes_dir = tmp_path / "resumes"
    resumes_dir.mkdir()
    (resumes_dir / "new_cv.txt").write_text("content", encoding="utf-8")

    mock_process.return_value = (
        ["chunk"],
        [{"source": "new_cv.txt", "hash": "abc", "chunk_index": 0}],
        ["id-1"],
    )

    db = FakeDatabase()

    with patch("document_processor.Config") as mock_config:
        mock_config.DOCUMENTS_DIR = str(resumes_dir)
        added, updated, removed = DocumentProcessor.process_documents(db)

    assert added == 1
    assert updated == 0
    assert removed == 0
    assert db.documents[0]["chunk_index"] == 0


@patch.object(DocumentProcessor, "process_single_document")
def test_process_documents_removes_deleted_files(mock_process, tmp_path):
    resumes_dir = tmp_path / "resumes"
    resumes_dir.mkdir()

    db = FakeDatabase()
    db.documents.append({"source": "old_cv.txt", "hash": "old", "chunk_index": 0})

    with patch("document_processor.Config") as mock_config:
        mock_config.DOCUMENTS_DIR = str(resumes_dir)
        added, updated, removed = DocumentProcessor.process_documents(db)

    assert added == 0
    assert updated == 0
    assert removed == 1
    assert db.removed_sources == ["old_cv.txt"]


@patch.object(DocumentProcessor, "process_single_document")
def test_process_documents_updates_changed_hash(mock_process, tmp_path):
    resumes_dir = tmp_path / "resumes"
    resumes_dir.mkdir()
    cv_path = resumes_dir / "cv.txt"
    cv_path.write_text("version one", encoding="utf-8")

    db = FakeDatabase()
    old_hash = DocumentProcessor.get_file_hash(str(cv_path))
    db.documents.append({"source": "cv.txt", "hash": "stale-hash", "chunk_index": 0})

    cv_path.write_text("version two", encoding="utf-8")
    new_hash = DocumentProcessor.get_file_hash(str(cv_path))

    mock_process.return_value = (
        ["chunk-a", "chunk-b"],
        [
            {"source": "cv.txt", "hash": new_hash, "chunk_index": 0},
            {"source": "cv.txt", "hash": new_hash, "chunk_index": 1},
        ],
        ["id-1", "id-2"],
    )

    with patch("document_processor.Config") as mock_config:
        mock_config.DOCUMENTS_DIR = str(resumes_dir)
        added, updated, removed = DocumentProcessor.process_documents(db)

    assert added == 0
    assert updated == 1
    assert removed == 0
    assert db.removed_sources == ["cv.txt"]
    assert len(db.documents) == 2


from pathlib import Path


def test_sync_runs_on_chat_start_not_import():
    source = Path("hr_assistant/__init__.py").read_text(encoding="utf-8")
    before_chat_start, after_chat_start = source.split("@cl.on_chat_start", 1)

    assert "process_documents" not in before_chat_start
    assert "process_documents" in after_chat_start
