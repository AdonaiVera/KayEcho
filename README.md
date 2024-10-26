# KayEcho


## How to deploy to Google Cloud Platform as a Cloud Run 
# Remember to configure your environment
gcloud auth configure-docker

# Build the Docker image
docker build --platform linux/amd64 -t gcr.io/{your_organization}/kay_echo:v1 .

# Build it with the gcloud option
gcloud builds submit --tag gcr.io/{your_organization}/kay_echo:v1

# Run the Docker image
docker run -p 8080:8080 kay_echo:v1

# Create the cloud run service using the latest images
gcloud run deploy kay_echo \
  --image gcr.io/{your_organization}/kay_echo:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated