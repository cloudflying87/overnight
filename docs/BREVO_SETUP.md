# Brevo Email Setup Guide

Quick guide to set up Brevo (formerly Sendinblue) for OvernightApp daily emails.

## Why Brevo?

- **Free tier**: 300 emails/day (plenty for daily summaries)
- **Reliable**: Professional email delivery service
- **Easy setup**: Simple SMTP configuration
- **No credit card required** for free tier

## Setup Steps

### 1. Create Brevo Account

1. Go to https://www.brevo.com
2. Click "Sign up free"
3. Enter your email and create password
4. Verify your email address

### 2. Get SMTP Credentials

1. Log in to Brevo
2. Go to **Settings** (top right) → **SMTP & API**
3. Click **"Create a new SMTP key"**
4. Give it a name (e.g., "OvernightApp")
5. Copy the generated SMTP key (you won't see it again!)

### 3. Update .env File

On your production server (globemaster), edit `/docker/overnight/.env`:

```bash
# Email Configuration - Brevo
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-brevo-account-email@example.com
EMAIL_HOST_PASSWORD=your-brevo-smtp-key-from-step-2
DEFAULT_FROM_EMAIL=OvernightApp <noreply@yourdomain.com>
```

**Important:**
- `EMAIL_HOST_USER` = The email you used to sign up for Brevo
- `EMAIL_HOST_PASSWORD` = The SMTP key you generated in step 2
- `DEFAULT_FROM_EMAIL` = Can be any address (Brevo will handle it)

### 4. Rebuild and Test

```bash
# On globemaster
cd /docker/overnight
./build.sh

# Test email sending
docker compose exec web python manage.py send_daily_emails --force --user=yourusername
```

Check the logs:
```bash
docker compose logs -f web
```

You should see:
```
Sent email to yourusername (X recipient(s)): email1@example.com, email2@example.com
```

### 5. Set Up Cron Job

Add to crontab to run every 15 minutes:

```bash
crontab -e
```

Add this line:
```bash
*/15 * * * * cd /docker/overnight && docker compose exec -T web python manage.py send_daily_emails >> /var/log/overnight_emails.log 2>&1
```

## Troubleshooting

### "Authentication failed"
- Double-check EMAIL_HOST_USER matches your Brevo account email
- Regenerate SMTP key in Brevo and update .env
- Make sure you copied the full SMTP key (no spaces)

### "Connection refused"
- Check EMAIL_HOST=smtp-relay.brevo.com (not smtp-relay.sendinblue.com)
- Verify EMAIL_PORT=587
- Ensure EMAIL_USE_TLS=True

### Emails not sending
1. Check user settings at `/users/settings/`:
   - Daily email enabled?
   - Recipients configured?
   - Time set correctly?

2. Test manually:
   ```bash
   docker compose exec web python manage.py send_daily_emails --force --user=yourusername
   ```

3. Check Django can send emails:
   ```bash
   docker compose exec web python manage.py shell
   >>> from django.core.mail import send_mail
   >>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
   ```

### Emails going to spam
- Add SPF record to your domain DNS
- Use a real "from" email address you control
- Consider verifying your domain in Brevo (optional)

## Daily Email Limits

Brevo free tier allows **300 emails/day**.

Example usage:
- 10 users × 1 email/day = 10 emails/day
- Each email can have multiple recipients (family members)
- Well within the 300 email limit

If you need more, Brevo paid plans start at $25/month for 20,000 emails.

## Monitoring

Check email delivery in Brevo dashboard:
1. Go to **Statistics** → **Email**
2. View sent, delivered, bounced emails
3. Monitor for any issues

## Security Notes

- **Never commit** EMAIL_HOST_PASSWORD to git
- Store SMTP key securely
- Rotate keys periodically
- Monitor Brevo logs for suspicious activity
