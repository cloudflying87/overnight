# OvernightApp - Care Tracking System

A Django web application for tracking and monitoring nighttime care events. Built to help caregivers track patterns and correlate daily activities with nighttime events.

## Features

### ✨ Core Functionality
- **User Authentication**: Secure login/logout with password reset functionality
- **Nighttime Event Logging**: Track events with customizable options and timestamps
- **Day Notes**: Record daily activities, diet, mood, and observations
- **Event Options Management**: Customize your own event types with colors
- **Dashboard**: Overview of recent events and quick statistics
- **Auto-populated Defaults**: 10 pre-configured event options for new users

### 🎯 Default Event Options
- Underwear change
- Underwear/Clothes wet
- Bed clothes wet
- Sheets rearranged
- Sheets changed
- Need to pee
- Active Sleeping
- Settled Sleeping
- Moving around the mattresses/room
- PJ's Top and/or Bottom off

### 🔐 Security Features
- Custom user model with email uniqueness
- Password validation
- CSRF protection
- Secure session handling
- Production-ready security settings

### 📊 Data Management
- User-scoped data (each caregiver sees only their data)
- Many-to-many relationship between events and options
- Automatic timestamps for event logging
- Soft delete for event options
- Unique constraints to prevent duplicates

## Technology Stack

- **Backend**: Django 5.0.3
- **Database**: PostgreSQL (external)
- **Storage**: Cloudflare R2 (for static/media files in production)
- **Caching**: Redis
- **Frontend**: Bootstrap 5
- **Containerization**: Docker + Docker Compose

## Project Structure

```
OvernightApp/
├── apps/
│   ├── users/              # User authentication & management
│   └── care_tracking/      # Core care tracking functionality
├── config/                 # Django project settings
│   ├── settings/
│   │   ├── base.py        # Shared settings
│   │   ├── development.py # Dev environment
│   │   └── production.py  # Production environment
│   └── urls.py
├── static/                 # CSS, JavaScript, images
├── templates/              # HTML templates
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Service orchestration
├── requirements.txt        # Python dependencies
└── .env                    # Environment variables
```

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL database (external)
- Cloudflare R2 account (for production)
- Docker & Docker Compose (optional)

### 1. Clone and Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and update with your credentials:

```env
# Django settings
DJANGO_SETTINGS_MODULE=config.settings.development
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL Database
DATABASE_NAME=overnight_db
DATABASE_USER=your_db_user
DATABASE_PASSWORD=your_db_password
DATABASE_HOST=your_db_host
DATABASE_PORT=5432

# Cloudflare R2 (for production)
AWS_ACCESS_KEY_ID=your_r2_access_key
AWS_SECRET_ACCESS_KEY=your_r2_secret_key
AWS_STORAGE_BUCKET_NAME=your_bucket_name
AWS_S3_ENDPOINT_URL=https://your-account-id.r2.cloudflarestorage.com
```

### 3. Database Setup

```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# (Optional) Create default options for existing users
python manage.py create_default_options
```

### 4. Run Development Server

```bash
# Collect static files
python manage.py collectstatic --noinput

# Run server
python manage.py runserver
```

Visit `http://localhost:8000` and sign up for an account!

## Docker Deployment

### Using Docker Compose

```bash
# Build and start services
docker-compose up --build

# Run migrations (first time)
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

The app will be available at `http://localhost:8000`

## Usage Guide

### 1. Sign Up
- Create a new account with username, email, and password
- Default event options are automatically created for you

### 2. Log Events
1. Click "Log Event" from the dashboard or navigation
2. Select one or more event options
3. Add optional notes
4. Timestamp is auto-filled with current time (editable)
5. Click "Log Event"

### 3. Manage Event Options
- View all your event options in "Event Options"
- Create new custom options with colors
- Edit or deactivate existing options
- Inactive options won't appear when logging events

### 4. Add Day Notes
- Track daily activities, diet, mood, schedule changes
- One note per day per user
- Helps correlate daily patterns with nighttime events

### 5. View Dashboard
- See recent events and day notes
- Quick statistics (events this week, total events, etc.)
- Quick action buttons for common tasks

## Management Commands

### Create Default Event Options

```bash
# For all users without options
python manage.py create_default_options

# For a specific user
python manage.py create_default_options --username=john

# For ALL users (even those with existing options)
python manage.py create_default_options --all
```

## Development

### Settings Environments

- **Development** (`config.settings.development`):
  - DEBUG=True
  - SQLite or external PostgreSQL
  - WhiteNoise for static files
  - Console email backend
  - Django Debug Toolbar enabled

- **Production** (`config.settings.production`):
  - DEBUG=False
  - External PostgreSQL required
  - Cloudflare R2 for static/media files
  - Security headers enabled
  - Session stored in Redis

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.users
python manage.py test apps.care_tracking
```

## Database Models

### User
- Custom user model extending AbstractUser
- Fields: username, email (unique), display_name
- Automatic timestamps

### EventOption
- User-customizable event types
- Fields: name, description, color_code, is_active
- Unique constraint: (user, name)

### NightEvent
- Individual logged events
- Many-to-many relationship with EventOption
- Fields: event_datetime, notes, created_at
- User-scoped data

### DayNote
- Daily activity notes
- Fields: date, content
- Unique constraint: (user, date) - one note per day

## API Endpoints

All endpoints require authentication except login/signup.

### Authentication
- `GET/POST /users/login/` - User login
- `GET/POST /users/signup/` - User registration
- `GET /users/logout/` - User logout
- `POST /users/password-reset/` - Request password reset

### Dashboard
- `GET /` - Main dashboard

### Event Options
- `GET /options/` - List all event options
- `GET/POST /options/create/` - Create new option
- `GET/POST /options/<id>/edit/` - Edit option
- `POST /options/<id>/delete/` - Delete option

### Night Events
- `GET /events/` - List all events
- `GET/POST /events/log/` - Log new event
- `GET/POST /events/<id>/edit/` - Edit event
- `POST /events/<id>/delete/` - Delete event

### Day Notes
- `GET /notes/` - List all day notes
- `GET/POST /notes/create/` - Create new note
- `GET/POST /notes/<id>/edit/` - Edit note
- `POST /notes/<id>/delete/` - Delete note

## Future Enhancements

### Phase 6: Trend Analysis (Planned)
- Line charts showing event frequency over time
- Bar charts for event type distribution
- Correlation analysis between day notes and nighttime events
- Date range filtering
- Export to CSV/PDF

### Additional Features
- Email notifications
- Shared access for multiple caregivers (households)
- Mobile app (Django REST API)
- Advanced pattern detection with ML
- Custom report builder

## Troubleshooting

### Database Connection Issues
```bash
# Test PostgreSQL connection
python manage.py dbshell

# Check database settings
python manage.py showmigrations
```

### Static Files Not Loading
```bash
# Development
python manage.py collectstatic --noinput

# Check STATIC_ROOT and STATIC_URL in settings
```

### R2 Upload Issues
- Verify R2 credentials in `.env`
- Check bucket permissions
- Ensure `AWS_S3_ENDPOINT_URL` is correct

## Contributing

This is a personal care tracking project. If you'd like to contribute:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is for personal use.

## Support

For issues or questions, please open an issue in the repository.

## Changelog

### Version 1.0.0 (Current)
- Initial release
- User authentication system
- Event logging with customizable options
- Day notes functionality
- Dashboard with quick stats
- Docker deployment support
- PostgreSQL + Cloudflare R2 integration

---

**Built with Django & PostgreSQL for tracking and improving nighttime care patterns.**
