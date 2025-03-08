#!/usr/bin/env python
"""
Test Runner for WhatsApp Chat Bot

This script runs all tests for the WhatsApp Chat Bot application.
It provides options to run specific test types or all tests.
"""
import os
import sys
import argparse
import pytest

def run_unit_tests():
    """Run unit tests"""
    print("\n=== Running Unit Tests ===\n")
    return pytest.main(["-v", "tests/unit/"])

def run_integration_tests():
    """Run integration tests"""
    print("\n=== Running Integration Tests ===\n")
    return pytest.main(["-v", "tests/integration/"])

def run_api_tests():
    """Run API tests"""
    print("\n=== Running API Tests ===\n")
    return pytest.main(["-v", "tests/test_flask_app.py"])

def run_all_tests():
    """Run all tests"""
    print("\n=== Running All Tests ===\n")
    return pytest.main(["-v", "tests/"])

def run_coverage():
    """Run tests with coverage"""
    print("\n=== Running Tests with Coverage ===\n")
    return pytest.main(["--cov=.", "--cov-report=term", "--cov-report=html", "tests/"])

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run tests for WhatsApp Chat Bot")
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--api", action="store_true", help="Run API tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--coverage", action="store_true", help="Run tests with coverage")
    
    args = parser.parse_args()
    
    # Set environment variables for testing
    os.environ["ENV"] = "test"
    os.environ["GROQ_API_KEY"] = "test-key"
    os.environ["GROQ_MODEL"] = "test-model"
    
    # Determine which tests to run
    if args.unit:
        return run_unit_tests()
    elif args.integration:
        return run_integration_tests()
    elif args.api:
        return run_api_tests()
    elif args.coverage:
        return run_coverage()
    elif args.all or not any([args.unit, args.integration, args.api, args.coverage]):
        # Default to all tests if no specific option is provided
        return run_all_tests()

if __name__ == "__main__":
    sys.exit(main())
