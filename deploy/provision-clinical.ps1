$ProjectID = "clinical-ai-501918"
$Location = "us-central1"
$Repo = "clinical"

Write-Host "Starting Google Cloud provision script (PowerShell) for Clinical AI..."

# Set project
gcloud config set project $ProjectID

# Enable APIs
Write-Host "Enabling APIs..."
gcloud services enable `
  run.googleapis.com `
  secretmanager.googleapis.com `
  artifactregistry.googleapis.com `
  cloudbuild.googleapis.com

# Create Artifact Registry
Write-Host "Checking/Creating Artifact Registry repository..."
gcloud artifacts repositories create $Repo `
  --repository-format=docker `
  --location=$Location `
  --description="Clinical Reasoning Engine Docker registry" 2>$null

# Helper to create secret if missing
function Create-Secret-If-Missing ($Name, $Value) {
  gcloud secrets describe $Name 2>$null
  if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating secret $Name..."
    gcloud secrets create $Name --replication-policy="automatic"
    if ($Value) {
      $Value = $Value.Trim()
      Write-Host "Adding value to secret $Name..."
      $Value | gcloud secrets versions add $Name --data-file=-
    } else {
      Write-Host "Adding placeholder to secret $Name..."
      "placeholder" | gcloud secrets versions add $Name --data-file=-
    }
  } else {
    Write-Host "Secret $Name already exists."
  }
}

# Parse keys from .env if present
$GroqKey = ""
$NvidiaKey = ""
$GeminiKey = ""
if (Test-Path .env) {
  $envContent = Get-Content .env
  foreach ($line in $envContent) {
    if ($line -match "^GROQ_API_KEY=(.*)") { $GroqKey = $Matches[1] }
    if ($line -match "^NVIDIA_NIM_API_KEY=(.*)") { $NvidiaKey = $Matches[1] }
    if ($line -match "^GEMINI_API_KEY=(.*)") { $GeminiKey = $Matches[1] }
  }
}

Create-Secret-If-Missing "clinical-groq-key" $GroqKey
Create-Secret-If-Missing "clinical-nvidia-key" $NvidiaKey
Create-Secret-If-Missing "clinical-gemini-key" $GeminiKey
Create-Secret-If-Missing "clinical-google-client-id" "your_google_client_id_here"

# Configure IAM permissions
Write-Host "Configure IAM permissions..."
$ProjectNumber = gcloud projects describe $ProjectID --format="value(projectNumber)"
$ProjectNumber = $ProjectNumber.Trim()

$ComputeSA = "${ProjectNumber}-compute@developer.gserviceaccount.com"
$CloudBuildSA = "${ProjectNumber}@cloudbuild.gserviceaccount.com"

# Grant access
gcloud projects add-iam-policy-binding $ProjectID `
  --member="serviceAccount:$ComputeSA" `
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $ProjectID `
  --member="serviceAccount:$CloudBuildSA" `
  --role="roles/secretmanager.secretAccessor"

Write-Host "Google Cloud environment provisioned for $ProjectID!"
