# Cron Job Setup for Scraper

This guide explains how to set up a cron job to automatically run the scraper on Linux/Mac systems.

---

## 📋 Prerequisites

- Linux or Mac system
- Python 3 installed
- Access to crontab (usually requires user account, not necessarily root)

---

## 🔧 Step 1: Open Crontab Editor

Open your crontab file for editing:

```bash
crontab -e
```

If this is your first time, you'll be asked to choose an editor. Choose your preferred editor (nano is easiest for beginners).

---

## 📝 Step 2: Add Cron Job

Add one of the following lines to your crontab file, depending on your desired schedule:

### Run Daily at 2:00 AM

```cron
0 2 * * * cd /path/to/phygitals && /usr/bin/python3 scraper_marketplace_url.py --no-resume >> /path/to/phygitals/scraper.log 2>&1
```

### Run Every 6 Hours

```cron
0 */6 * * * cd /path/to/phygitals && /usr/bin/python3 scraper_marketplace_url.py --no-resume >> /path/to/phygitals/scraper.log 2>&1
```

### Run Every 12 Hours (Twice Daily)

```cron
0 */12 * * * cd /path/to/phygitals && /usr/bin/python3 scraper_marketplace_url.py --no-resume >> /path/to/phygitals/scraper.log 2>&1
```

### Run Every 2 Hours

```cron
0 */2 * * * cd /path/to/phygitals && /usr/bin/python3 scraper_marketplace_url.py --no-resume >> /path/to/phygitals/scraper.log 2>&1
```

### Run Every Day at Multiple Times (e.g., 2 AM and 2 PM)

```cron
0 2,14 * * * cd /path/to/phygitals && /usr/bin/python3 scraper_marketplace_url.py --no-resume >> /path/to/phygitals/scraper.log 2>&1
```

### Run Every Weekday at 2 AM (Monday-Friday)

```cron
0 2 * * 1-5 cd /path/to/phygitals && /usr/bin/python3 scraper_marketplace_url.py --no-resume >> /path/to/phygitals/scraper.log 2>&1
```

### Run Every Sunday at Midnight

```cron
0 0 * * 0 cd /path/to/phygitals && /usr/bin/python3 scraper_marketplace_url.py --no-resume >> /path/to/phygitals/scraper.log 2>&1
```

---

## 📖 Cron Syntax Explanation

```
* * * * * command
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, Sunday = 0 or 7)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

### Common Patterns:

- `0 2 * * *` = Every day at 2:00 AM
- `0 */6 * * *` = Every 6 hours (at minute 0 of hours 0, 6, 12, 18)
- `0 */12 * * *` = Every 12 hours (at minute 0 of hours 0 and 12)
- `0 0 * * 0` = Every Sunday at midnight
- `30 3 * * 1-5` = Every weekday (Mon-Fri) at 3:30 AM
- `0 2,14 * * *` = Every day at 2:00 AM and 2:00 PM

---

## ⚙️ Important Configuration

### Replace Paths

**IMPORTANT**: Replace these placeholders with your actual paths:

1. `/path/to/phygitals` - Replace with your actual project directory
   - Example: `/home/username/phygitals`
   - Example: `/Users/username/Desktop/phygitals`

2. `/usr/bin/python3` - Replace with your Python 3 executable path
   - Find it with: `which python3`
   - Common locations:
     - `/usr/bin/python3`
     - `/usr/local/bin/python3`
     - `/opt/homebrew/bin/python3` (Mac with Homebrew)

### Example with Real Paths

If your project is at `/home/john/phygitals` and Python is at `/usr/bin/python3`:

```cron
0 2 * * * cd /home/john/phygitals && /usr/bin/python3 scraper_marketplace_url.py --no-resume >> /home/john/phygitals/scraper.log 2>&1
```

---

## 📊 Logging Explained

The `>> /path/to/phygitals/scraper.log 2>&1` part:

- `>>` = Append output to log file (creates file if it doesn't exist)
- `scraper.log` = Name of the log file
- `2>&1` = Redirect error messages (stderr) to the same file as standard output

This ensures all output (both success and error messages) is saved to the log file.

---

## 🔍 Step 3: Verify Cron Job

### List All Cron Jobs

```bash
crontab -l
```

This shows all your scheduled cron jobs.

### Check Cron Service Status

**Linux:**
```bash
sudo systemctl status cron
# or
sudo service cron status
```

**Mac:**
```bash
sudo launchctl list | grep cron
```

### View Cron Logs

**Linux:**
```bash
# View system cron log
sudo tail -f /var/log/cron

