from document_processor import DocumentProcessor


SAMPLE_CV = """
Marco Rossi
marco.rossi@email.it
+39 333 1234567

## Esperienza
Sviluppatore Python con 5 anni di esperienza.
"""


def test_extract_email():
    info = DocumentProcessor.extract_candidate_info(SAMPLE_CV)
    assert info["email"] == "marco.rossi@email.it"


def test_extract_phone():
    info = DocumentProcessor.extract_candidate_info(SAMPLE_CV)
    assert info["phone"] == "3331234567"


def test_extract_name():
    info = DocumentProcessor.extract_candidate_info(SAMPLE_CV)
    assert info["name"] == "Marco Rossi"


def test_name_not_email_or_phone():
    cv = "info@company.it\n+39 02 12345678\nLuca Bianchi\nCompetenze: Java"
    info = DocumentProcessor.extract_candidate_info(cv)
    assert info["name"] == "Luca Bianchi"
    assert "@" not in info["name"]


def test_missing_contacts_return_none():
    cv = "Anna Verdi\n\nEsperienza professionale nel settore HR."
    info = DocumentProcessor.extract_candidate_info(cv)
    assert info["name"] == "Anna Verdi"
    assert info["email"] is None
    assert info["phone"] is None


def test_get_cv_text_reads_plain_text(tmp_path):
    cv_file = tmp_path / "cv.txt"
    cv_file.write_text("Paolo Neri\npaolo@example.com", encoding="utf-8")

    text = DocumentProcessor.get_cv_text(str(cv_file))

    assert "Paolo Neri" in text
    assert "paolo@example.com" in text
