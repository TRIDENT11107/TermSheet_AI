# TermSheet AI Deployment

## 1. Train + Test + Build + Run (single command)

```bash
python deploy_today.py
```

This command:

1. Trains/tests the model (`Backend/model/train_model.py`)
2. Builds the React app (`Front End/react-app`)
3. Starts production server on `http://localhost:5000`

## 2. Quick Production Run (skip training/build)

```bash
python deploy_today.py --skip-train --skip-build
```

## 3. Docker Deployment

```bash
docker compose up --build
```

App will be available at:

- `http://localhost:5000` (frontend + backend)
- API routes:
  - `POST /predict`
  - `GET /health`
  - `GET /model/metrics`
  - `GET /supported-types`
