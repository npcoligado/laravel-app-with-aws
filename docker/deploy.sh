#!/bin/bash
set -e

if [ -f .env ]; then
    echo "Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
else
    echo ".env file not found. Using existing environment variables."
fi

# Check required variables
: "${AWS_ACCOUNT_ID:?Need to set AWS_ACCOUNT_ID}"
: "${AWS_REGION:?Need to set AWS_REGION}"
: "${STAGE:?Need to set STAGE}"
: "${IMAGE_TAG:=latest}"

REPO_NAME="laravel-$STAGE-repo"
IMAGE_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO_NAME:$IMAGE_TAG"

echo "Building Docker image..."
docker build -t $REPO_NAME .

echo "Tagging Docker image for ECR..."
docker tag $REPO_NAME:latest $IMAGE_URI

echo "Logging in to AWS ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

echo "Pushing Docker image to ECR..."
docker push $IMAGE_URI

echo "Deployment complete! Image URI: $IMAGE_URI"
