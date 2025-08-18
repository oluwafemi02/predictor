#!/usr/bin/env python3
"""
Manual SportMonks sync runner
"""
import os
import sys
from app import create_app
from improved_sportmonks_sync import improved_sync

def main():
    # Set environment if not set
    if not os.environ.get('FLASK_ENV'):
        os.environ['FLASK_ENV'] = 'development'
    
    # Create app
    app = create_app()
    
    print("🚀 Starting SportMonks sync...")
    print("=" * 50)
    
    # Run sync
    success, message = improved_sync(app)
    
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ Sync failed: {message}")
        sys.exit(1)

if __name__ == "__main__":
    main()