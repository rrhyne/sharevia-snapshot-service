# Quick Start Guide

## Initial Setup

1. **Copy environment variables from backend**

```bash
# Copy .env from backend (if you have one)
cp ../backend/.env .env

# OR create from template
cp .env.example .env
```

2. **Edit .env file with your credentials**

```bash
# Edit the .env file
nano .env
```

Required variables:
- `BRIGHTDATA_TOKEN` - Your Brightdata API token
- `SUPABASE_PROJECT_REF` - Your Supabase project reference (e.g., kqcksqolkgzrqyxjqvul)
- `SUPABASE_SERVICE_ROLE_KEY` - Your Supabase service role key

Optional:
- `SNAPSHOT_POLL_INTERVAL` - How often to poll (default: 60 seconds)

3. **Install dependencies**

```bash
pip3 install -r requirements.txt
```

## Running the Service

### Option 1: Run Directly (for testing)

```bash
# Start the service
python3 main.py

# Stop with Ctrl+C
```

### Option 2: Run as Background Process

```bash
# Start
./service.sh start

# Check status
./service.sh status

# View logs
./service.sh logs

# Stop
./service.sh stop

# Restart
./service.sh restart
```

### Option 3: Run as macOS Service (launchd)

```bash
# Copy plist file to LaunchAgents
cp com.sharevia.snapshot.plist ~/Library/LaunchAgents/

# Load the service (starts automatically)
launchctl load ~/Library/LaunchAgents/com.sharevia.snapshot.plist

# Check if running
launchctl list | grep sharevia

# View logs
tail -f logs/snapshot-service.out.log

# Unload (stop) the service
launchctl unload ~/Library/LaunchAgents/com.sharevia.snapshot.plist
```

## Verifying It Works

1. **Check the logs**

```bash
# If running with service.sh
./service.sh logs

# If running with launchd
tail -f logs/snapshot-service.out.log
```

2. **What to look for**

You should see output like:
```
2024-11-08 13:00:00 - __main__ - INFO - Sharevia Snapshot Service Starting
2024-11-08 13:00:00 - __main__ - INFO - Configuration:
2024-11-08 13:00:00 - __main__ - INFO -   - Poll interval: 60 seconds
2024-11-08 13:00:01 - snapshot_service - INFO - Starting Brightdata snapshot polling service
2024-11-08 13:00:01 - snapshot_service - INFO - Checking for snapshots (iteration 1)...
2024-11-08 13:00:02 - brightdata_client - INFO - Retrieved 5 snapshots
```

## Troubleshooting

### "Missing required environment variables"

Make sure your `.env` file exists and contains all required variables.

### "ImportError" or "ModuleNotFoundError"

Install dependencies:
```bash
pip3 install -r requirements.txt
```

### Service won't start

Check if another instance is already running:
```bash
./service.sh status
```

### No snapshots being processed

1. Make sure the backend is creating snapshots (look for 202 responses)
2. Check Brightdata API is accessible
3. Verify your BRIGHTDATA_TOKEN is valid

## Next Steps

- Monitor logs to ensure snapshots are being processed
- Check your Supabase bookmarks table to verify updates
- Adjust `SNAPSHOT_POLL_INTERVAL` if needed (lower = more frequent checks)
