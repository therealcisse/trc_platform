# Heroku Deployment Guide for Django Backend

This guide provides step-by-step instructions for deploying the Image Solve Platform backend to Heroku.

## Prerequisites

1. Heroku CLI installed: `brew install heroku/brew/heroku`
2. A Heroku account (free or paid)
3. Git repository initialized

## Initial Setup

### 1. Create a Heroku App

```bash
# Login to Heroku
heroku login

# Create a new Heroku app
heroku create your-app-name

# Or if you want Heroku to generate a name
heroku create
```

### 2. Add PostgreSQL Database

```bash
# Add Heroku Postgres (free tier)
heroku addons:create heroku-postgresql:essential-0

# This automatically sets DATABASE_URL environment variable
```

### 3. Configure Environment Variables

Set all required environment variables:

```bash
# Generate a secure secret key
heroku config:set DJANGO_SECRET_KEY='your-secure-secret-key-here'

# Set production environment
heroku config:set DJANGO_DEBUG=0
heroku config:set ENV=production

# Set your app's domain
heroku config:set ALLOWED_HOSTS=your-app-name.herokuapp.com
heroku config:set CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
heroku config:set CSRF_TRUSTED_ORIGINS=https://your-frontend-domain.com

# OpenAI Configuration
heroku config:set OPENAI_API_KEY='sk-your-api-key'
heroku config:set OPENAI_MODEL='gpt-4-vision-preview'
heroku config:set USE_MOCK_OPENAI=false

# Email Configuration (using Resend)
heroku config:set RESEND_API_KEY='your-resend-api-key'
heroku config:set DEFAULT_FROM_EMAIL='noreply@yourdomain.com'

# Billing Settings
heroku config:set COST_PER_REQUEST_CENTS=100

# Optional: Sentry for error tracking
heroku config:set SENTRY_DSN='your-sentry-dsn'
```

### 4. Verify Configuration

```bash
# View all config vars
heroku config

# View specific config var
heroku config:get DJANGO_SECRET_KEY
```

## Deployment

### 1. Prepare Your Repository

```bash
# Ensure you're in the backend directory
cd /path/to/backend

# Add Heroku remote if not already added
heroku git:remote -a your-app-name

# Check your remotes
git remote -v
```

### 2. Deploy to Heroku

```bash
# Commit your changes
git add .
git commit -m "Prepare for Heroku deployment"

# Deploy to Heroku
git push heroku main

# Or if you're on a different branch
git push heroku your-branch:main
```

### 3. Run Database Migrations

The migrations will run automatically via the Procfile's release command, but you can also run them manually:

```bash
heroku run python manage.py migrate
```

### 4. Create a Superuser

```bash
heroku run python manage.py createsuperuser
```

### 5. Bootstrap Demo Data (Optional)

```bash
heroku run python manage.py bootstrap_demo
```

## Post-Deployment

### Check Application Status

```bash
# View application logs
heroku logs --tail

# Check dyno status
heroku ps

# Open the application
heroku open
```

### Scaling

```bash
# Scale web dynos (free tier allows 1)
heroku ps:scale web=1

# For paid plans, you can scale up
heroku ps:scale web=2
```

### Database Management

```bash
# Access database shell
heroku pg:psql

# Backup database
heroku pg:backups:capture

# View backups
heroku pg:backups

# Download latest backup
heroku pg:backups:download
```

## Monitoring and Maintenance

### View Logs

```bash
# Real-time logs
heroku logs --tail

# Specific number of lines
heroku logs -n 200

# Filter by process type
heroku logs --source app --tail
```

### Django Shell Access

```bash
heroku run python manage.py shell
```

### Run Management Commands

```bash
# Create billing periods
heroku run python manage.py create_billing_periods

# Mark overdue periods
heroku run python manage.py mark_overdue_periods
```

## Troubleshooting

### Common Issues

1. **Collectstatic errors**: WhiteNoise handles static files automatically
2. **Database connection errors**: Ensure DATABASE_URL is set (automatic with Heroku Postgres)
3. **Module import errors**: Check requirements.txt includes all dependencies
4. **ALLOWED_HOSTS error**: Ensure your Heroku app domain is in ALLOWED_HOSTS

### Debug Production Issues

```bash
# Temporarily enable debug mode (not recommended for production)
heroku config:set DJANGO_DEBUG=1

# Check specific logs
heroku logs --tail --source app

# Run Django check
heroku run python manage.py check --deploy

# Don't forget to disable debug mode
heroku config:set DJANGO_DEBUG=0
```

## Continuous Deployment

### Using GitHub Integration

1. Connect your GitHub repo in Heroku Dashboard
2. Enable automatic deploys from main branch
3. Optional: Enable review apps for PRs

### Using Heroku CLI

```bash
# Deploy specific branch
git push heroku feature-branch:main

# Force push if needed
git push heroku main --force
```

## Security Checklist

- [ ] DJANGO_SECRET_KEY is unique and secure
- [ ] DJANGO_DEBUG is set to 0
- [ ] Database has SSL enabled (automatic with Heroku Postgres)
- [ ] ALLOWED_HOSTS is properly configured
- [ ] CORS_ALLOWED_ORIGINS only includes your frontend domain
- [ ] Sentry or similar error tracking is configured
- [ ] Regular database backups are scheduled

## Useful Heroku Commands

```bash
# Restart application
heroku restart

# View environment info
heroku info

# View available add-ons
heroku addons

# SSH into dyno (for debugging)
heroku run bash

# View recent deployments
heroku releases

# Rollback to previous version
heroku rollback
```

## Cost Considerations

### Free Tier Limitations (Eco Dyno)
- 1000 dyno hours per month
- Sleeps after 30 minutes of inactivity
- No custom domain SSL

### Recommended Paid Setup
- Basic dyno: $7/month (no sleeping)
- Essential-0 Postgres: $5/month (10K rows)
- Total: ~$12/month minimum

## Additional Resources

- [Heroku Django Guide](https://devcenter.heroku.com/articles/django-app-configuration)
- [Heroku Postgres Documentation](https://devcenter.heroku.com/articles/heroku-postgresql)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
