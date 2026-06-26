---
name: Document Sync
description: Hash-based CV folder sync with ChromaDB, triggered on chat start
targets:
  - ../hr_assistant/document_processor.py
  - ../hr_assistant/__init__.py
---

# Document Sync

Keep the vector database aligned with files in `resumes/` using MD5 hashes.

```python
def process_documents(db) -> tuple[int, int, int]: ...
```

`[@test] ../tests/test_document_sync.py`

## REQ-SYNC-001 — Detect changes

- Compare filesystem files against `db.get_tracked_files()` by hash.
- Return counts of added, updated, and removed files.
  `[@test] ../tests/test_document_sync.py`

## REQ-SYNC-002 — Add and update

- New files are chunked and indexed.
- Changed files remove old chunks by `source`, then re-index.
  `[@test] ../tests/test_document_sync.py`

## REQ-SYNC-003 — Remove deleted files

- Files removed from `resumes/` delete all associated chunks from the database.
  `[@test] ../tests/test_document_sync.py`

## REQ-SYNC-004 — Chat-start trigger

- Document sync must NOT run at module import time.
- Sync runs once per session inside `@cl.on_chat_start`.
  `[@test] ../tests/test_document_sync.py`

## REQ-SYNC-005 — Chunk index metadata

- Each chunk stores `chunk_index` in metadata for ordered reassembly.
  `[@test] ../tests/test_document_sync.py`
