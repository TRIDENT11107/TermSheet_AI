FROM node:22-alpine AS frontend-builder
WORKDIR /app

COPY . .
RUN cd "Front End/react-app" && npm install && npm run build
RUN mkdir -p /frontend-dist && cp -r "Front End/react-app/dist/." /frontend-dist/

FROM python:3.11-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY Backend Backend
COPY Datasets Datasets
COPY run_app.py .

COPY --from=frontend-builder /frontend-dist /app/Front\ End/react-app/dist

EXPOSE 5000

CMD ["waitress-serve", "--listen=0.0.0.0:5000", "Backend.app:app"]
