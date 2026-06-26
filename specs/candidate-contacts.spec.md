---
name: Candidate Contact Extraction
description: Local extraction of name, email, and phone from CV text without LLM calls
targets:
  - ../hr_assistant/document_processor.py
---

# Candidate Contact Extraction

Extract candidate contact details from plain-text or markdown CV content using local regex and heuristics only.

```python
def extract_candidate_info(document: str) -> dict[str, str | None]: ...
```

`[@test] ../tests/test_candidate_contacts.py`

## REQ-CONTACT-001 — Email extraction

- Scan the full document text for a valid email address.
- Return the first match as `email`, or `None` when absent.
  `[@test] ../tests/test_candidate_contacts.py`

## REQ-CONTACT-002 — Phone extraction

- Scan for Italian and international phone formats (`+39`, mobile `3xx`, landline `0xx`).
- Normalize to a compact string; return `None` when absent.
  `[@test] ../tests/test_candidate_contacts.py`

## REQ-CONTACT-003 — Name extraction

- Infer candidate name from header lines before section keywords (`esperienza`, `competenze`, etc.).
- Must not return an email address or phone number as the name.
  `[@test] ../tests/test_candidate_contacts.py`

## REQ-CONTACT-004 — Markdown source text

- `get_cv_text(file_path)` returns markdown/plain text via MarkItDown for any supported extension.
- Used instead of raw byte reads for contact extraction.
  `[@test] ../tests/test_candidate_contacts.py`
