from langchain_core.documents import Document

from app.rag.pdf_processor import extract_text_from_pdf
from app.rag.chunker import split_text
from app.rag.vector_store import add_documents
from app.rag.chain import ask_question


PDF_PATH = "sample.pdf"


def ingest_pdf():
    print("\n1. Extracting PDF...")

    text = extract_text_from_pdf(PDF_PATH)

    print(f"Extracted characters: {len(text)}")

    print("\n2. Splitting into chunks...")

    chunks = split_text(text)

    print(f"Created chunks: {len(chunks)}")

    documents = []

    for index, chunk in enumerate(chunks):

        documents.append(
            Document(
                page_content=chunk,
                metadata={
                    "source": PDF_PATH,
                    "chunk_index": index,
                },
            )
        )

    print("\n3. Creating embeddings and storing in ChromaDB...")

    add_documents(documents)

    print("Documents successfully stored in ChromaDB.")


def run_question():

    print("\n4. Asking question...")

    question = input("\nEnter your question: ")

    result = ask_question(question)

    print("\n" + "=" * 60)
    print("ANSWER")
    print("=" * 60)

    print(result["answer"])

    print("\n" + "=" * 60)
    print("SOURCES")
    print("=" * 60)

    for source in result["sources"]:
        print(source)


if __name__ == "__main__":

    ingest_pdf()

    run_question()