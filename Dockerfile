FROM node:22-alpine AS frontend-builder
WORKDIR /app

COPY . .
RUN cd "Front End/react-app" && npm ci && npm run build

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
COPY Datasets Datasets

# Copy built frontend
COPY --from=frontend-builder /app/Front\ End/react-app/dist /app/Frontend/dist

# Update Flask app to serve frontend
RUN mkdir -p /app/Frontend

EXPOSE 5000

CMD ["waitress-serve", "--listen=0.0.0.0:5000", "Backend.app:app"]
