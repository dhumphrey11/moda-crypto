#!/bin/bash

# Setup GCP for existing Moda Crypto project
# This script configures an existing GCP project for deployment

set -e

echo "🚀 GCP Setup for Existing Moda Crypto Project"
echo "============================================="

# Use existing project
PROJECT_ID="moda-crypto"
SA_NAME="github-actions"
SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"
KEY_FILE="$HOME/moda-crypto-sa-key.json"

echo "📋 Project ID: $PROJECT_ID"
echo "📧 Service Account: $SA_EMAIL"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if project exists
echo "1️⃣ Checking if project exists..."
if ! gcloud projects describe $PROJECT_ID &> /dev/null; then
    echo "❌ Project '$PROJECT_ID' not found. Please create it first:"
    echo "   https://console.cloud.google.com/projectcreate"
    exit 1
fi

echo "✅ Project '$PROJECT_ID' found"

echo ""
echo "2️⃣ Setting project as default..."
gcloud config set project $PROJECT_ID

echo ""
echo "3️⃣ Checking billing status..."
BILLING_ENABLED=$(gcloud beta billing projects describe $PROJECT_ID --format="value(billingEnabled)" 2>/dev/null || echo "false")

if [ "$BILLING_ENABLED" != "True" ]; then
    echo "⚠️  Billing is not enabled for this project."
    echo "   Please enable billing at: https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID"
    echo ""
    echo "💡 You can continue with the setup after enabling billing."
    read -p "   Press Enter after enabling billing, or Ctrl+C to exit..."
    echo ""
fi

echo "4️⃣ Enabling required APIs..."
echo "   This may take a few minutes..."

# Enable APIs one by one with better error handling
APIS=(
    "run.googleapis.com"
    "cloudbuild.googleapis.com" 
    "containerregistry.googleapis.com"
    "artifactregistry.googleapis.com"
    "iam.googleapis.com"
    "cloudresourcemanager.googleapis.com"
)

for API in "${APIS[@]}"; do
    echo "   Enabling $API..."
    if gcloud services enable $API; then
        echo "   ✅ $API enabled"
    else
        echo "   ❌ Failed to enable $API"
        echo "   Please check billing and try again"
        exit 1
    fi
done

echo ""
echo "5️⃣ Creating service account..."
if gcloud iam service-accounts describe $SA_EMAIL &> /dev/null; then
    echo "   Service account already exists, skipping creation"
else
    gcloud iam service-accounts create $SA_NAME \
        --description="Service account for GitHub Actions" \
        --display-name="GitHub Actions"
    echo "   ✅ Service account created"
fi

echo ""
echo "6️⃣ Granting necessary roles..."
ROLES=(
    "roles/run.admin"
    "roles/storage.admin" 
    "roles/cloudbuild.builds.editor"
    "roles/iam.serviceAccountUser"
    "roles/artifactregistry.admin"
)

for ROLE in "${ROLES[@]}"; do
    echo "   Granting $ROLE..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SA_EMAIL" \
        --role="$ROLE" > /dev/null
done

echo "   ✅ All roles granted"

echo ""
echo "7️⃣ Creating service account key..."
if [ -f "$KEY_FILE" ]; then
    echo "   Key file already exists, backing up..."
    mv "$KEY_FILE" "$KEY_FILE.backup.$(date +%s)"
fi

gcloud iam service-accounts keys create $KEY_FILE \
    --iam-account=$SA_EMAIL

echo "   ✅ Key saved to: $KEY_FILE"

echo ""
echo "8️⃣ Setting up GitHub secrets..."
if ! command -v gh &> /dev/null; then
    echo "   ❌ GitHub CLI not found. Install it to auto-configure secrets:"
    echo "      https://cli.github.com/"
    echo ""
    echo "   Manual setup required - add these secrets to GitHub:"
    echo "   GCP_PROJECT_ID: $PROJECT_ID"
    echo "   GCP_SA_EMAIL: $SA_EMAIL"
    echo "   GCP_SA_KEY: $(cat $KEY_FILE | base64 -w 0 2>/dev/null || cat $KEY_FILE | base64)"
else
    echo "   Setting GitHub secrets..."
    
    # Check if authenticated
    if ! gh auth status &> /dev/null; then
        echo "   Please authenticate with GitHub CLI first:"
        echo "   gh auth login"
        exit 1
    fi
    
    # Set the secrets
    echo "   Setting GCP_PROJECT_ID..."
    echo "$PROJECT_ID" | gh secret set GCP_PROJECT_ID --repo=dhumphrey11/moda-crypto
    
    echo "   Setting GCP_SA_EMAIL..."
    echo "$SA_EMAIL" | gh secret set GCP_SA_EMAIL --repo=dhumphrey11/moda-crypto
    
    echo "   Setting GCP_SA_KEY..."
    cat "$KEY_FILE" | gh secret set GCP_SA_KEY --repo=dhumphrey11/moda-crypto
    
    echo "   ✅ GitHub secrets configured"
fi

echo ""
echo "🎉 GCP setup complete!"
echo "========================"
echo ""
echo "✅ Project: $PROJECT_ID"
echo "✅ Service Account: $SA_EMAIL"
echo "✅ APIs enabled"
echo "✅ GitHub secrets configured"
echo ""
echo "🚀 Next steps:"
echo "   1. Get external API keys: ./api-keys-guide.sh"
echo "   2. Deploy: git push origin main"
echo ""
echo "📋 Manual verification:"
echo "   - GCP Console: https://console.cloud.google.com/run?project=$PROJECT_ID"
echo "   - GitHub Actions: https://github.com/dhumphrey11/moda-crypto/actions"