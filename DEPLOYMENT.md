# Deploy to Render

This project deploys both the Flask backend and the Vite React frontend to Render.

## What’s included
- `Backend/Dockerfile`: Container for Flask (with Tesseract OCR, OpenCV libs) running via Gunicorn.
- `Backend/requirements.txt`: Includes Flask, gunicorn, OCR and analytics deps.
- `render.yaml`: Defines two services:
  - backend: Dockerized web service, health check `/expenses/balance`.
  - frontend: Static site from `my-chalkboard-cash/dist`, with `VITE_API_BASE_URL` wired to backend URL.

## Steps
1. Push this repo to GitHub.
2. Create a new Render Blueprint deployment using `render.yaml` (Render → New + → Blueprint).
3. Render will build:
   - Backend image, install Tesseract, run `gunicorn app:app` on `$PORT`.
   - Frontend with `npm ci && npm run build`, publish `dist/`.
4. The frontend will fetch API from the backend via `VITE_API_BASE_URL`.

## Notes
- Backend OCR requires Tesseract; the Dockerfile installs it (`tesseract-ocr`).
- If you need a different region/plan, edit `render.yaml`.
- To switch frontend to live API locally, set `VITE_API_BASE_URL`.