# MAADT Cloud Deployment Guide
### *Deploying to Google Cloud Run (Unified Architecture: FastAPI + Next.js HUD)*

This guide provides end-to-end instructions for deploying the **MAADT (Mission-Aware Adaptive Digital Twin)** platform to **Google Cloud Run**.

---

## 1. Cloud Architecture Overview

MAADT uses a **Unified Cloud Container** architecture engineered specifically for Google Cloud Run:

```
                            INTERNET (HTTPS / WSS)
                                      │
                                      ▼  (Port 443 / Automatic TLS)
        ┌───────────────────────────────────────────────────────────┐
        │                 GOOGLE CLOUD RUN SERVICE                  │
        │                                                           │
        │  ┌─────────────────────────────────────────────────────┐  │
        │  │       Nginx Ingress Reverse Proxy (Port 8080)       │  │
        │  └──────────┬───────────────────────────────┬──────────┘  │
        │             │                               │             │
        │             ▼                               ▼             │
        │     /api/*, /ws/*, /docs               /* (HTML/JS)       │
        │  ┌─────────────────────────┐     ┌─────────────────────┐  │
        │  │ FastAPI Intelligence    │     │ Next.js 16 WebGL    │  │
        │  │ Core (Port 8000)        │     │ Standalone HUD      │  │
        │  │ - 10 Hz Telemetry WS    │     │ (Port 3000)         │  │
        │  │ - EKF Twin & Physics    │     │ - Three.js 3D Twin  │  │
        │  │ - SQLite Persistence    │     │ - Real-Time Charts  │  │
        │  │ - Gemini AI Cloud Bridge│     │ - Mission Scenarios │  │
        │  └─────────────────────────┘     └─────────────────────┘  │
        └───────────────────────────────────────────────────────────┘
```

### Key Advantages:
1. **Single Public URL**: Frontend, REST APIs, and WebSockets live on the exact same origin (`https://maadt-xxxx-uc.a.run.app`). Zero CORS errors, zero mixed content warnings, and no custom domain configuration required.
2. **Native 10 Hz WebSocket Streaming**: Built with 3,600-second session timeouts to sustain real-time bidirectional telemetry streaming without connection drops.
3. **Micro-Footprint**: The Next.js frontend uses output standalone file tracing (~73 MB) combined with a Python 3.12-slim backend for rapid cold starts.
4. **Cloud AI Copilot**: Fully integrated with **Google Gemini 2.5 Flash** via standard environment variable `GEMINI_API_KEY`. If no key is set, the system seamlessly uses the offline rules-based DRDO aerospace diagnostics.

---

## 2. Quick Deploy (Automated 1-Command)

The repository includes an automated deployment wizard that enables the necessary Google Cloud APIs, submits the build to Cloud Build, and deploys directly to Cloud Run.

From the project root:

```bash
# Basic deployment (offline rules-based diagnostics)
./scripts/deploy_cloud_run.sh

# Or with Google Cloud Gemini AI Copilot enabled:
./scripts/deploy_cloud_run.sh --gemini-key "YOUR_GEMINI_API_KEY"
```

The script automatically detects your active GCP Project (e.g. `eleven-508514`) and region (`us-central1`), builds the container, and prints your live HTTPS URL.

---

## 3. Step-by-Step Manual Deployment (`gcloud` CLI)

If you prefer to run the commands manually:

### Step 1: Set Project and Region
```bash
export GCP_PROJECT=$(gcloud config get-value project)
export GCP_REGION="us-central1"
export SERVICE_NAME="maadt"
```

### Step 2: Enable Required APIs
```bash
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    --project="$GCP_PROJECT"
```

