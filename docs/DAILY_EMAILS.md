# Daily Email Summaries

OvernightApp can send automated daily email summaries to users and their designated recipients (family members, caregivers, etc.).

## How It Works

1. Users enable daily emails in their Settings page
2. Users configure:
   - What time to send (in their timezone)
   - Who should receive the emails (comma-separated email addresses)
3. A scheduled task runs every 15 minutes checking for users whose email time has arrived
4. Emails include:
   - Events from the last 24 hours
   - Day note from yesterday (if present)
   - Event counts and timestamps

## Email Configuration

### 1. Configure Email Settings

Update your `.env` file with SMTP credentials:

```bash
# For Gmail (recommended: use App Password, not your regular password)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=OvernightApp <noreply@yourdomain.com>
```

#### Getting a Gmail App Password

1. Go to your Google Account settings
2. Navigate to Security
3. Enable 2-Step Verification (if not already enabled)
4. Under "2-Step Verification", find "App passwords"
5. Generate a new app password for "Mail"
6. Use this 16-character password in `EMAIL_HOST_PASSWORD`

#### Alternative Email Providers

**Brevo (formerly Sendinblue) - Recommended:**
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-brevo-email@example.com
EMAIL_HOST_PASSWORD=your-brevo-smtp-key
DEFAULT_FROM_EMAIL=OvernightApp <noreply@yourdomain.com>
```

To get Brevo SMTP credentials:
1. Sign up at https://www.brevo.com (free tier: 300 emails/day)
2. Go to Settings → SMTP & API
3. Create new SMTP key
4. Use your Brevo login email as EMAIL_HOST_USER
5. Use the generated SMTP key as EMAIL_HOST_PASSWORD

**SendGrid:**
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
```

**Mailgun:**
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.mailgun.org
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=postmaster@your-domain.mailgun.org
EMAIL_HOST_PASSWORD=your-mailgun-password
```

### 2. Set Up Scheduled Task

The email command should run every 15 minutes to check for users whose email time has arrived.

#### Using Cron (Linux/Mac)

Edit your crontab:

```bash
crontab -e
```

Add this line to run every 15 minutes:

```bash
*/15 * * * * cd /path/to/OvernightApp && docker compose exec -T web python manage.py send_daily_emails >> /var/log/overnight_emails.log 2>&1
```

Or if running without Docker:

```bash
*/15 * * * * cd /path/to/OvernightApp && /path/to/venv/bin/python manage.py send_daily_emails >> /var/log/overnight_emails.log 2>&1
```

#### Using systemd Timer (Linux)

Create `/etc/systemd/system/overnight-emails.service`:

```ini
[Unit]
Description=Send OvernightApp Daily Emails
After=docker.service

[Service]
Type=oneshot
WorkingDirectory=/path/to/OvernightApp
ExecStart=/usr/bin/docker compose exec -T web python manage.py send_daily_emails
User=your-user
Group=your-group
```

Create `/etc/systemd/system/overnight-emails.timer`:

```ini
[Unit]
Description=Run OvernightApp Email Service Every 15 Minutes
Requires=overnight-emails.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=15min
Unit=overnight-emails.service

[Install]
WantedBy=timers.target
```

Enable and start the timer:

```bash
sudo systemctl daemon-reload
sudo systemctl enable overnight-emails.timer
sudo systemctl start overnight-emails.timer
```

Check status:

```bash
sudo systemctl status overnight-emails.timer
sudo systemctl list-timers overnight-emails.timer
```

## Testing

### Test Email Sending (Development)

For development/testing, you can use Django's console backend which prints emails to console instead of sending them:

```bash
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### Test the Command

Test for a specific user (ignores time check):

```bash
# With Docker
docker compose exec web python manage.py send_daily_emails --force --user=davidhale87

# Without Docker
python manage.py send_daily_emails --force --user=davidhale87
```

Force send for all users regardless of time:

```bash
docker compose exec web python manage.py send_daily_emails --force
```

Normal run (respects time settings):

```bash
docker compose exec web python manage.py send_daily_emails
```

### Check Logs

View the command output:

```bash
# If using cron log
tail -f /var/log/overnight_emails.log

# If using systemd
journalctl -u overnight-emails.service -f

# Docker logs
docker compose logs -f web
```

## User Configuration

Users can configure their email preferences at: `https://your-domain.com/users/settings/`

Settings include:
- **Enable Daily Summary Email**: Toggle to enable/disable
- **Email Time**: Time to send (in user's timezone, e.g., 7:00 AM)
- **Email Recipients**: Comma-separated email addresses (e.g., `mom@example.com, dad@example.com, nurse@example.com`)

## Email Content

The daily summary email includes:

1. **Header**: Date and total event count
2. **Day Note**: Yesterday's day note (if present)
3. **Night Events**: All events from last 24 hours with:
   - Timestamp (in user's timezone)
   - Event options (colored badges)
   - Notes (if any)

## Troubleshooting

### Emails Not Sending

1. **Check email configuration**:
   ```bash
   docker compose exec web python manage.py shell
   >>> from django.core.mail import send_mail
   >>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
   ```

2. **Check user settings**:
   - Is daily_email_enabled = True?
   - Are recipients configured?
   - Is the current time within 15 minutes of daily_email_time?

3. **Check logs**:
   ```bash
   docker compose logs web | grep "send_daily_emails"
   ```

4. **Verify cron is running**:
   ```bash
   # Check cron service
   sudo systemctl status cron

   # Check if crontab is set
   crontab -l
   ```

### SMTP Authentication Failed

- For Gmail: Ensure you're using an App Password, not your regular password
- Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are correct
- Check if "Less secure app access" is needed (not recommended)

### Emails Going to Spam

- Set up SPF, DKIM, and DMARC records for your domain
- Use a verified email service (SendGrid, Mailgun, AWS SES)
- Ensure DEFAULT_FROM_EMAIL uses a real domain you control

## Security Notes

- Never commit email credentials to git
- Use environment variables for sensitive data
- Consider using a dedicated email service (SendGrid, Mailgun) for production
- Rotate email credentials periodically
- Monitor for unusual email activity

## Advanced Configuration

### Rate Limiting

If sending to many users, you may want to add rate limiting:

```python
# In send_daily_emails.py
import time

for user in users:
    # Send email...
    time.sleep(1)  # Wait 1 second between sends
```

### Custom Email Templates

Email template location: `apps/care_tracking/templates/care_tracking/emails/daily_summary.html`

Customize the HTML/CSS to match your branding.

### Email Delivery Monitoring

Consider integrating with email service webhooks to track:
- Delivery success/failure
- Bounces
- Opens/clicks (if needed)
