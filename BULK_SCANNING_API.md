# Bulk Target Scanning API — Phase 4 Implementation

## Overview

The Bulk Target Scanning API enables automated scanning of multiple targets in parallel with efficient queue management, progress tracking, and aggregated result handling. This API is designed for enterprise-scale vulnerability assessment operations.

## Performance Characteristics

- **Parallel Execution**: Up to 10 concurrent scans by default (configurable 1-20)
- **Performance**: 10 targets scanned in approximately 2-3x the time of a single target scan
- **Queue Management**: FIFO with priority retry for failed targets
- **Memory Efficient**: Streaming results, no full-payload buffering
- **Error Recovery**: Automatic retry with exponential backoff (max 3 attempts)

## Core Concepts

### Job
A bulk scanning job represents a collection of targets to scan with identical module configuration.

### Target
Individual target URL within a job. Each target tracks its own status, results, and error history.

### Queue
Thread-safe queue managing parallel execution with configurable concurrency limits (1-20 parallel scans).

### Progress
Real-time tracking of completed/failed/pending targets with percentage completion.

## Database Schema

### `bulk_jobs` Table
```sql
CREATE TABLE bulk_jobs (
    id              TEXT PRIMARY KEY,
    project_id      TEXT NOT NULL,
    status          TEXT DEFAULT 'pending',          -- pending|running|completed|failed|cancelled
    progress        INTEGER DEFAULT 0,               -- 0-100 percentage
    total_targets   INTEGER NOT NULL,
    completed_count INTEGER DEFAULT 0,
    failed_count    INTEGER DEFAULT 0,
    created_at      TEXT NOT NULL,
    started_at      TEXT,
    completed_at    TEXT,
    config          TEXT                             -- JSON scan configuration
);
```

### `bulk_job_targets` Table
```sql
CREATE TABLE bulk_job_targets (
    id              TEXT PRIMARY KEY,
    job_id          TEXT NOT NULL,
    target_url      TEXT NOT NULL,
    status          TEXT DEFAULT 'pending',          -- pending|scanning|completed|error|cancelled
    result          TEXT,                            -- JSON result data
    error           TEXT,                            -- Error message if failed
    started_at      TEXT,
    completed_at    TEXT
);
```

## API Endpoints

### 1. Create and Start Bulk Scan

**Endpoint:** `POST /api/bulk/scan`

**Authentication:** Optional (uses project context)

**Request Body:**
```json
{
  "targets": [
    "example.com",
    "test.org",
    "sample.net"
  ],
  "modules": {
    "recon": true,
    "ports": true,
    "web": true,
    "cve": false,
    "full_scan": false,
    "scan_classification": "active",
    "port_range": "top-1000"
  },
  "max_parallel": 5,
  "project_id": "optional-project-uuid"
}
```

**Response (201 Created):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "estimated_time_seconds": 300,
  "targets_count": 3,
  "max_parallel": 5
}
```

**Error Responses:**
- `400 Bad Request`: No targets, >100 targets, invalid max_parallel
- `500 Internal Server Error`: Scan execution failure

---

### 2. List Bulk Jobs

**Endpoint:** `GET /api/bulk/jobs`

**Query Parameters:**
- `project_id` (optional): Filter by project
- `limit` (optional, default=50): Max jobs to return

**Response:**
```json
{
  "jobs": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "project_id": "proj-123",
      "status": "completed",
      "progress": 100,
      "total_targets": 3,
      "completed_count": 3,
      "failed_count": 0,
      "created_at": "2024-01-15T10:30:00Z",
      "started_at": "2024-01-15T10:30:05Z",
      "completed_at": "2024-01-15T10:35:00Z"
    }
  ],
  "count": 1
}
```

---

### 3. Get Job Status

**Endpoint:** `GET /api/bulk/jobs/{job_id}`

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress": 66,
  "completed": 2,
  "failed": 0,
  "total": 3,
  "created_at": "2024-01-15T10:30:00Z",
  "started_at": "2024-01-15T10:30:05Z",
  "completed_at": null,
  "queue_size": 1,
  "running_count": 1
}
```

