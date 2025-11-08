# Sharevia Snapshot Service

A standalone background service for polling and processing Brightdata snapshots.

## Overview

This service handles async scraping jobs from the Sharevia backend. When the backend receives a 202 response from Brightdata (indicating the scrape will take longer than 1 minute), it saves the `snapshot_id` to the database. This service then:

1. Polls Brightdata API for available snapshots
2. Checks status (pending/running/ready/failed)
3. Downloads results when status is 'ready'
4. Processes results using Brightdata extraction functions
5. Looks up bookmark in Supabase by URL
6. Updates bookmark with extracted content, images, videos, and social profile

This ensures that async scraping jobs eventually complete and update bookmarks with the full scraped data from X/Twitter and LinkedIn.

## Installation

```bash
# Clone the repository
cd /path/to/sharevia_snapshot_service

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your credentials
```

## Configuration

Create a `.env` file with the following variables:

```env
# Brightdata API credentials
BRIGHTDATA_TOKEN=your_brightdata_token_here

# Supabase configuration (matches backend/.env)
SUPABASE_PROJECT_REF=your_project_ref_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# Optional: Polling interval in seconds (default: 60)
SNAPSHOT_POLL_INTERVAL=60
```

## Running

### Directly

```bash
python3 main.py
```

### With custom poll interval

```bash
SNAPSHOT_POLL_INTERVAL=30 python3 main.py
```

### As a background service (macOS)

Using launchd:

```bash
# Copy the plist file
cp com.sharevia.snapshot.plist ~/Library/LaunchAgents/

# Load the service
launchctl load ~/Library/LaunchAgents/com.sharevia.snapshot.plist

# Check status
launchctl list | grep sharevia

# View logs
tail -f logs/snapshot-service.out.log
tail -f logs/snapshot-service.err.log
```

### Using the service manager script

```bash
# Start the service
./service.sh start

# Stop the service
./service.sh stop

# Restart the service
./service.sh restart

# Check status
./service.sh status

# View logs
./service.sh logs
```

## Project Structure

```
sharevia_snapshot_service/
├── main.py                  # Entry point
├── snapshot_service.py      # Core service logic
├── brightdata_client.py     # Brightdata API client
├── supabase_client.py       # Supabase API client
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
├── README.md               # This file
├── service.sh              # Service management script
├── com.sharevia.snapshot.plist  # macOS launchd config
└── logs/                   # Log files directory
```

## Development

### Running Tests

```bash
# Integration tests (mocked APIs - fast)
./run_tests.sh integration

# End-to-end tests (requires backend running)
./run_tests.sh e2e
```

See [TESTING.md](TESTING.md) for detailed testing documentation.

### Test Types

1. **Integration Tests** - Test service logic with mocked APIs
   - Fast, no external dependencies
   - Tests all core functionality
   - Run: `./run_tests.sh integration`

2. **End-to-End Tests** - Test against real backend server
   - Tests complete flow from bookmark creation to snapshot processing
   - Requires backend running at http://localhost:8080
   - Run: `./run_tests.sh e2e`

## Environment Variables

- `BRIGHTDATA_TOKEN` - Brightdata API token (required)
- `SUPABASE_PROJECT_REF` - Supabase project reference ID (required)
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key (required)
- `SNAPSHOT_POLL_INTERVAL` - Seconds between polls (default: 60)

## Logging

Logs are written to:
- `logs/snapshot-service.out.log` - Standard output
- `logs/snapshot-service.err.log` - Error output

When running directly, logs are also printed to the console.

## How It Works

1. **Polling**: Service continuously polls Brightdata's snapshots API
2. **Status Check**: Checks each snapshot's status
3. **Download**: When a snapshot is ready, downloads the results
4. **Extract**: Processes results using service-specific extractors (X/Twitter, LinkedIn)
5. **Lookup**: Finds the corresponding bookmark in Supabase by URL
6. **Update**: Updates the bookmark with the scraped content and media

## License

MIT
