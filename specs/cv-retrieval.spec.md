---
name: CV Retrieval
description: Retrieve all chunks from the best-matching CV for a recruiter query
targets:
  - ../hr_assistant/database.py
  - ../hr_assistant/__init__.py
---

# CV Retrieval

After a recruiter query, return the complete content of the single best-matching CV.

```python
def query_best_cv_chunks(query_text: str) -> dict: ...
```

`[@test] ../tests/test_cv_retrieval.py`

## REQ-RETRIEVE-001 — Best source selection

- Use vector search to identify the top-matching chunk and its `source` file.
- Return empty result when no documents are indexed.
  `[@test] ../tests/test_cv_retrieval.py`

## REQ-RETRIEVE-002 — All chunks from best CV

- Fetch every chunk whose `source` matches the best match.
- Order chunks by `chunk_index` ascending.
- Provide `combined_text` joining all chunks with double newlines.
  `[@test] ../tests/test_cv_retrieval.py`

## REQ-RETRIEVE-003 — Prompt context

- The chat handler passes `combined_text` (not a single chunk) to the LLM prompt.
- Contact extraction uses full CV markdown text from the matched file.
  `[@test] ../tests/test_cv_retrieval.py`
