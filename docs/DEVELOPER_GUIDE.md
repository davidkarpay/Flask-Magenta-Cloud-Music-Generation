# Flask Magenta Cloud Music Generation

## Table of Contents

1. [Purpose](#purpose)
2. [Architecture & Core Features](#architecture--core-features)
3. [Module Overview](#module-overview)
4. [Setup & Installation](#setup--installation)
5. [Running Locally](#running-locally)
6. [Deployment via GitHub Actions](#deployment-via-github-actions)
7. [API Endpoints](#api-endpoints)
8. [Test-Driven Development (TDD) Workflow](#test-driven-development-tdd-workflow)
9. [Sample Smoke Tests](#sample-smoke-tests)
10. [Managing Magenta Checkpoints](#managing-magenta-checkpoints)
11. [Logging Configuration](#logging-configuration)
12. [Roadmap & Extendability](#roadmap--extendability)

---

## Purpose

This service exposes a REST API for generating short music segments using Google’s [Magenta MusicVAE](https://github.com/magenta/magenta) models. It is meant to run as a lightweight Flask app, suitable for containerized deployment in cloud platforms.

## Architecture & Core Features

- **Flask API** (`app.py`) serving endpoints under `/v1`.
- **Model loader** (`model_loader.py`) to fetch or cache pretrained checkpoints.
- **Generator** (`generator.py`) wrapping MusicVAE inference.
- **Cache** (`cache.py`) for in-memory or file-based output caching.
- **Schema** (`schema.json`) for validating incoming JSON payloads.

Key features:
- Dynamic downloading of Magenta checkpoints on first use.
- JSON schema validation of request payloads.
- Modular code to ease testing of each component.
- Built-in logging at each processing stage.

## Module Overview

```
magenta-api/
├── app.py           # Flask app + routing + request validation
├── model_loader.py  # ensure_checkpoint(), downloads ckpts if missing
├── generator.py     # load model, run inference, return note sequences
├── cache.py         # simple LRU or TTL cache for results
├── schema.json      # JSON Schema for /v1/generate payload
├── requirements.txt # Python deps
└── runtime.yaml     # Cloud runtime config (start command, env)
```

### Internal Interactions
1. `app.py` receives POST `/v1/generate` → validates JSON against `schema.json`.
2. Calls `model_loader.ensure_checkpoint()` → fetches `*.ckpt` into `./models/`.
3. Instantiates or reuses MusicVAE model via `generator.py` → runs `model.sample()`.
4. Optionally stores result in `cache.py` and responds with JSON.

## Setup & Installation

```bash
# 1. Clone repo
git clone <repo-url> flask-magenta
cd flask-magenta

# 2. (Optional) Create & activate virtualenv
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r magenta-api/requirements.txt
``` 

## Running Locally

```bash
# From project root:
export MODEL_DIR="$(pwd)/magenta-api/models"
cd magenta-api
python app.py
```  
By default, the app listens on `http://127.0.0.1:5000/`.

## Deployment via GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: CI & Deploy

on:
  push:
    branches: [main]

jobs:
  build-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.10
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('magenta-api/requirements.txt') }}
      - name: Install dependencies
        run: pip install -r magenta-api/requirements.txt
      - name: Run lint & tests
        run: |
          pytest --maxfail=1 --disable-warnings -q

  deploy:
    needs: build-test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Heroku
        uses: akhileshns/heroku-deploy@v3
        with:
          heroku_api_key: ${{ secrets.HEROKU_API_KEY }}
          heroku_app_name: <your-app-name>
          buildpack: heroku/python
```

Adjust “Deploy to …” to your target cloud provider or container registry.

## API Endpoints

### POST /v1/generate

- **URL**: `/v1/generate`
- **Content-Type**: `application/json`
- **Payload**: see [`schema.json`](magenta-api/schema.json)
- **Response**: JSON object with generated sequence data.

Example:
```json
{
  "model": "cat-mel_2bar_big",
  "seed_sequence": [0,1,2,3]
}
```

## Test-Driven Development (TDD) Workflow

1. **Write failing test** in `tests/test_<module>.py` using `pytest`.
2. **Run**:
   ```bash
   pytest -q
   ```
3. **Implement code** until test passes.
4. **Refactor & log** updates.

### Sample test file
```python
# tests/test_app.py
import json
from magenta_api.app import app

def test_generate_endpoint(client):
    payload = {"model": "cat-mel_2bar_big", "seed_sequence": [0,1,2,3]}
    res = client.post('/v1/generate', json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert 'notes' in data
```

## Sample Smoke Tests

**cURL**:
```bash
curl -X POST http://127.0.0.1:5000/v1/generate \
     -H "Content-Type: application/json" \
     -d '{"model":"cat-mel_2bar_big","seed_sequence":[0,1,2,3]}' | jq .
```

**Python**:
```python
import requests

resp = requests.post(
    'http://127.0.0.1:5000/v1/generate',
    json={"model":"cat-mel_2bar_big","seed_sequence":[0,1,2,3]},
    timeout=30
)
resp.raise_for_status()
print(resp.json())
```

## Managing Magenta Checkpoints

In `model_loader.py`:

```python
# ...existing code...
CHECKPOINT_URL = "https://storage.googleapis.com/magentadata/models/music_vae/cat-mel_2bar_big.ckpt"
# ...existing code...
def ensure_checkpoint():
    # Downloads if missing, saves to MODEL_DIR
    # ...existing code...
```

### Dockerfile snippet
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY magenta-api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install gdown && \
    mkdir -p magenta-api/models && \
    gdown https://drive.google.com/uc?id=<file-id> -O magenta-api/models/cat-mel_2bar_big.ckpt
COPY magenta-api ./magenta-api
ENV MODEL_DIR=/app/magenta-api/models
CMD ["python", "magenta-api/app.py"]
```

## Logging Configuration

All modules use Python’s built-in `logging`:

```python
# In app.py, at top:
import logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
# ...existing code...

# Example in generator.py:
logger.info("Loading MusicVAE model %s", model_name)
# ...existing code...
```

To increase verbosity, set `level=logging.DEBUG` via env var:
```bash
export LOG_LEVEL=DEBUG
```  
and modify `basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))`.

## Roadmap & Extendability

### Development Roadmap (TDD Milestones)
1. **Core API & Model Loading**
   - Write pytest for `model_loader.ensure_checkpoint()` (mock HTTP + file exists)
   - Write pytest for `generator.py` (sample call → expected output shape)
   - Implement `cache.py` TTL/LRU cache; tests for hits/misses

2. **Request Validation & Error Handling**
   - Tests for invalid payloads against `schema.json` → expect 400 responses
   - Implement and log schema validation failures in `app.py`
   - Ensure generator errors (bad model, missing checkpoint) return 500 with safe message

3. **Logging & Configuration**
   - Centralize `LOG_LEVEL` support via env var in bootstrap code
   - Add tests capturing `logger.debug()` and `logger.info()` calls
   - Document adding request IDs and timers for traceability

4. **End-to-End & CI Integration**
   - Expand `tests/test_app.py` for full integration via Flask test client
   - Add CI steps: `pytest --cov`, fail if coverage < threshold
   - Enforce linting (black/flake8) in GitHub Actions

5. **Docker & Deployment Validation**
   - Write integration test: `docker build` + `docker run` + smoke curl
   - Extend `.github/workflows/deploy.yml` with AWS/GCP/Azure templates
   - Test Heroku/Cloud Run staging deployments

6. **Checkpoint Management at Scale**
   - Abstract checkpoint source behind `CheckpointStore` interface
   - Tests for streaming download from GCS/S3 buckets
   - Optional in-memory model caching for small assets

7. **Feature Extensions**
   - Add support for extra Magenta models (drums, melody_rnn) with tests
   - Implement Redis-backed cache; integrate `redis-mock` in tests
   - Layer in authentication/rate-limiting (Flask-Limiter)

### Extendability
- Support additional Magenta models (e.g., drums, melody_rnn)
- Pluggable cache backends (Redis, Memcached)
- Authentication, rate limiting, quotas
- Streaming inference for longer sequences
- Websocket endpoint for live generation

---

*This document is the single source of truth for feature planning, TDD, and deployment.*
