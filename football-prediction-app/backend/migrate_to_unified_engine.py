#!/usr/bin/env python3
"""
Migration script to update all files to use the unified prediction engine
"""

import os
import re
import shutil
from datetime import datetime

# Files to update
FILES_TO_UPDATE = [
    'test_simple_api.py',
    'main_page_predictions_routes.py',
    'routes/predictions_advanced.py',
    'simple_routes.py',
    'enhanced_predictions_route.py',
    'enhanced_predictions_routes.py'
]

# Backup directory
BACKUP_DIR = f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'

def create_backup():
    """Create backup of files before modification"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    for file in FILES_TO_UPDATE:
        if os.path.exists(file):
            backup_path = os.path.join(BACKUP_DIR, file)
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            shutil.copy2(file, backup_path)
            print(f"Backed up {file} to {backup_path}")

def update_imports(content):
    """Update import statements to use unified engine"""
    # Replace various prediction engine imports
    replacements = [
        (r'from simple_prediction_engine import SimplePredictionEngine',
         'from unified_prediction_engine import UnifiedPredictionEngine'),
        (r'from main_page_prediction_engine import MainPagePredictionEngine',
         'from unified_prediction_engine import UnifiedPredictionEngine'),
        (r'from enhanced_prediction_engine import EnhancedPredictionEngine',
         'from unified_prediction_engine import UnifiedPredictionEngine'),
        (r'from prediction_engine import AdvancedPredictionEngine',
         'from unified_prediction_engine import UnifiedPredictionEngine'),
    ]
    
    for old, new in replacements:
        content = re.sub(old, new, content)
    
    return content

def update_class_instantiation(content):
    """Update class instantiation to use unified engine"""
    # Replace various engine instantiations
    replacements = [
        (r'SimplePredictionEngine\((.*?)\)', r'UnifiedPredictionEngine(\1)'),
        (r'MainPagePredictionEngine\((.*?)\)', r'UnifiedPredictionEngine(\1)'),
        (r'EnhancedPredictionEngine\((.*?)\)', r'UnifiedPredictionEngine(\1)'),
        (r'AdvancedPredictionEngine\((.*?)\)', r'UnifiedPredictionEngine(\1)'),
    ]
    
    for old, new in replacements:
        content = re.sub(old, new, content)
    
    return content

def update_method_calls(content):
    """Update method calls to match unified engine API"""
    # The unified engine uses predict_match instead of various method names
    replacements = [
        (r'\.generate_prediction\(', r'.predict_match('),
        (r'\.get_prediction\(', r'.predict_match('),
        (r'\.predict\(', r'.predict_match('),
    ]
    
    for old, new in replacements:
        content = re.sub(old, new, content)
    
    return content

def migrate_file(filepath):
    """Migrate a single file to use unified engine"""
    print(f"\nMigrating {filepath}...")
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Apply updates
        original_content = content
        content = update_imports(content)
        content = update_class_instantiation(content)
        content = update_method_calls(content)
        
        # Only write if changes were made
        if content != original_content:
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"✓ Updated {filepath}")
        else:
            print(f"- No changes needed for {filepath}")
            
    except Exception as e:
        print(f"✗ Error migrating {filepath}: {str(e)}")

def main():
    """Run the migration"""
    print("Starting migration to unified prediction engine...")
    
    # Create backup
    create_backup()
    
    # Migrate each file
    for file in FILES_TO_UPDATE:
        if os.path.exists(file):
            migrate_file(file)
        else:
            print(f"✗ File not found: {file}")
    
    print(f"\nMigration complete! Backup saved to {BACKUP_DIR}")
    print("\nNext steps:")
    print("1. Test the application to ensure everything works")
    print("2. Delete old prediction engine files if tests pass")
    print("3. Update any remaining references in the codebase")

if __name__ == "__main__":
    main()