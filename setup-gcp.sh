#!/bin/bash

# Quick GCP Setup for Moda Crypto
# This script helps you create a GCP project and service account

set -e

echo "🚀 Quick GCP Setup for Moda Crypto"
echo "=================================="

# Generate a unique project ID
TIMESTAMP=$(date +%s)
PROJECT_ID="moda-crypto-$TIMESTAMP"
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

echo "1️⃣ Creating GCP project..."
gcloud projects create $PROJECT_ID --name="Moda Crypto"

echo ""
echo "2️⃣ Setting project as default..."
gcloud config set project $PROJECT_ID

echo ""
echo "3️⃣ Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com

echo ""
echo "4️⃣ Creating service account..."
gcloud iam service-accounts create $SA_NAME \
    --description="Service account for GitHub Actions" \
    --display-name="GitHub Actions"

echo ""
echo "5️⃣ Granting necessary roles..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/cloudbuild.builds.builder"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/iam.serviceAccountUser"

echo ""
echo "6️⃣ Creating and downloading service account key..."
gcloud iam service-accounts keys create $KEY_FILE \
    --iam-account=$SA_EMAIL

echo ""
echo "7️⃣ Setting GitHub secrets..."
echo $PROJECT_ID | gh secret set GCP_PROJECT_ID --repo=dhumphrey11/moda-crypto
gh secret set GCP_SA_KEY --repo=dhumphrey11/moda-crypto < $KEY_FILE

echo ""
echo "✅ GCP setup complete!"
echo ""
echo "📋 Summary:"
echo "   Project ID: $PROJECT_ID"
echo "   Service Account: $SA_EMAIL"
echo "   Key File: $KEY_FILE"
echo ""
echo "🔐 GitHub secrets set:"
echo "   ✅ GCP_PROJECT_ID"
echo "   ✅ GCP_SA_KEY"
echo ""
echo "🚀 You can now deploy by pushing to main branch!"
echo "   git push origin main"
echo ""
echo "🗑️  Cleanup: You can delete the key file after setup:"
echo "   rm $KEY_FILE"