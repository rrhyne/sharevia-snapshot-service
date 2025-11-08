# Testing Guide

This document describes how to test the Sharevia Snapshot Service.

## Test Types

### 1. Integration Tests (Mocked APIs)

These tests use mocked Brightdata and Supabase APIs to test the service logic without making real API calls.

**Run:**
```bash
./run_tests.sh integration
```

**What it tests:**
- Brightdata API client functions
- Supabase API client functions
- Content extraction (X/Twitter, LinkedIn)
- Snapshot result processing
- Full polling cycle logic

**Pros:**
- Fast (no network calls)
- No external dependencies
- Can run anywhere

**Cons:**
- Doesn't test against real APIs
- May miss integration issues

### 2. End-to-End Tests (Real Server)

These tests run against the actual Sharevia backend server and test the complete flow from bookmark creation to snapshot processing.

**Prerequisites:**
1. Backend server must be running at `http://localhost:8080`
2. Valid `.env` file with credentials:
   - `BRIGHTDATA_TOKEN`
   - `SUPABASE_PROJECT_REF`
   - `SUPABASE_SERVICE_ROLE_KEY`
3. Network access to Brightdata and Supabase

**Run:**
```bash
# Make sure backend is running first
cd ../backend
python3 app.py

# In another terminal
cd ../sharevia_snapshot_service
./run_tests.sh e2e
```

**What it tests:**
- Creating a bookmark via backend API
- Backend triggering Brightdata scrape
- Handling async scrapes (202 responses)
- Snapshot service polling and processing
- Bookmark updates with scraped content

**Pros:**
- Tests real integration
- Tests actual API behavior
- Catches real-world issues

**Cons:**
- Slower (real API calls)
- Requires backend running
- Requires valid credentials
- May incur API costs

## Running Tests

### All Integration Tests

```bash
./run_tests.sh integration
```

### End-to-End Tests

```bash
# Terminal 1: Start backend
cd ../backend
python3 app.py

# Terminal 2: Run E2E tests
cd ../sharevia_snapshot_service
./run_tests.sh e2e
```

### Individual Test Files

```bash
# Integration tests
python3 tests/test_integration.py -v

# E2E tests
python3 tests/test_e2e.py -v

# Specific test
python3 tests/test_integration.py TestSnapshotServiceIntegration.test_extract_x_content -v
```

## Test Scenarios

### Integration Test Scenarios

1. **test_get_snapshots**: Verify snapshot listing from Brightdata
2. **test_download_snapshot_results**: Verify downloading results
3. **test_extract_x_content**: X/Twitter content extraction
4. **test_extract_x_content_with_video**: X/Twitter with video
5. **test_extract_linkedin_content**: LinkedIn content extraction
6. **test_get_bookmark_by_url**: Bookmark lookup in Supabase
7. **test_update_bookmark**: Bookmark updates in Supabase
8. **test_process_result_x**: Processing X/Twitter results
9. **test_process_result_linkedin**: Processing LinkedIn results
10. **test_process_snapshot_results**: End-to-end result processing
11. **test_process_snapshot_no_bookmark_found**: Handling missing bookmarks
12. **test_full_poll_cycle**: Complete polling iteration

### E2E Test Scenarios

1. **test_backend_healthcheck**: Verify backend is accessible
2. **test_e2e_bookmark_creation_and_snapshot_processing**: Full flow test
   - Creates bookmark via backend
   - Handles sync (200) or async (202) response
   - Runs snapshot service to process async results
   - Verifies bookmark was updated

## Expected Outcomes

### Integration Tests
All 12 tests should pass:
```
----------------------------------------------------------------------
Ran 12 tests in 0.109s

OK
```

### E2E Tests
The test will either:

**Scenario 1: Sync Success (200)**
```
✅ Sync scrape succeeded - got immediate results
✅ E2E test PASSED - bookmark has sync content!
```

**Scenario 2: Async Success (202)**
```
✅ Async scrape initiated - snapshot_id: sd_xxx
Polling for snapshot results (max 5 minutes)...
✅ E2E test PASSED - bookmark was updated from snapshot!
```

## Troubleshooting

### Integration Tests Fail

**Import errors:**
```bash
pip3 install -r requirements.txt
```

**Module not found:**
```bash
# Make sure you're in the correct directory
cd /path/to/sharevia_snapshot_service
```

### E2E Tests Fail

**"Backend server is not running"**
```bash
# Start the backend in another terminal
cd ../backend
python3 app.py
```

**"Missing required environment variables"**
```bash
# Copy .env from backend or create new
cp ../backend/.env .env
# Edit with your credentials
nano .env
```

**"Request timed out"**
- Check network connection
- Verify Brightdata API is accessible
- Check backend logs for errors

**"No bookmark found for URL"**
- Check Supabase credentials are correct
- Verify database has bookmarks table
- Check backend is creating bookmarks correctly

### Common Issues

**Test hangs during E2E**
- Snapshot might be taking longer than expected
- Check Brightdata dashboard for snapshot status
- Press Ctrl+C to cancel

**Bookmark not updated after snapshot**
- Check snapshot service logs
- Verify snapshot was marked as "ready"
- Check Supabase for bookmark updates

## Debugging

### Enable Debug Logging

```python
# In test file, change logging level
logging.basicConfig(level=logging.DEBUG)
```

### Check Snapshot Status

```bash
# View Brightdata snapshots
curl -H "Authorization: Bearer $BRIGHTDATA_TOKEN" \
  https://api.brightdata.com/datasets/snapshots
```

### Check Bookmark in Database

```bash
# Use Supabase dashboard or SQL
# Navigate to: https://supabase.com/dashboard
# Go to Table Editor > bookmarks
```

### Monitor Service Logs

```bash
# If running snapshot service
./service.sh logs
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test Snapshot Service

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          cd sharevia_snapshot_service
          pip install -r requirements.txt

      - name: Run integration tests
        run: |
          cd sharevia_snapshot_service
          ./run_tests.sh integration
```

## Performance Benchmarks

### Integration Tests
- Expected time: < 1 second
- All tests should complete in under 5 seconds

### E2E Tests
- Sync scrape: 1-70 seconds
- Async scrape: 1-5 minutes (depends on Brightdata processing time)
- Timeout: 5 minutes max

## Test Coverage

Current coverage focuses on:
- ✅ API client functions
- ✅ Content extraction
- ✅ Result processing
- ✅ Polling logic
- ✅ Error handling
- ✅ End-to-end flow

Future test additions:
- [ ] Concurrent snapshot processing
- [ ] Rate limiting behavior
- [ ] Failed snapshot handling
- [ ] Retry logic
- [ ] Multiple bookmark updates
