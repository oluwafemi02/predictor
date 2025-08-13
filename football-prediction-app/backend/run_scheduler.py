#!/usr/bin/env python
"""
Standalone scheduler runner for deployment as a separate service
"""
import os
import sys
import time
import logging
from app import create_app
from scheduler import data_scheduler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run the scheduler as a standalone process"""
    logger.info("Starting standalone scheduler process...")
    
    # Force scheduler instance flag
    os.environ['IS_SCHEDULER_INSTANCE'] = 'true'
    os.environ['ENABLE_SCHEDULER'] = 'true'
    
    # Create Flask app with production config
    app = create_app('production')
    
    # Initialize and start scheduler
    with app.app_context():
        data_scheduler.init_app(app)
        data_scheduler.start()
        
        logger.info("Scheduler started successfully. Running indefinitely...")
        
        # Keep the process running
        try:
            while True:
                time.sleep(60)  # Sleep for 1 minute
                # You could add health checks or status logging here
                if not data_scheduler.scheduler.running:
                    logger.error("Scheduler stopped unexpectedly! Attempting restart...")
                    data_scheduler.start()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
            data_scheduler.shutdown()
            sys.exit(0)
        except Exception as e:
            logger.error(f"Scheduler process error: {e}")
            data_scheduler.shutdown()
            sys.exit(1)

if __name__ == "__main__":
    main()