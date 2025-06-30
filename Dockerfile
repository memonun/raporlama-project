# --- Stage 1: Build Frontend on Alpine ---
FROM node:18-alpine AS builder-frontend
WORKDIR /app/frontend

# Install Node deps & build
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build


# --- Stage 2: Build Backend & Install OS deps on Debian Slim ---
FROM python:3.12-slim AS builder-backend
WORKDIR /app

# Install system-level deps for psycopg2, Pillow, cryptography, etc.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
      python3-dev \
      libpq-dev \
      libssl-dev \
      libffi-dev \
      libjpeg-dev \
      zlib1g-dev \
      libfreetype6-dev \
      libtiff5-dev \
      curl \
      libnss3 \
      libatk1.0-0 \
      libx11-6 \
 && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend


# --- Stage 3: Final Runtime Image ---
FROM python:3.12-slim
# Create non-root user
RUN useradd --create-home appuser
USER appuser
WORKDIR /home/appuser/app

# Copy installed Python packages and scripts
COPY --from=builder-backend /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder-backend /usr/local/bin /usr/local/bin

# Copy backend code
COPY --from=builder-backend /app/backend ./backend

# Copy built frontend into backend static folder
COPY --from=builder-frontend /app/frontend/dist ./backend/static

# Expose and run
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]