# OvernightApp Deployment Checklist

## ✅ Pre-Deployment Checklist

### 1. Database Setup
- [ ] Database connection tested (`python test_db.py`)
- [ ] Migrations applied (`python manage.py migrate`)
- [ ] Superuser created (`python manage.py createsuperuser`)
- [ ] Default event options created for test user

### 2. Environment Configuration
- [ ] `.env` file configured with correct settings
- [ ] `DJANGO_SETTINGS_MODULE` set to `config.settings.production`
- [ ] `DEBUG=False` in production
- [ ] `SECRET_KEY` is unique and secure (not the default!)
- [ ] `ALLOWED_HOSTS` includes your domain/IP
- [ ] PostgreSQL credentials correct
- [ ] R2 credentials configured

### 3. Code Quality
- [ ] All tests passing (`make test`)
- [ ] Code formatted (`make format`)
- [ ] No linting errors (`make lint`)
- [ ] Security scan clean (`make security`)
- [ ] Type checking passed (`make type-check`)

### 4. Static Files
- [ ] R2 bucket created
- [ ] R2 credentials in `.env`
- [ ] Static files collected (`python manage.py collectstatic`)
- [ ] R2 sync tested

### 5. Docker
- [ ] Docker images built (`docker compose build`)
- [ ] Containers start successfully (`docker compose up`)
- [ ] Database accessible from container
- [ ] Environment variables loaded correctly

## 🚀 Initial Deployment Steps

### On Your Development Machine

1. **Commit and push code**
   ```bash
   git add .
   git commit -m "Initial deployment"
   git push origin main
   ```

2. **Test locally first**
   ```bash
   make check-all
   ./dev.sh
   ```

### On Production Server

1. **Clone repository**
   ```bash
   git clone <your-repo-url> OvernightApp
   cd OvernightApp
   ```

2. **Copy and configure .env**
   ```bash
   cp .env.example .env
   nano .env  # Edit with production settings
   ```

   Update these values:
   ```env
   DJANGO_SETTINGS_MODULE=config.settings.production
   DEBUG=False
   ALLOWED_HOSTS=your-server-ip,your-domain.com
   SECRET_KEY=<generate-a-new-one>

   # Keep same database settings
   DATABASE_NAME=postgres  # or overnight_app if you created new DB
   DATABASE_USER=postgres
   DATABASE_PASSWORD=N6itXbLxfePIDes8r44E1SXB
   DATABASE_HOST=hercules
   DATABASE_PORT=5432

   # Add R2 credentials
   AWS_ACCESS_KEY_ID=your_actual_key
   AWS_SECRET_ACCESS_KEY=your_actual_secret
   AWS_STORAGE_BUCKET_NAME=your_bucket_name
   AWS_S3_ENDPOINT_URL=https://your-account-id.r2.cloudflarestorage.com
   ```

3. **Make scripts executable**
   ```bash
   chmod +x build.sh dev.sh
   ```

4. **Run initial build**
   ```bash
   ./build.sh
   ```

   This will:
   - Build Docker images
   - Run migrations
   - Collect static files
   - Sync to R2
   - Create default options
   - Start containers

5. **Create superuser**
   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

6. **Test the application**
   - Visit `http://your-server-ip:8000`
   - Test login
   - Create a test account
   - Verify default event options appear
   - Log a test event

## 🔄 Update Deployment Process

When you have code updates:

```bash
# On production server
cd OvernightApp
./build.sh
```

The `build.sh` script handles:
- ✅ Git pull latest code
- ✅ Rebuild Docker images
- ✅ Run new migrations
- ✅ Collect static files
- ✅ **Sync only changed files to R2** (smart sync!)
- ✅ Restart services

## 🔐 Security Checklist

### Before Going Live

- [ ] Change `SECRET_KEY` to a unique value
- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS` properly
- [ ] Enable HTTPS (SSL/TLS)
- [ ] Set up firewall rules
- [ ] Configure CSRF settings
- [ ] Enable secure cookies
- [ ] Set up logging
- [ ] Configure backup strategy
- [ ] Review all environment variables
- [ ] Run security scan (`make security`)

### Generate Secure SECRET_KEY

```python
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

## 📊 Monitoring Checklist

- [ ] Application logs accessible (`docker compose logs -f web`)
- [ ] Database connection monitored
- [ ] R2 storage usage tracked
- [ ] Error alerts configured
- [ ] Backup schedule set
- [ ] Performance monitoring active

## 🆘 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose logs web

# Restart containers
docker compose restart

# Rebuild from scratch
docker compose down
docker compose up --build
```

### Database Connection Issues

```bash
# Test connection
docker compose exec web python test_db.py

# Check network
ping hercules
telnet hercules 5432
```

### Static Files Not Loading

```bash
# Recollect and sync
docker compose exec web python manage.py collectstatic --noinput
# Then run build.sh to sync to R2
```

### Migration Issues

```bash
# Check migration status
docker compose exec web python manage.py showmigrations

# Apply migrations
docker compose exec web python manage.py migrate

# Fake migrations if needed (advanced)
docker compose exec web python manage.py migrate --fake
```

## 🔄 Rollback Plan

If deployment fails:

1. **Check logs**
   ```bash
   docker compose logs --tail=100 web
   ```

2. **Revert to previous version**
   ```bash
   git log  # Find previous commit
   git checkout <previous-commit-hash>
   ./build.sh
   ```

3. **Database rollback** (if needed)
   ```bash
   # Revert migration
   docker compose exec web python manage.py migrate <app_name> <migration_name>
   ```

## 📝 Post-Deployment

- [ ] Test all major features
- [ ] Create test accounts
- [ ] Log sample events
- [ ] Add day notes
- [ ] Check dashboard
- [ ] Verify email (if configured)
- [ ] Test on mobile
- [ ] Review logs for errors
- [ ] Document any issues
- [ ] Create backup

## 🎯 Production Recommendations

### Create Dedicated Database

```sql
-- On hercules PostgreSQL server
CREATE DATABASE overnight_app;
GRANT ALL PRIVILEGES ON DATABASE overnight_app TO postgres;
```

Then update `.env`:
```env
DATABASE_NAME=overnight_app
```

### Set Up SSL/HTTPS

Use a reverse proxy like Nginx with Let's Encrypt:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Configure Backups

```bash
# Database backup script
pg_dump -h hercules -U postgres overnight_app > backup_$(date +%Y%m%d).sql

# Automated daily backups
0 2 * * * /path/to/backup.sh
```

## ✅ Final Verification

Before going live:

```bash
# Run all checks
make check-all

# Test deployment
./build.sh

# Verify services
docker compose ps

# Check logs
docker compose logs --tail=50 web

# Test application
curl http://localhost:8000
```

---

**You're ready to deploy! 🚀**

Remember: Test in development first, then deploy to production with confidence.
