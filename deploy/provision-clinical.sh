#!/usr/bin/env bash
set -e

PROJECT_ID="clinical-ai-501918"
LOCATION="us-central1"
REPO="clinical"

echo "🤖 Starting Google Cloud provision script for Clinical AI..."

# Set project
gcloud config set project "$PROJECT_ID"

# Enable APIs
echo "📡 Enabling APIs..."
gcloud services enable \
  run.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com

# Create Artifact Registry
echo "🐳 Creating Artifact Registry repository..."
gcloud artifacts repositories create "$REPO" \
  --repository-format=docker \
  --location="$LOCATION" \
  --description="Clinical Reasoning Engine Docker registry" 2>/dev/null || echo "Registry already exists."

# Create Secrets
echo "🔒 Checking secrets in Secret Manager..."

create_secret_if_missing() {
  local name=$1
  local value=$2
  if ! gcloud secrets describe "$name" &>/dev/null; then
    echo "Creating secret $name..."
    gcloud secrets create "$name" --replication-policy="automatic"
    if [ -n "$value" ]; then
      echo -n "$value" | gcloud secrets versions add "$name" --data-file=-
    else
      echo "placeholder" | gcloud secrets versions add "$name" --data-file=-
    fi
  else
    echo "Secret $name already exists."
  fi
}

# Fetch local keys to seed secret manager if possible
GROQ_API_KEY_VAL="${GROQ_API_KEY:-}"
NVIDIA_API_KEY_VAL="${NVIDIA_NIM_API_KEY:-}"
GEMINI_API_KEY_VAL="${GEMINI_API_KEY:-}"

# Parse from .env if variables are empty
if [ -f .env ]; then
  [ -z "$GROQ_API_KEY_VAL" ] && GROQ_API_KEY_VAL=$(grep "^GROQ_API_KEY=" .env | cut -d'=' -f2- || true)
  [ -z "$NVIDIA_API_KEY_VAL" ] && NVIDIA_API_KEY_VAL=$(grep "^NVIDIA_NIM_API_KEY=" .env | cut -d'=' -f2- || true)
  [ -z "$GEMINI_API_KEY_VAL" ] && GEMINI_API_KEY_VAL=$(grep "^GEMINI_API_KEY=" .env | cut -d'=' -f2- || true)
fi

create_secret_if_missing "clinical-groq-key" "$GROQ_API_KEY_VAL"
create_secret_if_missing "clinical-nvidia-key" "$NVIDIA_API_KEY_VAL"
create_secret_if_missing "clinical-gemini-key" "$GEMINI_API_KEY_VAL"
create_secret_if_missing "clinical-google-client-id" ""

# Grant Secret Manager Secret Accessor to service accounts
echo "👤 Configuring IAM permissions..."
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")

# Compute engine default service account (used by Cloud Run)
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
# Cloud Build service account
CLOUDBUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

# Grant access
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$COMPUTE_SA" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$CLOUDBUILD_SA" \
  --role="roles/secretmanager.secretAccessor"

echo "🎉 Google Cloud environment provisioned for $PROJECT_ID!"
