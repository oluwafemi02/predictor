#!/usr/bin/env python3
"""
Test runner script for the Football Prediction App
"""

import sys
import os
import pytest
import coverage

def run_tests():
    """Run all tests with coverage report"""
    
    # Initialize coverage
    cov = coverage.Coverage()
    cov.start()
    
    # Add current directory to Python path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Run pytest
    exit_code = pytest.main([
        'tests/',
        '-v',  # Verbose output
        '--tb=short',  # Short traceback format
        '--color=yes',  # Colored output
        '-x',  # Stop on first failure
        '--maxfail=5',  # Stop after 5 failures
    ])
    
    # Stop coverage and generate report
    cov.stop()
    cov.save()
    
    print("\n" + "="*70)
    print("Coverage Report:")
    print("="*70)
    
    # Generate coverage report
    cov.report(omit=[
        '*/tests/*',
        '*/venv/*',
        '*/migrations/*',
        '*/__pycache__/*',
        '*/site-packages/*'
    ])
    
    # Generate HTML coverage report
    cov.html_report(directory='htmlcov', omit=[
        '*/tests/*',
        '*/venv/*',
        '*/migrations/*',
        '*/__pycache__/*',
        '*/site-packages/*'
    ])
    
    print(f"\nHTML coverage report generated in: htmlcov/index.html")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(run_tests())