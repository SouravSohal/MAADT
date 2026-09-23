#!/bin/bash
# ==============================================================================
# MAADT Google Cloud Run One-Click Automated Deployment Script
# Deploys Unified Next.js 16 WebGL HUD + FastAPI Digital Twin Engine
# ==============================================================================

set -e

# Default settings
DEFAULT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "maadt-509407")
DEFAULT_REGION="us-central1"
DEFAULT_SERVICE="maadt"

PROJECT_ID="${GCP_PROJECT:-$DEFAULT_PROJECT}"
REGION="${GCP_REGION:-$DEFAULT_REGION}"
SERVICE_NAME="${GCP_SERVICE:-$DEFAULT_SERVICE}"
GEMINI_KEY="${GEMINI_API_KEY:-}"

# Parse optional command line flags
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --project) PROJECT_ID="$2"; shift ;;
        --region) REGION="$2"; shift ;;
        --service) SERVICE_NAME="$2"; shift ;;
        --gemini-key) GEMINI_KEY="$2"; shift ;;
        -h|--help)
            echo "Usage: ./scripts/deploy_cloud_run.sh [OPTIONS]"
            echo "Options:"
            echo "  --project <GCP_PROJECT_ID>   Google Cloud Project ID (default: $DEFAULT_PROJECT)"
            echo "  --region <GCP_REGION>         Deployment Region (default: $DEFAULT_REGION)"
            echo "  --service <SERVICE_NAME>      Cloud Run Service Name (default: $DEFAULT_SERVICE)"
            echo "  --gemini-key <API_KEY>        Google Gemini API Key for Cloud AI Copilot"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
    shift
done

echo "======================================================================"
echo "          MAADT CLOUD RUN DEPLOYMENT WIZARD                           "
echo "======================================================================"
echo "Target Project  : $PROJECT_ID"
echo "Target Region   : $REGION"
echo "Service Name    : $SERVICE_NAME"
if [ -n "$GEMINI_KEY" ]; then
    echo "AI Copilot      : Enabled (Gemini Cloud API Key Detected)"
else
    echo "AI Copilot      : Offline (Rules-based aerospace diagnostics)"
fi
echo "======================================================================"

# 1. Verify gcloud authentication
if ! gcloud auth print-access-token >/dev/null 2>&1; then
    echo "Error: gcloud is not authenticated. Please run: gcloud auth login"
    exit 1
fi

# 2. Enable essential Google Cloud APIs
echo ""
echo "[Step 1/3] Enabling Google Cloud Services..."
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    --project="$PROJECT_ID" --quiet

# 3. Prepare Environment Variables
ENV_VARS="MAADT_CONFIG_DIR=/app/configs,MAADT_DB_PATH=/app/data/maadt_data.db"
if [ -n "$GEMINI_KEY" ]; then
    ENV_VARS="$ENV_VARS,GEMINI_API_KEY=$GEMINI_KEY,GEMINI_MODEL=gemini-2.5-flash"
fi

# 4. Build and Deploy using Cloud Run Source Deployment
echo ""
echo "[Step 2/3] Submitting build to Google Cloud Build & deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --platform=managed \
    --port=8080 \
    --memory=2Gi \
    --cpu=2 \
    --timeout=3600 \
    --min-instances=0 \
    --max-instances=1 \
    --concurrency=80 \
    --set-env-vars="$ENV_VARS" \
    --allow-unauthenticated \
    --quiet

# 5. Retrieve deployed HTTPS URL
echo ""
echo "[Step 3/3] Fetching Service URL..."
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --format='value(status.url)')

echo ""
echo "======================================================================"
echo "  🚀 MAADT PLATFORM IS LIVE ON GOOGLE CLOUD RUN!                      "
echo "======================================================================"
echo "  URL: $SERVICE_URL"
echo ""
echo "  Components included in this single-endpoint deployment:"
echo "    - 3D WebGL Digital Twin HUD     : $SERVICE_URL/"
echo "    - 10 Hz Telemetry WebSocket     : wss://${SERVICE_URL#https://}/ws/telemetry"
echo "    - REST Engine Diagnostics APIs  : $SERVICE_URL/api/v1/system/status"
echo "    - Interactive OpenAPI Docs      : $SERVICE_URL/docs"
echo "======================================================================"
