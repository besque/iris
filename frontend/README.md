# Frontend

The web UI. Must let a user:
1. Upload 1–2 images (GeoTIFF/TIFF; PNG/JPEG for benchmark data)
2. See the validation result (modality detected, pair compatibility)
3. Type a natural-language query
4. See: text answer, image with overlays (boxes/masks/change map), confidence,
   and the execution summary (which task, which models, which params)
5. Download a report

Tech choice is open — two options:
- **Streamlit** (fast to build, good enough for the demo) — start here
- **React + the FastAPI backend** (nicer, more work) — switch later if time allows
