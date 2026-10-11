# Controlled RAG App

Starter workspace for a controlled retrieval-augmented generation application.

## Project layout

- `frontend/pharma_app/`: Flutter application.
- `backend/`: FastAPI service and backend tests.
- `docs/`: architecture, API, and database documentation.
- `scripts/`: project utility scripts.
- `tests/`: cross-project tests.

## Run the backend

From `backend/`, install `requirements.txt`, copy `.env.example` to `.env`, and run `uvicorn app.main:app --reload`.

## Run the Flutter app

From `frontend/pharma_app/`, run `flutter pub get` followed by `flutter run`.