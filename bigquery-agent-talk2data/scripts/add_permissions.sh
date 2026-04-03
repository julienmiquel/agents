#!/bin/bash

# Configuration
export PATH=$PATH:/opt/homebrew/bin
PROJECT_ID="ml-demo-384110"
PROJECT_NUMBER="1008225662928"

# Candidate Service Accounts
VERTEX_AI_SA_RE="service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
VERTEX_AI_SA_AP="service-${PROJECT_NUMBER}@gcp-sa-aiplatform.iam.gserviceaccount.com"
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "Attempting to grant BigQuery Data Viewer and Job User roles to candidate service accounts in project ${PROJECT_ID}..."

# 1. Grant to Vertex AI Reasoning Engine Service Agent
echo "Granting BigQuery roles to Vertex AI Reasoning Engine Service Agent: ${VERTEX_AI_SA_RE}"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${VERTEX_AI_SA_RE}" \
    --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${VERTEX_AI_SA_RE}" \
    --role="roles/bigquery.jobUser"

# 1b. Grant to Standard Vertex AI Service Agent
echo "Granting BigQuery roles to Standard Vertex AI Service Agent: ${VERTEX_AI_SA_AP}"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${VERTEX_AI_SA_AP}" \
    --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${VERTEX_AI_SA_AP}" \
    --role="roles/bigquery.jobUser"

# 2. Grant to Compute Engine Default Service Account
echo "Granting BigQuery roles to Compute Engine Default Service Account: ${COMPUTE_SA}"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${COMPUTE_SA}" \
    --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${COMPUTE_SA}" \
    --role="roles/bigquery.jobUser"

# 3. Grant Gemini Data Analytics Roles to Candidate Service accounts
echo "Granting Gemini Data Analytics roles to candidate service accounts..."

for ROLE in "roles/geminidataanalytics.dataAgentOwner" "roles/geminidataanalytics.dataAgentUser" "roles/geminidataanalytics.dataAgentStatelessUser" "roles/geminidataanalytics.queryDataUser"; do
    echo "Applying ${ROLE}..."
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="serviceAccount:${VERTEX_AI_SA_RE}" \
        --role="${ROLE}"

    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="serviceAccount:${VERTEX_AI_SA_AP}" \
        --role="${ROLE}"

    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="serviceAccount:${COMPUTE_SA}" \
        --role="${ROLE}"
done

# 4. Grant Discovery Engine User role to Candidate Service accounts
echo "Granting Discovery Engine User role to candidate service accounts..."

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${VERTEX_AI_SA_RE}" \
    --role="roles/discoveryengine.user"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${VERTEX_AI_SA_AP}" \
    --role="roles/discoveryengine.user"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${COMPUTE_SA}" \
    --role="roles/discoveryengine.user"

echo "Permissions script execution complete."
