FROM node:22-alpine AS frontend-builder
WORKDIR /app

# Copy only necessary files for frontend build
COPY "Front End/react-app/package*.json" "Front End/react-app/"
COPY "Front End/react-app/vite.config.ts" "Front End/react-app/"
COPY "Front End/react-app/tsconfig.json" "Front End/react-app/"
COPY "Front End/react-app/src" "Front End/react-app/src"
COPY "Front End/react-app/public" "Front End/react-app/public"
COPY "Front End/react-app/index.html" "Front End/react-app/"

WORKDIR /app/Front\ End/react-app
RUN npm ci && npm run build

FROM python:3.11-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies for OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY Backend Backend

# Copy built frontend
COPY --from=frontend-builder /app/Front\ End/react-app/dist /app/Frontend/dist

EXPOSE 5000

CMD ["waitress-serve", "--listen=0.0.0.0:5000", "Backend.app:app"]
