import pymupdf


def validate_pdf_file(file_path: str) -> None:
    """Reject files that are not readable PDF documents."""
    try:
        with open(file_path, "rb") as pdf_file:
            if pdf_file.read(5) != b"%PDF-":
                raise ValueError("Uploaded file is not a valid PDF.")

        document = pymupdf.open(file_path)
        try:
            if document.is_encrypted:
                raise ValueError("Encrypted PDFs are not supported.")
            if document.page_count == 0:
                raise ValueError("PDF contains no pages.")
        finally:
            document.close()
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Uploaded file is not a readable PDF.") from exc


def extract_pages_from_pdf(file_path: str) -> list[dict]:
    """
    Extract text from a PDF while preserving page numbers.
    """

    document = pymupdf.open(file_path)

    pages = []

    try:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text().strip()

            if text:
                pages.append(
                    {
                        "page_number": page_number,
                        "text": text,
                    }
                )

    finally:
        document.close()

    return pages


def extract_text_from_pdf(file_path: str) -> str:
    """
    Backward-compatible helper that returns the full PDF text.
    """

    pages = extract_pages_from_pdf(file_path)

    return "\n\n".join(
        page["text"]
        for page in pages
    )
