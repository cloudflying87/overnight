# OvernightApp Setup Guide

## ✅ What's Already Done

1. ✅ Database connection configured (hercules:5432)
2. ✅ All migrations applied
3. ✅ Database tables created successfully
4. ✅ Build scripts created

## 🚀 Quick Start

### 1. Create Your Admin Account

```bash
source venv/bin/activate
python manage.py createsuperuser
```

Follow the prompts to create your admin user.

### 2. Start the Development Server

```bash
# Option A: Using the dev script
./dev.sh

# Option B: Manually
source venv/bin/activate
python manage.py runserver
```

Visit: **http://localhost:8000**

### 3. Sign Up for a Regular Account

- Go to http://localhost:8000
- Click "Sign up"
- Create your caregiver account
- **Default event options will be automatically created for you!**

## 📊 Your Default Event Options

When you sign up, these 10 event options are automatically created:

1. Underwear change
2. Underwear/Clothes wet
3. Bed clothes wet
4. Sheets rearranged
5. Sheets changed
6. Need to pee
7. Active Sleeping
8. Settled Sleeping
9. Moving around the mattresses/room
10. PJ's Top and/or Bottom off

You can edit, add, or delete these in the "Event Options" menu.

## 🔧 Deployment Scripts

### Local Development

```bash
./dev.sh
```

This script:
- Activates virtual environment
- Runs migrations
- Creates default event options
- Collects static files
- Starts development server

### Production Deployment (On Your Server)

```bash
./build.sh
```

This script:
- Pulls latest code from git
- Stops existing containers
- Builds new Docker images
- Starts containers
- Runs migrations
- Collects static files
- **Syncs only changed files to R2** (smart sync!)
- Creates default options for new users
- Shows logs and status

**Important**: The build script only uploads NEW or CHANGED static files to R2, not everything every time. This saves bandwidth and time!

## 🗄️ Database Info

- **Host**: hercules (172.16.29.5)
- **Port**: 5432
- **Database**: postgres
- **User**: postgres
- **Status**: ✅ Connected and ready

All tables created:
- `users` - User accounts
- `event_options` - Customizable event types
- `night_events` - Logged nighttime events
- `day_notes` - Daily activity notes
- Plus Django system tables

## 📦 Using Docker

### Build and Run

```bash
docker compose up --build -d
```

### View Logs

```bash
docker compose logs -f web
```

### Stop Containers

```bash
docker compose down
```

### Access Container Shell

```bash
docker compose exec web bash
```

## 🔐 Admin Access

After creating a superuser, you can access the Django admin at:

**http://localhost:8000/admin**

From here you can:
- Manage all users
- View all event options
- See all logged events
- Access day notes
- Manage data

## 📝 Common Commands

```bash
# Test database connection
python test_db.py

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create default event options for existing users
python manage.py create_default_options

# Collect static files
python manage.py collectstatic

# Run development server
python manage.py runserver

# Access Django shell
python manage.py shell
```

## 🌐 Production Setup

1. **Update .env for production**:
   ```env
   DJANGO_SETTINGS_MODULE=config.settings.production
   DEBUG=False
   ALLOWED_HOSTS=your-domain.com,your-ip
   ```

2. **Add R2 credentials** (already in .env.example):
   - AWS_ACCESS_KEY_ID
   - AWS_SECRET_ACCESS_KEY
   - AWS_STORAGE_BUCKET_NAME
   - AWS_S3_ENDPOINT_URL

3. **Run build script**:
   ```bash
   ./build.sh
   ```

## 🎯 Next Steps

1. Create your superuser account
2. Start the dev server
3. Sign up for a regular account
4. Log your first event!
5. Add day notes
6. Customize your event options
7. View the dashboard

## 📞 Need Help?

- Check the main README.md for detailed documentation
- Run `python test_db.py` to verify database connection
- Check logs: `docker compose logs -f web`

---

**Your database is ready and waiting! Just create your account and start tracking!** 🚀
