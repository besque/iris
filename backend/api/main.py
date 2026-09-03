"""FastAPI server — the endpoints the frontend talks to.

Planned endpoints:
- POST /upload   -> upload image(s), run validation, return config type
- POST /query    -> {session_id, query} -> answer + evidence + trace
- GET  /report/{session_id} -> downloadable report (JSON/PDF)
"""

from fastapi import FastAPI

app = FastAPI(title="SatQuery AI")


@app.get("/health")
def health():
    return {"status": "ok"}
