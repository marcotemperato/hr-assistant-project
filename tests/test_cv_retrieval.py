from unittest.mock import MagicMock

from database import Database


def _make_db_with_collection(collection):
    db = Database.__new__(Database)
    db.collection = collection
    return db


def test_query_best_cv_chunks_empty_collection():
    collection = MagicMock()
    collection.count.return_value = 0

    db = _make_db_with_collection(collection)
    result = db.query_best_cv_chunks("python developer")

    assert result["source"] is None
    assert result["chunks"] == []
    assert result["combined_text"] == ""
    collection.query.assert_not_called()


def test_query_best_cv_chunks_returns_all_chunks_ordered():
    collection = MagicMock()
    collection.count.return_value = 5
    collection.query.return_value = {
        "documents": [["best chunk"]],
        "metadatas": [[{"source": "marco_cv.txt", "chunk_index": 1}]],
        "distances": [[0.12]],
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
    assert result["score"] == 0.12


def test_query_best_cv_chunks_picks_best_source_by_distance():
    collection = MagicMock()
    collection.count.return_value = 10
    collection.query.return_value = {
        "documents": [["a", "b", "c"]],
        "metadatas": [[
            {"source": "weak.txt", "chunk_index": 0},
            {"source": "winner.pdf", "chunk_index": 1},
            {"source": "winner.pdf", "chunk_index": 0},
        ]],
        "distances": [[0.8, 0.2, 0.25]],
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
    assert result["score"] == 0.2