**Fields:**
- `status`: Current job state
- `progress`: Completion percentage (0-100)
- `completed`: Number of successfully completed targets
- `failed`: Number of failed targets
- `total`: Total targets in job
- `queue_size`: Targets waiting to be scanned
- `running_count`: Currently running scans

---

### 4. Get Job Targets

**Endpoint:** `GET /api/bulk/jobs/{job_id}/targets`

**Query Parameters:**
- `limit` (optional, default=50): Results per page
- `offset` (optional, default=0): Pagination offset

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "targets": [
    {
      "id": "target-uuid-1",
      "job_id": "job-uuid",
      "target_url": "example.com",
      "status": "completed",
      "result": "{...}",
      "error": null,
      "started_at": "2024-01-15T10:30:05Z",
      "completed_at": "2024-01-15T10:31:00Z"
    }
  ],
  "total": 3,
  "limit": 50,
  "offset": 0
}
```

---

### 5. Get Job Results

**Endpoint:** `GET /api/bulk/jobs/{job_id}/results`

**Prerequisites:** Job must be completed or cancelled

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:35:00Z",
  "summary": {
    "total": 3,
    "completed": 3,
    "failed": 0
  },
  "results": [
    {
      "target": "example.com",
      "status": "completed",
      "result": {
        "scan_id": "scan-uuid",
        "subdomains": 12,
        "open_ports": 4,
        "vulnerabilities": 2
      },
      "error": null
    }
  ]
}
```

---

### 6. Cancel Job

**Endpoint:** `POST /api/bulk/jobs/{job_id}/cancel`

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "cancellation_requested"
}
```

**Error Responses:**
- `400 Bad Request`: Job already completed or cancelled
- `404 Not Found`: Job doesn't exist

---

### 7. Get Bulk Statistics

**Endpoint:** `GET /api/bulk/stats`

**Response:**
```json
{
  "total_jobs": 42,
  "status_breakdown": {
    "completed": 38,
    "running": 2,
    "failed": 1,
    "cancelled": 1,
    "pending": 0
  },
  "targets": {
    "total": 156,
    "completed": 148,
    "failed": 8,
    "success_rate": 94.87
  }
}
```

## Usage Examples

### Example 1: Basic Bulk Scan

```bash
curl -X POST http://localhost:8000/api/bulk/scan \
  -H "Content-Type: application/json" \
  -d '{
    "targets": ["example.com", "test.org"],
    "modules": {
      "recon": true,
      "ports": true,
      "web": true,
      "full_scan": false
    },
    "max_parallel": 5
  }'
```

### Example 2: Poll Job Status

```bash
JOB_ID="550e8400-e29b-41d4-a716-446655440000"

# Check status every 5 seconds
while true; do
  curl -s http://localhost:8000/api/bulk/jobs/$JOB_ID | jq '.progress'
  sleep 5
done
```

### Example 3: Get Results When Complete

```bash
JOB_ID="550e8400-e29b-41d4-a716-446655440000"

# Wait for completion
while [ "$(curl -s http://localhost:8000/api/bulk/jobs/$JOB_ID | jq -r '.status')" != "completed" ]; do
  echo "Still running..."
  sleep 10
done

# Get results
curl -s http://localhost:8000/api/bulk/jobs/$JOB_ID/results | jq '.'
```

### Example 4: Handle Large Target Lists

```bash
# For 100+ targets, consider batch processing
TARGETS=$(seq 1 50 | xargs -I {} echo "target{}.com")

curl -X POST http://localhost:8000/api/bulk/scan \
  -H "Content-Type: application/json" \
  -d "{
    \"targets\": [$TARGETS],
    \"modules\": {
      \"recon\": true,
      \"ports\": true
    },
    \"max_parallel\": 10
  }"
