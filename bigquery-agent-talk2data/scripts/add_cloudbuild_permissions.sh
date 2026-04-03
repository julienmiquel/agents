#!/bin/bash
export PATH=$PATH:/opt/homebrew/bin
PROJECT_ID="ml-demo-384110"
PROJECT_NUMBER="1008225662928"
CLOUDBUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

echo "Granting roles to Cloud Build Service Account: ${CLOUDBUILD_SA} in project ${PROJECT_ID}"

echo "Granting Vertex AI Admin..."
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${CLOUDBUILD_SA}" \
    --role="roles/aiplatform.admin"

echo "Granting Storage Admin..."
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${CLOUDBUILD_SA}" \
    --role="roles/storage.admin"

echo "Permissions added."
