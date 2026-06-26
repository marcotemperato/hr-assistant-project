from unittest.mock import MagicMock, patch

from database import Database


def _make_db_with_collection(collection):
    db = Database.__new__(Database)
    db.collection = collection
    return db


def test_query_best_cv_chunks_empty_collection():
    collection = MagicMock()
    collection.query.return_value = {"documents": [[]], "metadatas": [[]]}

    db = _make_db_with_collection(collection)
    result = db.query_best_cv_chunks("python developer")

    assert result["source"] is None
    assert result["chunks"] == []
    assert result["combined_text"] == ""


def test_query_best_cv_chunks_returns_all_chunks_ordered():
    collection = MagicMock()
    collection.query.return_value = {
        "documents": [["best chunk"]],
        "metadatas": [[{"source": "marco_cv.txt", "chunk_index": 1}]],
    }
    collection.get.return_value = {
        "documents": ["chunk-b", "chunk-a", "chunk-c"],
        "metadatas": [
            {"source": "marco_cv.txt", "chunk_index": 1},
            {"source": "marco_cv.txt", "chunk_index": 0},
            {"source": "marco_cv.txt", "chunk_index": 2},
        ],
    }

    db = _make_db_with_collection(collection)
    result = db.query_best_cv_chunks("python developer")

    assert result["source"] == "marco_cv.txt"
    assert result["chunks"] == ["chunk-a", "chunk-b", "chunk-c"]
    assert result["combined_text"] == "chunk-a\n\nchunk-b\n\nchunk-c"


def test_query_best_cv_chunks_filters_by_best_source():
    collection = MagicMock()
    collection.query.return_value = {
        "documents": [["match"]],
        "metadatas": [[{"source": "winner.pdf", "chunk_index": 0}]],
    }
    collection.get.return_value = {
        "documents": ["only winner"],
        "metadatas": [{"source": "winner.pdf", "chunk_index": 0}],
    }

    db = _make_db_with_collection(collection)
    result = db.query_best_cv_chunks("data scientist")

    collection.get.assert_called_once_with(
        where={"source": "winner.pdf"},
        include=["documents", "metadatas"],
    )
    assert result["metadata"]["source"] == "winner.pdf"