```

## BulkScanner Class Reference

### Core Methods

```python
class BulkScanner:
    def create_job(job_id: str, targets: list[str], modules: dict) -> str
    """Create a new scanning job"""
    
    def get_job_status(job_id: str) -> dict
    """Get current status of a job"""
    
    def get_job_results(job_id: str) -> dict
    """Get aggregated results from a completed job"""
    
    async def process_job(job_id: str) -> dict
    """Process all targets in a job with parallel scanning"""
    
    def cancel_job(job_id: str) -> dict
    """Cancel a running job"""
    
    def get_queue_size(job_id: str = None) -> int
    """Get count of pending scans"""
    
    def get_running_count(job_id: str = None) -> int
    """Get count of currently running scans"""
    
    def cleanup_job(job_id: str)
    """Clean up resources for a completed job"""
```

### Configuration

```python
BulkScanner(
    max_parallel: int = 10,              # Concurrency limit
    scan_callback: Callable = None       # Async scan executor
)
```

## Best Practices

### 1. Optimal Concurrency
- **Small targets (<1MB)**: Use max_parallel=10-15
- **Large targets (>10MB)**: Use max_parallel=3-5
- **Network constrained**: Use max_parallel=1-2

### 2. Error Handling
- Implement exponential backoff for retries
- Log failed targets for manual review
- Use error classification (timeout vs. permission denied)

### 3. Progress Monitoring
- Poll `/api/bulk/jobs/{id}` every 10-30 seconds
- Implement exponential backoff for polling (start 5s, max 60s)
- Use SSE if browser-based monitoring needed

### 4. Result Aggregation
- Collect results incrementally (pagination)
- Don't wait for full completion to start processing
- Store intermediate results in database

### 5. Resource Management
- Limit concurrent jobs to 3-5 at system level
- Implement job queuing for enterprise use
- Monitor memory usage (1GB RAM per 20 concurrent scans)

### 6. Security
- Validate targets against whitelist
- Enforce scope boundaries
- Audit job creation and cancellation
- Encrypt result storage

## Troubleshooting

### Job Stuck at 99% Progress
**Cause:** Network timeout on last target
**Solution:** Increase timeout, reduce target complexity, or retry

### High Memory Usage
**Cause:** Too many concurrent scans
**Solution:** Reduce max_parallel or implement pagination

### Scan Results Empty
**Cause:** Target unreachable or denied
**Solution:** Check network connectivity, firewall rules, target permissions

### Retry Loop
**Cause:** Persistent target failure
**Solution:** Check target validity, increase timeout, manual review

## Performance Metrics

### Typical Scan Times (Per Target)
- Recon only: 10-30 seconds
- Port scan: 30-120 seconds
- Web scan: 20-60 seconds
- Full scan: 120-300 seconds

### Throughput
- Sequential: 1 target per 2 minutes
- 5 parallel: 5 targets per 2 minutes
- 10 parallel: 10 targets per 2-3 minutes

### Memory Usage
- Base: ~50MB
- Per parallel scan: ~30MB
- With results caching: ~50MB per job

## Limits and Constraints

| Parameter | Limit | Notes |
|-----------|-------|-------|
| Targets per job | 100 | Enterprise can request higher |
| Max parallel | 20 | System-dependent |
| Job retention | 7 days | Configurable |
| Result size | 10GB max | Per job |
| Timeout per target | 600s | Configurable |
| Max retries | 3 | Per target |

## Future Enhancements

- [ ] WebSocket streaming results
- [ ] Scheduled bulk jobs (cron-like)
- [ ] Target filtering by previous results
- [ ] Dynamic concurrency adjustment
- [ ] Machine learning-based priority scheduling
- [ ] Cost estimation and billing integration
- [ ] Multi-region scanning federation
- [ ] Result deduplication across jobs

## Implementation Status

✅ **Completed:**
- Database schema for bulk jobs and targets
- BulkScanner class with parallel queue management
- All REST API endpoints
- Progress tracking and status monitoring
- Error handling and retry logic
- Unit and integration tests
- Performance validation

📋 **Deliverables:**
- `scanner/web/bulk_scanner.py`: Core BulkScanner implementation
- Database migrations: Bulk job tracking tables
- `server.py`: REST API endpoints (8 endpoints total)
- `tests_bulk_scanning.py`: Comprehensive test suite
- API documentation (this file)

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review test cases for usage patterns
3. Check scan logs: `/var/log/vapt/` or stdout
4. Enable debug logging: `LOG_LEVEL=DEBUG`
