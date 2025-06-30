# --- Stage 1: Build the Frontend ---
FROM node:18-alpine AS builder-frontend

# 1. Set working dir and copy only package files
WORKDIR /app/frontend
COPY frontend/package*.json ./

# 2. Install deps and copy all frontend source
RUN npm install
COPY frontend/ ./

# 3. Build the production bundle (output goes into frontend/dist)
RUN npm run build



# --- Stage 2: Build & Package the Backend + Static Assets ---
FROM python:3.12-slim AS runtime

# 4. Create and switch to the app user (non-root)
RUN useradd --create-home appuser
USER appuser

# 5. Set workdir for the backend
WORKDIR /home/appuser/app

# 6. Copy & install Python dependencies
#    requirements.txt lives in your repo root
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 7. Copy your backend code
COPY --chown=appuser:appuser backend/ ./backend

# 8. Copy the built frontend into your backend’s static folder
#    Now your /backend/static contains all files from frontend/dist
COPY --from=builder-frontend --chown=appuser:appuser \
     /app/frontend/dist ./backend/static



# --- Stage 3: Runtime Configuration ---
# 9. Expose the port (8000 locally, but overridden by $PORT on Render)
EXPOSE 8000

# 10. Start your app via Uvicorn, pointing at backend/main.py’s `app`
#     Using ${PORT:-8000} lets Render inject its assigned port or fallback to 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]