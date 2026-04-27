#!/bin/bash

# OvernightApp Deployment Script
# This script pulls latest code, rebuilds Docker images, and syncs static files to R2

set -e  # Exit on error

echo "🚀 Starting OvernightApp deployment..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Pull latest code from git
echo -e "${YELLOW}📦 Pulling latest code from git...${NC}"
git pull origin main || {
    echo -e "${RED}❌ Git pull failed. Continuing anyway...${NC}"
}

# 2. Stop existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker compose down

# 3. Build new Docker images
echo -e "${YELLOW}🔨 Building Docker images...${NC}"
docker compose build --no-cache

# 4. Start containers
echo -e "${YELLOW}🚀 Starting containers...${NC}"
docker compose up -d

# Wait for containers to be ready
echo -e "${YELLOW}⏳ Waiting for containers to start...${NC}"
sleep 5

# 5. Run database migrations
echo -e "${YELLOW}🗄️  Running database migrations...${NC}"
docker compose exec -T web python manage.py migrate --noinput

# 6. Collect static files
echo -e "${YELLOW}📦 Collecting static files...${NC}"
docker compose exec -T web python manage.py collectstatic --noinput

# 7. Sync static files to R2 (only changed files)
echo -e "${YELLOW}☁️  Syncing static files to Cloudflare R2...${NC}"

# Check if R2 credentials are set
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ] || [ -z "$AWS_STORAGE_BUCKET_NAME" ] || [ -z "$AWS_S3_ENDPOINT_URL" ]; then
    echo -e "${YELLOW}⚠️  R2 credentials not found in environment. Loading from .env file...${NC}"

    # Source .env file to get R2 credentials
    if [ -f .env ]; then
        export $(cat .env | grep -E '^AWS_' | xargs)
    else
        echo -e "${RED}❌ .env file not found. Skipping R2 sync.${NC}"
        echo -e "${GREEN}✅ Deployment complete (without R2 sync)${NC}"
        exit 0
    fi
fi

# Only proceed with R2 sync if credentials are available
if [ ! -z "$AWS_ACCESS_KEY_ID" ] && [ ! -z "$AWS_STORAGE_BUCKET_NAME" ]; then
    # Install AWS CLI if not present
    if ! command -v aws &> /dev/null; then
        echo -e "${YELLOW}📥 Installing AWS CLI...${NC}"
        pip install awscli-plugin-endpoint
    fi

    # Configure AWS CLI for R2
    export AWS_DEFAULT_REGION=auto

    # Sync static files to R2 (only upload new/changed files)
    # Using --size-only to compare file sizes (faster than checksums)
    # Add --dryrun flag to test without actually uploading
    echo -e "${YELLOW}☁️  Uploading changed static files to R2...${NC}"

    aws s3 sync ./staticfiles/ s3://${AWS_STORAGE_BUCKET_NAME}/static/ \
        --endpoint-url ${AWS_S3_ENDPOINT_URL} \
        --size-only \
        --delete \
        --exclude "*.pyc" \
        --exclude "__pycache__/*" \
        --exclude ".DS_Store" \
        --acl public-read || {
        echo -e "${RED}❌ R2 sync failed. Static files may not be updated.${NC}"
        echo -e "${YELLOW}⚠️  Continuing deployment anyway...${NC}"
    }

    echo -e "${GREEN}✅ Static files synced to R2${NC}"
else
    echo -e "${YELLOW}⚠️  R2 credentials not complete. Skipping R2 sync.${NC}"
fi

# 8. Create default event options for any new users
echo -e "${YELLOW}🎯 Creating default event options for new users...${NC}"
docker compose exec -T web python manage.py create_default_options || {
    echo -e "${YELLOW}⚠️  Failed to create default options (may already exist)${NC}"
}

# 9. Show running containers
echo -e "${YELLOW}📊 Container status:${NC}"
docker compose ps

# 10. Show logs (last 20 lines)
echo -e "${YELLOW}📝 Recent logs:${NC}"
docker compose logs --tail=20 web

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo -e "${GREEN}🌐 Application is running at: http://localhost:8000${NC}"
echo ""
echo "Useful commands:"
echo "  - View logs: docker compose logs -f web"
echo "  - Restart: docker compose restart web"
echo "  - Stop: docker compose down"
echo "  - Shell access: docker compose exec web bash"