# View user cron output (if mail is configured)
mail
```

**Mac:**
```bash
# View system log for cron
tail -f /var/log/system.log | grep cron
```

---

## 🧪 Step 4: Test the Cron Job

Before relying on the cron job, test it manually:

```bash
cd /path/to/phygitals
/usr/bin/python3 scraper_marketplace_url.py --no-resume
```

If this works, your cron job should work too.

---

## 🛠️ Advanced Options

### Prevent Multiple Instances

To prevent the scraper from running if it's already running, use a lock file:

```cron
0 2 * * * cd /path/to/phygitals && flock -n /tmp/scraper.lock /usr/bin/python3 scraper_marketplace_url.py --no-resume >> /path/to/phygitals/scraper.log 2>&1
```

This requires the `flock` utility (usually pre-installed on Linux, install via Homebrew on Mac).

### Run with Virtual Environment

If you're using a Python virtual environment:

```cron
0 2 * * * cd /path/to/phygitals && /path/to/venv/bin/python scraper_marketplace_url.py --no-resume >> /path/to/phygitals/scraper.log 2>&1
```

### Set Environment Variables

If your scraper needs environment variables:

```cron
0 2 * * * cd /path/to/phygitals && PATH=/usr/bin:/bin:/usr/local/bin /usr/bin/python3 scraper_marketplace_url.py --no-resume >> /path/to/phygitals/scraper.log 2>&1
```

Or export them before the command:

```cron
0 2 * * * export VARIABLE_NAME=value && cd /path/to/phygitals && /usr/bin/python3 scraper_marketplace_url.py --no-resume >> /path/to/phygitals/scraper.log 2>&1
```

---

## 🗑️ Remove or Edit Cron Job

### Edit Existing Cron Job

```bash
crontab -e
```

Make your changes and save.

### Remove All Cron Jobs

```bash
crontab -r
```

**Warning**: This removes ALL your cron jobs!

### Remove Specific Cron Job

```bash
crontab -e
```

Then delete the line you want to remove.

---

## 🐛 Troubleshooting

### Cron Job Doesn't Run

1. **Check cron service is running:**
   ```bash
   sudo systemctl status cron  # Linux
   ```

2. **Verify Python path:**
   ```bash
   which python3
   ```

3. **Check file permissions:**
   ```bash
   chmod +x scraper_marketplace_url.py
   ```

4. **Check cron logs for errors:**
   ```bash
   sudo tail -f /var/log/cron  # Linux
   ```

5. **Test command manually:**
   ```bash
   cd /path/to/phygitals
   /usr/bin/python3 scraper_marketplace_url.py --no-resume
   ```

### Path Issues

- Always use **absolute paths** in cron jobs
- Cron runs with minimal environment variables
- Set PATH explicitly if needed: `PATH=/usr/bin:/bin`

### Permission Issues

- Ensure the script is executable: `chmod +x scraper_marketplace_url.py`
- Check file ownership matches your user
- Verify write permissions for log file directory

### No Output in Log File

- Check if log file directory exists and is writable
- Verify the `>>` redirection syntax is correct
- Check disk space: `df -h`

---

## 📋 Recommended Schedules

For marketplace data scraping:

- **Conservative**: Once daily at 2:00 AM (low traffic time)
- **Moderate**: Every 12 hours (2 AM and 2 PM)
- **Aggressive**: Every 6 hours (4 times daily)
- **Real-time**: Every 2-3 hours (8-12 times daily)

**Note**: More frequent scraping = more server load. Start with daily and adjust based on your needs.

---

## 📝 Complete Example

Here's a complete example cron job setup:

```bash
# 1. Open crontab
crontab -e

# 2. Add this line (replace paths with your actual paths):
0 2 * * * cd /home/username/phygitals && /usr/bin/python3 scraper_marketplace_url.py --no-resume >> /home/username/phygitals/scraper.log 2>&1

# 3. Save and exit (in nano: Ctrl+X, then Y, then Enter)

# 4. Verify it was added
crontab -l

# 5. Check cron service
sudo systemctl status cron

# 6. Monitor logs
tail -f /home/username/phygitals/scraper.log
```

---

## 🔗 Related Commands

- `crontab -e` - Edit cron jobs
- `crontab -l` - List cron jobs
- `crontab -r` - Remove all cron jobs
- `which python3` - Find Python 3 path
- `pwd` - Get current directory path
- `chmod +x script.py` - Make script executable

---

## ⚠️ Important Notes

1. **Cron runs with minimal environment** - Always use full paths
2. **Cron doesn't load shell profiles** - Set PATH and variables explicitly
3. **Log everything** - Use `>> logfile.log 2>&1` to capture all output
4. **Test manually first** - Always test the command before adding to cron
5. **Dashboard auto-refresh** - The dashboard will automatically detect when scraper runs and refresh every 30 seconds (no additional setup needed)

---

## 📞 Quick Reference

**Basic Cron Job Format:**
```cron
minute hour day month weekday command
```

**Common Schedule Examples:**
- `0 2 * * *` = Daily at 2:00 AM
- `0 */6 * * *` = Every 6 hours
- `0 2,14 * * *` = Twice daily (2 AM and 2 PM)
- `0 0 * * 0` = Weekly (Sunday midnight)

**Essential Commands:**
- `crontab -e` - Edit cron jobs
- `crontab -l` - List cron jobs
- `which python3` - Find Python path
- `tail -f logfile.log` - Monitor logs