### Step 3: Deploy Directly from Source
```bash
gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --project="$GCP_PROJECT" \
    --region="$GCP_REGION" \
    --platform=managed \
    --port=8080 \
    --memory=2Gi \
    --cpu=2 \
    --timeout=3600 \
    --min-instances=0 \
    --max-instances=1 \
    --concurrency=80 \
    --set-env-vars="PORT=8080,MAADT_CONFIG_DIR=/app/configs,MAADT_DB_PATH=/app/data/maadt_data.db,GEMINI_MODEL=gemini-2.5-flash" \
    --allow-unauthenticated
```

> [!NOTE]
> **Why `--max-instances=1`?**
> MAADT maintains a real-time Extended Kalman Filter (EKF) and physics simulation loop in memory. Setting `max-instances: 1` ensures state continuity for the active digital twin while keeping your Google Cloud costs minimal.

> [!TIP]
> **Why `--timeout=3600`?**
> By default, Cloud Run times out HTTP requests after 300 seconds. Setting `--timeout=3600` ensures your continuous 10 Hz WebSocket telemetry stream stays open for long-duration flight simulations.

---

## 4. Google Cloud Gemini AI Copilot Setup

MAADT comes with native support for **Google Gemini 2.5 Flash** for deep propulsion diagnostics and interactive mission control assistance.

### Option A: Via `gcloud` Environment Variable
```bash
gcloud run services update "$SERVICE_NAME" \
    --region="$GCP_REGION" \
    --update-env-vars="GEMINI_API_KEY=YOUR_GEMINI_KEY,GEMINI_MODEL=gemini-2.5-flash"
```

### Option B: Via Google Secret Manager (Enterprise Production)
```bash
# 1. Create secret in Secret Manager
echo -n "YOUR_GEMINI_KEY" | gcloud secrets create gemini-api-key --data-file=-

# 2. Grant Secret Accessor to Cloud Run Service Account
PROJECT_NUMBER=$(gcloud projects describe "$GCP_PROJECT" --format='value(projectNumber)')
gcloud secrets add-iam-policy-binding gemini-api-key \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# 3. Mount secret to Cloud Run
gcloud run services update "$SERVICE_NAME" \
    --region="$GCP_REGION" \
    --update-secrets="GEMINI_API_KEY=gemini-api-key:latest"
```

---

## 5. Persistent Storage with Cloud Storage (GCS FUSE)

For permanent storage of SQLite telemetry databases across container restarts:

```bash
# 1. Create a Cloud Storage Bucket
gcloud storage buckets create gs://${GCP_PROJECT}-maadt-data --location="$GCP_REGION"

# 2. Mount the bucket as a volume on Cloud Run
gcloud run services update "$SERVICE_NAME" \
    --region="$GCP_REGION" \
    --execution-environment=gen2 \
    --add-volume=name=maadt-storage,type=cloud-storage,bucket=${GCP_PROJECT}-maadt-data \
    --add-volume-mount=volume=maadt-storage,mount-path=/app/data
```

---

## 6. GitHub Actions CI/CD Workflow

To automate deployments on every `git push main`:

Create `.github/workflows/deploy-cloud-run.yml`:

```yaml
name: Deploy MAADT to Google Cloud Run

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy maadt \
            --source . \
            --region us-central1 \
            --port 8080 \
            --memory 2Gi \
            --cpu 2 \
            --timeout 3600 \
            --max-instances 1 \
            --allow-unauthenticated
```

---

## 7. Local Cloud Run Verification

To test the unified Cloud Run container locally on your workstation before pushing to the cloud:

```bash
# Build the unified image
docker build -t maadt-cloud:latest .

# Run locally simulating Cloud Run's $PORT environment variable
docker run -p 8080:8080 -e PORT=8080 -e GEMINI_API_KEY="YOUR_KEY" maadt-cloud:latest
```

Open:
* Frontend HUD: [http://localhost:8080/](http://localhost:8080/)
* API Status: [http://localhost:8080/api/v1/system/status](http://localhost:8080/api/v1/system/status)
* Interactive Docs: [http://localhost:8080/docs](http://localhost:8080/docs)
