# Pharma AI Flutter application

Run the FastAPI backend at `http://127.0.0.1:8000`, then launch Flutter Web:

```powershell
flutter pub get
flutter run -d chrome --no-web-resources-cdn --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

`API_BASE_URL` is the single REST base URL; the WebSocket URL is derived from it. For HTTPS deployments use an HTTPS base URL so chat uses WSS. The backend allows local Flutter Web origins on localhost/127.0.0.1.

The `--no-web-resources-cdn` option bundles Flutter's rendering assets locally, so the app does not depend on Google CDN access to start.

Choose `LLM_PROVIDER=ollama` or `LLM_PROVIDER=openai` in `backend/.env`, configure model names there, and restart FastAPI. OpenAI credentials belong only in the backend `OPENAI_API_KEY` variable. Flutter reads safe model/provider names from `/api/v1/settings/provider`; it cannot set credentials or change providers at runtime.

Embeddings remain on Ollama by default. Choosing a different embedding provider/model uses a separate Chroma collection to prevent mixing incompatible vectors. Set the embedding provider/model, restart the backend, then run `python scripts/reindex_embeddings.py` from `backend` before relying on retrieval with the new embedding configuration. The script rewrites only each processed document's vectors in the selected collection and leaves the existing collection available for rollback.

Use the Exports section to select a saved conversation and download PDF or Excel. Files are generated in memory by the backend and downloaded by the browser.
