# Scheduler Deployment Guide for Render

## Problem
When deploying a Flask app with APScheduler on Render using Gunicorn with multiple workers, you may encounter the error:
```
apscheduler.jobstores.base.ConflictingIdError: 'Job identifier (initial_fetch) conflicts with an existing job'
```

This happens because each Gunicorn worker process creates its own instance of the Flask app and scheduler, leading to conflicts.

## Solution

### Option 1: Use Environment Variables (Recommended)

1. **Set up environment variables on Render:**
   - `ENABLE_SCHEDULER=true` - Enable the scheduler functionality
   - `IS_SCHEDULER_INSTANCE=true` - Set this ONLY on one service instance

2. **For a single web service:**
   - Set both environment variables to `true`
   - The scheduler will run in the same process as your web server

3. **For multiple services or scaling:**
   - Create a separate "Background Worker" service on Render
   - Set `ENABLE_SCHEDULER=true` and `IS_SCHEDULER_INSTANCE=true` only on the worker
   - Set `ENABLE_SCHEDULER=false` on all web service instances

### Option 2: Use Gunicorn Preload (Alternative)

1. **Update your Gunicorn command:**
   ```bash
   gunicorn --preload -w 4 wsgi:app
   ```

2. **Modify scheduler.py to use file-based locking:**
   ```python
   import fcntl
   
   # In the start() method
   lock_file = '/tmp/scheduler.lock'
   with open(lock_file, 'w') as f:
       try:
           fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
           # Start scheduler here
       except IOError:
           logger.info("Scheduler already running in another process")
   ```

### Option 3: Separate Scheduler Service (Best for Production)

1. **Create a separate scheduler script (`run_scheduler.py`):**
   ```python
   from app import create_app
   from scheduler import data_scheduler
   
   app = create_app()
   data_scheduler.init_app(app)
   data_scheduler.start()
   
   # Keep the script running
   import time
   while True:
       time.sleep(60)
   ```

2. **Deploy as a Background Worker on Render:**
   - Create a new "Background Worker" service
   - Set the start command to: `python run_scheduler.py`
   - Disable scheduler on web services: `ENABLE_SCHEDULER=false`

## Current Implementation

The current implementation uses Option 1 with environment variables:

- The scheduler checks for `IS_SCHEDULER_INSTANCE=true` before starting
- Jobs are added with `replace_existing=True` to handle restarts gracefully
- Individual job additions are wrapped in try/except to handle conflicts
- The scheduler includes proper cleanup on shutdown

## Deployment Steps on Render

1. **In your Render dashboard:**
   - Go to your web service settings
   - Add environment variables:
     - `ENABLE_SCHEDULER=true`
     - `IS_SCHEDULER_INSTANCE=true`
   
2. **If you have multiple instances or auto-scaling:**
   - Create a new Background Worker service
   - Use the same repo and branch
   - Set start command: `python run_scheduler.py` (if using Option 3)
   - Add environment variables to the worker service only

3. **Monitor logs** to ensure scheduler starts correctly:
   ```
   INFO:scheduler:Scheduler started with all jobs configured
   ```

## Troubleshooting

1. **ConflictingIdError persists:**
   - Ensure only one instance has `IS_SCHEDULER_INSTANCE=true`
   - Check that jobs use `replace_existing=True`
   - Verify no duplicate scheduler initialization

2. **Scheduler not running:**
   - Check environment variables are set correctly
   - Verify logs show scheduler initialization
   - Ensure database connection is available

3. **Jobs not executing:**
   - Check timezone settings
   - Verify API keys are configured
   - Monitor scheduler logs for errors