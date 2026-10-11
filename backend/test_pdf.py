from app.rag.pdf_processor import extract_text_from_pdf


PDF_PATH = "sample.pdf"


text = extract_text_from_pdf(PDF_PATH)

print("=" * 60)
print("EXTRACTED PDF TEXT")
print("=" * 60)

print(text)

print("=" * 60)
print(f"Characters extracted: {len(text)}")
print("=" * 60)