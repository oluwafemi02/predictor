#!/usr/bin/env python
"""
Monitor automatic data synchronization
Checks if schedulers are running and data is being updated
"""

import os
import requests
import time
from datetime import datetime, timedelta
import sys

# Configuration
BASE_URL = os.environ.get('API_URL', 'http://localhost:5000')
CHECK_INTERVAL = int(os.environ.get('CHECK_INTERVAL', '300'))  # 5 minutes default

def check_sync_status():
    """Check current sync status"""
    try:
        response = requests.get(f"{BASE_URL}/api/sync/status", timeout=10)
        if response.status_code == 200:
            return response.json().get('stats', {})
        else:
            print(f"❌ Failed to get sync status: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error checking sync status: {str(e)}")
        return None

def check_scheduler_health():
    """Check if scheduler is healthy via health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/health/detailed", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('checks', {})
        else:
            return None
    except:
        return None

def monitor_data_growth(previous_stats, current_stats):
    """Compare data counts to see if they're growing"""
    if not previous_stats or not current_stats:
        return None
    
    db_prev = previous_stats.get('database', {})
    db_curr = current_stats.get('database', {})
    
    changes = {}
    for key in ['teams', 'matches', 'sportmonks_fixtures', 'sportmonks_predictions']:
        prev_count = db_prev.get(key, 0)
        curr_count = db_curr.get(key, 0)
        changes[key] = curr_count - prev_count
    
    return changes

def check_recent_updates():
    """Check for recent data updates"""
    try:
        # Check recent matches
        response = requests.get(f"{BASE_URL}/api/v1/matches?limit=10&sort=updated_desc")
        if response.status_code == 200:
            matches = response.json().get('matches', [])
            if matches:
                # Check if any match was updated in the last hour
                for match in matches[:5]:
                    # This would need timestamp parsing logic
                    pass
        
        return True
    except:
        return False

def main():
    """Main monitoring loop"""
    print("=" * 60)
    print("Football Prediction App - Automatic Sync Monitor")
    print(f"API URL: {BASE_URL}")
    print(f"Check Interval: {CHECK_INTERVAL} seconds")
    print("=" * 60)
    
    previous_stats = None
    check_count = 0
    
    while True:
        check_count += 1
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n[{timestamp}] Check #{check_count}")
        print("-" * 40)
        
        # Get current sync status
        current_stats = check_sync_status()
        
        if current_stats:
            db_stats = current_stats.get('database', {})
            print("📊 Current Database Stats:")
            print(f"   Teams: {db_stats.get('teams', 0)}")
            print(f"   Matches: {db_stats.get('matches', 0)}")
            print(f"   SportMonks Fixtures: {db_stats.get('sportmonks_fixtures', 0)}")
            print(f"   SportMonks Predictions: {db_stats.get('sportmonks_predictions', 0)}")
            
            # Check for data growth
            if previous_stats:
                changes = monitor_data_growth(previous_stats, current_stats)
                if changes:
                    print("\n📈 Data Changes Since Last Check:")
                    any_change = False
                    for key, change in changes.items():
                        if change != 0:
                            any_change = True
                            symbol = "+" if change > 0 else ""
                            print(f"   {key.replace('_', ' ').title()}: {symbol}{change}")
                    
                    if not any_change:
                        print("   No changes detected")
            
            # Check scheduler health
            health = check_scheduler_health()
            if health:
                print("\n🏥 Scheduler Health:")
                redis_check = health.get('redis', {})
                if redis_check.get('status') == 'healthy':
                    print("   ✅ Redis connection healthy")
                else:
                    print("   ❌ Redis connection issues")
            
            previous_stats = current_stats
        else:
            print("❌ Unable to retrieve sync status")
        
        # Summary
        if check_count > 1 and previous_stats:
            db_stats = current_stats.get('database', {}) if current_stats else {}
            total_records = sum(db_stats.get(k, 0) for k in ['teams', 'matches', 'sportmonks_fixtures'])
            
            if total_records > 0:
                print(f"\n✅ Automatic sync appears to be working ({total_records} total records)")
            else:
                print("\n⚠️  No data found - check scheduler logs")
        
        # Wait for next check
        if CHECK_INTERVAL > 0:
            print(f"\nNext check in {CHECK_INTERVAL} seconds... (Press Ctrl+C to stop)")
            try:
                time.sleep(CHECK_INTERVAL)
            except KeyboardInterrupt:
                print("\n\nMonitoring stopped by user")
                sys.exit(0)
        else:
            # Single check mode
            break

if __name__ == '__main__':
    # Command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--once':
            CHECK_INTERVAL = 0
    
    main()